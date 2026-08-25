"""
FutureMind Iran Teacher AI V1
ZarinPal Gateway Adapter

SECURITY CONTRACT:
- Fail closed.
- Callback is never payment proof.
- Server-side verification is mandatory.
- Product/order/amount/currency binding is mandatory.
- No download token creation.
"""

import os
import json
import urllib.request
import urllib.error


PRODUCT_ID = "iran-teacher-ai-v1"
AMOUNT = 790000
CURRENCY = "IRR"


class ZarinPalGatewayError(Exception):
    pass


def _config():
    base = os.path.dirname(os.path.dirname(__file__))
    path = os.path.join(base, "payment", "gateway_config.json")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _credentials():
    cfg = _config()["gateways"]["zarinpal"]

    merchant_id = (
        os.getenv("ZARINPAL_MERCHANT_ID")
        or cfg.get("merchant_id", "")
    )

    callback_url = (
        os.getenv("ZARINPAL_CALLBACK_URL")
        or cfg.get("callback_url", "")
    )

    return merchant_id, callback_url


def gateway_status():
    cfg = _config()
    gateway = cfg["gateways"]["zarinpal"]

    merchant_id, callback_url = _credentials()

    return {
        "gateway": "zarinpal",
        "enabled": gateway.get("enabled", False),
        "sandbox": gateway.get("sandbox", True),
        "credentials_present": bool(merchant_id),
        "callback_configured": bool(callback_url),
        "real_gateway_enabled": cfg.get(
            "real_gateway_enabled", False
        ),
        "server_verify_required": True,
        "token_creation": False,
    }


def _require_order_contract(order):
    if not isinstance(order, dict):
        raise ZarinPalGatewayError("INVALID_ORDER")

    order_id = order.get("order_id")
    product_id = order.get("product_id")
    amount = order.get("amount")
    currency = order.get("currency")

    if not order_id:
        raise ZarinPalGatewayError("MISSING_ORDER_ID")

    if product_id != PRODUCT_ID:
        raise ZarinPalGatewayError(
            "PRODUCT_ID_MISMATCH"
        )

    if amount != AMOUNT:
        raise ZarinPalGatewayError(
            "AMOUNT_MISMATCH"
        )

    if currency != CURRENCY:
        raise ZarinPalGatewayError(
            "CURRENCY_MISMATCH"
        )

    return order_id


def _request_json(url, payload, headers=None):
    body = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            **(headers or {}),
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            raw = response.read().decode(
                "utf-8",
                errors="replace"
            )

            return json.loads(raw)

    except urllib.error.HTTPError as e:
        raise ZarinPalGatewayError(
            f"ZARINPAL_HTTP_ERROR:{e.code}"
        )

    except urllib.error.URLError as e:
        raise ZarinPalGatewayError(
            f"ZARINPAL_NETWORK_ERROR:{e.reason}"
        )

    except json.JSONDecodeError:
        raise ZarinPalGatewayError(
            "ZARINPAL_INVALID_JSON"
        )


def create_payment(order):
    """
    ZarinPal REST API V4 payment request.

    SECURITY:
    - Fail closed.
    - Product/order/amount/currency binding.
    - Explicit gateway enable required.
    - HTTPS callback required.
    - No download token creation.
    """

    order_id = _require_order_contract(order)

    cfg = _config()
    gateway = cfg["gateways"]["zarinpal"]

    if not cfg.get("real_gateway_enabled", False):
        return {
            "ok": False,
            "real_transaction": False,
            "reason": "REAL_GATEWAY_DISABLED",
            "order_id": order_id,
        }

    if not gateway.get("enabled", False):
        return {
            "ok": False,
            "real_transaction": False,
            "reason": "GATEWAY_DISABLED",
            "order_id": order_id,
        }

    merchant_id, callback_url = _credentials()

    if not merchant_id:
        return {
            "ok": False,
            "real_transaction": False,
            "reason": "MISSING_MERCHANT_ID",
            "order_id": order_id,
        }

    if not callback_url:
        return {
            "ok": False,
            "real_transaction": False,
            "reason": "MISSING_CALLBACK_URL",
            "order_id": order_id,
        }

    if not callback_url.startswith("https://"):
        return {
            "ok": False,
            "real_transaction": False,
            "reason": "HTTPS_CALLBACK_REQUIRED",
            "order_id": order_id,
        }

    # --------------------------------------------------------
    # ZarinPal REST API V4
    # --------------------------------------------------------

    endpoint = (
        "https://api.zarinpal.com"
        "/pg/v4/payment/request.json"
    )

    payload = {
        "merchant_id": merchant_id,
        "amount": int(AMOUNT),
        "callback_url": callback_url,
        "description": (
            f"iran-teacher-ai-v1 order {order_id}"
        ),
    }

    response = _request_json(
        endpoint,
        payload,
        headers={
            "User-Agent": "FutureMind-IranTeacherAI/1.0",
        },
    )

    if not isinstance(response, dict):
        raise ZarinPalGatewayError(
            "ZARINPAL_INVALID_RESPONSE"
        )

    errors = response.get("errors")

    if errors:
        return {
            "ok": False,
            "real_transaction": False,
            "reason": "ZARINPAL_REQUEST_REJECTED",
            "order_id": order_id,
            "gateway_error": errors,
        }

    data = response.get("data")

    if not isinstance(data, dict):
        raise ZarinPalGatewayError(
            "ZARINPAL_INVALID_RESPONSE_DATA"
        )

    code = data.get("code")
    authority = data.get("authority")

    if code != 100:
        return {
            "ok": False,
            "real_transaction": False,
            "reason": "ZARINPAL_REQUEST_FAILED",
            "order_id": order_id,
            "gateway_code": code,
            "gateway_message": data.get("message"),
        }

    if not authority:
        raise ZarinPalGatewayError(
            "ZARINPAL_MISSING_AUTHORITY"
        )

    return {
        "ok": True,
        "real_transaction": True,
        "order_id": order_id,
        "gateway": "zarinpal",
        "authority": authority,
        "gateway_code": code,
        "payment_url": (
            "https://www.zarinpal.com/pg/StartPay/"
            + str(authority)
        ),
        "token_created": False,
        "server_verify_required": True,
    }

def verify_payment(order, authority):
    """
    Server-side ZarinPal REST API V4 verification.

    Callback is NOT payment proof.

    Verification is bound to:
    - product
    - order
    - amount
    - currency

    No download token creation.
    """

    order_id = _require_order_contract(order)

    if not authority:
        return {
            "ok": False,
            "verified": False,
            "reason": "MISSING_AUTHORITY",
            "order_id": order_id,
        }

    cfg = _config()

    if not cfg.get("real_gateway_enabled", False):
        return {
            "ok": False,
            "verified": False,
            "reason": "REAL_GATEWAY_DISABLED",
            "order_id": order_id,
        }

    gateway = cfg["gateways"]["zarinpal"]

    if not gateway.get("enabled", False):
        return {
            "ok": False,
            "verified": False,
            "reason": "GATEWAY_DISABLED",
            "order_id": order_id,
        }

    merchant_id, callback_url = _credentials()

    if not merchant_id:
        return {
            "ok": False,
            "verified": False,
            "reason": "MISSING_MERCHANT_ID",
            "order_id": order_id,
        }

    # --------------------------------------------------------
    # ZarinPal REST API V4
    # --------------------------------------------------------

    endpoint = (
        "https://api.zarinpal.com"
        "/pg/v4/payment/verify.json"
    )

    payload = {
        "merchant_id": merchant_id,
        "amount": int(AMOUNT),
        "authority": str(authority),
    }

    response = _request_json(
        endpoint,
        payload,
        headers={
            "User-Agent": "FutureMind-IranTeacherAI/1.0",
        },
    )

    if not isinstance(response, dict):
        raise ZarinPalGatewayError(
            "ZARINPAL_INVALID_RESPONSE"
        )

    data = response.get("data")

    if not isinstance(data, dict):
        raise ZarinPalGatewayError(
            "ZARINPAL_INVALID_RESPONSE_DATA"
        )

    code = data.get("code")
    ref_id = data.get("ref_id")

    if code not in (100, 101):
        return {
            "ok": False,
            "verified": False,
            "reason": "ZARINPAL_VERIFY_FAILED",
            "order_id": order_id,
            "authority": authority,
            "gateway_code": code,
            "gateway_message": data.get("message"),
            "ref_id": ref_id,
        }

    if not ref_id:
        raise ZarinPalGatewayError(
            "ZARINPAL_MISSING_REF_ID"
        )

    return {
        "ok": True,
        "verified": True,
        "verification_code": code,
        "already_verified": code == 101,
        "order_id": order_id,
        "authority": authority,
        "ref_id": ref_id,
        "gateway": "zarinpal",
        "token_created": False,
        "server_verified": True,
    }

def handle_callback(payload):
    """
    Callback parser only.

    NEVER converts callback directly into PAID.
    """

    if not isinstance(payload, dict):
        raise ZarinPalGatewayError(
            "INVALID_CALLBACK"
        )

    return {
        "ok": True,
        "callback_received": True,
        "gateway": "zarinpal",
        "order_id": payload.get("order_id"),
        "gateway_reference": (
            payload.get("gateway_reference")
            or payload.get("Authority")
        ),
        "token_created": False,
        "paid": False,
    }
