# ================================================================
# R-GATEWAY-17 — PAYMENT CONFIRM INTEGRATION
# ================================================================
#
# SECURITY CONTRACT:
#
# 1. Client tx_hash is NOT payment proof.
# 2. Client Status is NOT payment proof.
# 3. Callback is NOT payment proof.
# 4. Authority is only an input to server-side verification.
# 5. verify_payment() MUST succeed before PAID.
# 6. download token MUST be created only after verification.
# 7. Product/order/amount/currency binding is performed by gateway.
# 8. Gateway configuration remains fail-closed.
#
# ================================================================

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path

BASE = Path(
    "/content/drive/MyDrive/"
    "FutureMind_Lab_V7_RC2_IRAN_GATEWAY_WORKING_20260822_183110"
)

ORDERS = BASE / "orders" / "orders.json"


def _load_orders():
    if not ORDERS.exists():
        raise RuntimeError("ORDERS_FILE_MISSING")

    data = json.loads(
        ORDERS.read_text(encoding="utf-8")
    )

    if not isinstance(data, list):
        raise RuntimeError("INVALID_ORDERS_CONTRACT")

    return data


def _save_orders(orders):
    if not isinstance(orders, list):
        raise RuntimeError("INVALID_ORDERS_WRITE")

    ORDERS.write_text(
        json.dumps(
            orders,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )


def _find_order(order_id):
    orders = _load_orders()

    for order in orders:
        if (
            isinstance(order, dict)
            and order.get("order_id") == order_id
        ):
            return orders, order

    return orders, None


def _safe_product_contract(order):
    if not isinstance(order, dict):
        raise RuntimeError("INVALID_ORDER")

    product_id = order.get("product_id")
    amount = order.get("amount")

    if amount is None:
        amount = order.get("price")

    currency = order.get("currency")

    if not product_id:
        raise RuntimeError("MISSING_PRODUCT_ID")

    if amount is None:
        raise RuntimeError("MISSING_AMOUNT")

    if not currency:
        raise RuntimeError("MISSING_CURRENCY")

    return product_id, int(amount), currency


def _create_download_token(order_id, product_id):
    """
    Token creation boundary.

    This function is imported only after successful
    server-side gateway verification.
    """

    from payment.token_engine import (
        create_download_token
    )

    return create_download_token(
        order_id,
        product_id
    )


class PaymentConfirmHandler(BaseHTTPRequestHandler):

    def _json_response(self, status_code, payload):

        self.send_response(status_code)

        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8"
        )

        self.end_headers()

        self.wfile.write(
            json.dumps(
                payload,
                ensure_ascii=False
            ).encode("utf-8")
        )

    def do_POST(self):

        try:

            length = int(
                self.headers.get(
                    "Content-Length",
                    "0"
                )
            )

            if length <= 0:
                self._json_response(
                    400,
                    {
                        "status": "error",
                        "message": "Missing request body"
                    }
                )
                return

            data = self.rfile.read(length)

            request = json.loads(
                data.decode("utf-8")
            )

            if not isinstance(request, dict):
                self._json_response(
                    400,
                    {
                        "status": "error",
                        "message": "Invalid request"
                    }
                )
                return

            # ----------------------------------------------------
            # INPUTS
            # ----------------------------------------------------

            order_id = request.get("order_id")

            # ZarinPal callback authority.
            authority = (
                request.get("authority")
                or request.get("Authority")
            )

            # Legacy/client field.
            # NEVER treated as payment proof.
            tx_hash = request.get("tx_hash")

            if not order_id:
                self._json_response(
                    400,
                    {
                        "status": "error",
                        "message": "Missing order_id"
                    }
                )
                return

            if not authority:
                self._json_response(
                    400,
                    {
                        "status": "error",
                        "message": "Missing authority",
                        "order_id": order_id,
                        "payment_verified": False,
                        "download_authorized": False
                    }
                )
                return

            # ----------------------------------------------------
            # ORDER LOOKUP
            # ----------------------------------------------------

            orders, order = _find_order(order_id)

            if order is None:
                self._json_response(
                    404,
                    {
                        "status": "error",
                        "message": "Order not found",
                        "order_id": order_id,
                        "payment_verified": False,
                        "download_authorized": False
                    }
                )
                return

            # ----------------------------------------------------
            # ORDER CONTRACT
            # ----------------------------------------------------

            try:
                product_id, amount, currency = (
                    _safe_product_contract(order)
                )
            except Exception as e:
                self._json_response(
                    409,
                    {
                        "status": "error",
                        "message": str(e),
                        "order_id": order_id,
                        "payment_verified": False,
                        "download_authorized": False
                    }
                )
                return

            # ----------------------------------------------------
            # PREVENT REPLAY AFTER PAID
            # ----------------------------------------------------

            if order.get("status") == "PAID":

                self._json_response(
                    409,
                    {
                        "status": "error",
                        "message": "ORDER_ALREADY_PAID",
                        "order_id": order_id,
                        "payment_verified": True,
                        "download_authorized": False
                    }
                )
                return

            # ----------------------------------------------------
            # SERVER-SIDE VERIFICATION
            # ----------------------------------------------------

            payment_method = str(
                order.get("payment_method", "")
            ).lower()

            if payment_method == "crypto":

                from GLOBAL_CRYPTO_VERIFIER_INTEGRATION_V98_15.payment_confirm_verifier_adapter import (
                    verify_crypto_confirmation
                )

                verification = verify_crypto_confirmation(
                    {
                        "order_id": order_id,
                        "product_id": product_id,
                        "amount": amount,
                        "currency": currency,
                        "payment_method": "crypto",
                        "wallet": order.get("wallet"),
                        "asset": order.get("asset"),
                        "network": order.get("network"),
                    },
                    tx_hash=authority,
                    expected_wallet=order.get("wallet"),
                    expected_amount=amount,
                    confirmations_required=1,
                )

            else:

                from payment.zarinpal_gateway import (
                    verify_payment
                )

                verification = verify_payment(
                    {
                        "order_id": order_id,
                        "product_id": product_id,
                        "amount": amount,
                        "currency": currency,
                    },
                    authority
                )

            if not isinstance(
                verification,
                dict
            ):
                raise RuntimeError(
                    "INVALID_VERIFY_RESPONSE"
                )

            if not verification.get("verified"):
                self._json_response(
                    402,
                    {
                        "status": "error",
                        "message": (
                            "Payment verification failed"
                        ),
                        "order_id": order_id,
                        "payment_verified": False,
                        "download_authorized": False,
                        "reason": verification.get(
                            "reason",
                            "VERIFY_FAILED"
                        )
                    }
                )
                return

            # ----------------------------------------------------
            # SECURITY: VERIFY RESPONSE MUST PROVE SERVER VERIFY
            # ----------------------------------------------------

            if verification.get(
                "server_verified"
            ) is not True:

                self._json_response(
                    402,
                    {
                        "status": "error",
                        "message": (
                            "Server verification flag missing"
                        ),
                        "order_id": order_id,
                        "payment_verified": False,
                        "download_authorized": False
                    }
                )
                return

            # ----------------------------------------------------
            # SECURITY: SERVER-SIDE VERIFICATION REQUIRED
            # ----------------------------------------------------

            if verification.get("server_verified") is not True:
                self._json_response(
                    402,
                    {
                        "status": "error",
                        "message": "Server verification flag missing",
                        "order_id": order_id,
                        "payment_verified": False,
                        "download_authorized": False
                    }
                )
                return

            # ----------------------------------------------------
            # REF_ID REQUIRED
            # ----------------------------------------------------

            ref_id = verification.get("ref_id")

            if not ref_id:
                self._json_response(
                    402,
                    {
                        "status": "error",
                        "message": (
                            "Missing gateway reference"
                        ),
                        "order_id": order_id,
                        "payment_verified": False,
                        "download_authorized": False
                    }
                )
                return

            # ----------------------------------------------------
            # ONLY NOW: MARK PAID
            # ----------------------------------------------------

            order["status"] = "PAID"

            # ------------------------------------------------
            # PAYMENT PROVIDER METADATA
            # ------------------------------------------------
            # Crypto payments must never be recorded as
            # ZarinPal payments.
            if payment_method == "crypto":
                order["payment_method"] = "crypto"
                order["gateway"] = "CRYPTO"
            else:
                pass  # ZARINPAL METADATA NOT APPLIED TO CRYPTO
                # ZARINPAL GATEWAY OMITTED FOR CRYPTO

            order["authority"] = str(authority)
            order["ref_id"] = str(ref_id)
            order["verified"] = True
            order["server_verified"] = True
            order["verified_at"] = (
                __import__("datetime")
                .datetime.now()
                .isoformat()
            )

            _save_orders(orders)

            # ----------------------------------------------------
            # ONLY AFTER PAID + SERVER VERIFY:
            # CREATE DOWNLOAD TOKEN
            # ----------------------------------------------------

            token_result = _create_download_token(
                order_id,
                product_id
            )

            if not isinstance(
                token_result,
                dict
            ):
                raise RuntimeError(
                    "INVALID_TOKEN_RESPONSE"
                )

            token = token_result.get("token")
            download_url = token_result.get(
                "download_url"
            )

            if not token:
                raise RuntimeError(
                    "TOKEN_CREATION_FAILED"
                )

            # ----------------------------------------------------
            # SUCCESS
            # ----------------------------------------------------

            self._json_response(
                200,
                {
                    "status": "success",
                    "order_id": order_id,
                    "gateway": "CRYPTO",
                    "payment_verified": True,
                    "server_verified": True,
                    "paid": True,
                    "ref_id": str(ref_id),
                    "download_authorized": True,
                    "token_created": True,
                    "token": token,
                    "download_url": download_url
                }
            )

        except Exception as e:

            print(
                "PAYMENT CONFIRM ERROR:",
                repr(e)
            )

            self._json_response(
                500,
                {
                    "status": "error",
                    "message": (
                        "Payment confirmation failed"
                    ),
                    "payment_verified": False,
                    "download_authorized": False,
                    "token_created": False
                }
            )


if __name__ == "__main__":

    server = HTTPServer(
        ("0.0.0.0", 9002),
        PaymentConfirmHandler
    )

    print(
        "Payment Confirm API running on port 9002 "
        "(SERVER VERIFY REQUIRED)"
    )

    server.serve_forever()
