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



def _resolve_crypto_contract(product_id):
    """
    Resolve the authoritative Global Crypto payment contract.

    Security boundary:
      - product mapping is authoritative
      - client/order wallet is never authoritative
      - amount/currency come from mapping
      - asset/network/standard/destination come from mapping
    """
    import json as _json
    from pathlib import Path as _Path

    _root = _Path(__file__).resolve().parent.parent
    _mapping_file = (
        _root /
        "store_integration" /
        "payment_mapping.json"
    )

    try:
        _mappings = _json.loads(
            _mapping_file.read_text(
                encoding="utf-8"
            )
        )
    except Exception as _exc:
        raise RuntimeError(
            "PAYMENT_MAPPING_UNREADABLE"
        ) from _exc

    _mapping = _mappings.get(product_id)

    if not isinstance(_mapping, dict):
        raise RuntimeError(
            "PRODUCT_MAPPING_NOT_FOUND"
        )

    market = str(
        _mapping.get("market", "")
    ).lower()

    payment_method = str(
        _mapping.get("payment_method", "")
    ).lower()

    if market != "global":
        raise RuntimeError(
            "CRYPTO_GLOBAL_MARKET_REQUIRED"
        )

    if payment_method != "crypto":
        raise RuntimeError(
            "CRYPTO_PAYMENT_METHOD_REQUIRED"
        )

    crypto = _mapping.get("crypto")

    if not isinstance(crypto, dict):
        raise RuntimeError(
            "CRYPTO_CONTRACT_MISSING"
        )

    required = (
        "asset",
        "network",
        "standard",
        "destination",
    )

    for key in required:
        value = crypto.get(key)

        if not isinstance(value, str) or not value.strip():
            raise RuntimeError(
                "CRYPTO_CONTRACT_INCOMPLETE"
            )

    try:
        amount = int(
            _mapping.get("amount")
        )
    except (TypeError, ValueError) as exc:
        raise RuntimeError(
            "CRYPTO_AMOUNT_INVALID"
        ) from exc

    currency = _mapping.get("currency")

    if amount <= 0:
        raise RuntimeError(
            "CRYPTO_AMOUNT_INVALID"
        )

    if not isinstance(currency, str) or not currency.strip():
        raise RuntimeError(
            "CRYPTO_CURRENCY_INVALID"
        )

    return {
        "market": market,
        "payment_method": payment_method,
        "amount": amount,
        "currency": currency.strip(),
        "asset": crypto["asset"].strip(),
        "network": crypto["network"].strip(),
        "standard": crypto["standard"].strip(),
        "destination": crypto["destination"].strip(),
    }

def _create_download_token(
    *args,
    **kwargs,
):
    """
    C-109 compatibility boundary.

    Operational token creation is PostgreSQL-only.
    """
    raise RuntimeError(
        "LEGACY_TOKEN_ENGINE_RETIRED"
    )
# ============================================================
# C-109 | POSTGRES PAYMENT FINALIZATION
# ============================================================

def _c109_db_order_contract(order_id):
    from data_layer.db import (
        build_engine,
        build_session_factory,
        get_database_url,
    )
    from data_layer.repository import get_order

    engine = build_engine(get_database_url())
    SessionFactory = build_session_factory(engine)

    with SessionFactory() as session:
        order = get_order(session, order_id)

        if order is None:
            return None

        return {
            "id": order.id,
            "order_id": order.order_id,
            "product_id": order.product_id,
            "market": order.market,
            "payment_method": order.payment_method,
            "amount": order.amount,
            "currency": order.currency,
            "status": order.status,
            "name": order.name,
            "email": order.email,
        }


def _c109_finalize_verified_payment(
    *,
    order_id,
    product_id,
    payment_method,
    amount,
    currency,
    verification,
):
    import secrets

    from data_layer.db import (
        build_engine,
        build_session_factory,
        get_database_url,
        transaction,
    )
    from data_layer.repository import (
        get_order_for_update,
        create_payment_attempt,
        record_payment_verification,
        mark_order_paid,
        create_download_token,
        get_active_download_token_for_order,
    )

    engine = build_engine(get_database_url())
    SessionFactory = build_session_factory(engine)

    with transaction(SessionFactory) as session:
        order = get_order_for_update(session, order_id)

        if order is None:
            raise ValueError("order not found")

        if order.product_id != product_id:
            raise ValueError("product mismatch")

        if order.amount != amount:
            raise ValueError("amount mismatch")

        if order.currency != currency:
            raise ValueError("currency mismatch")

        if order.payment_method != payment_method:
            raise ValueError("payment method mismatch")

        if order.status == "PAID":
            raise ValueError("order already paid")

        payment = create_payment_attempt(
            session,
            order=order,
            payment_method=payment_method,
            gateway=(
                "CRYPTO"
                if payment_method == "crypto"
                else "ZarinPal"
            ),
            amount=amount,
            currency=currency,
        )

        record_payment_verification(
            session,
            payment,
            verified=True,
            server_verified=True,
            gateway_reference=verification.get("ref_id"),
            verification_data=verification,
        )

        mark_order_paid(
            session,
            order,
            verified=True,
            server_verified=True,
        )

        existing_token = get_active_download_token_for_order(
            session,
            order_id,
        )

        if existing_token is not None:
            token = existing_token.token
        else:
            token = secrets.token_hex(16)

            create_download_token(
                session,
                order=order,
                product_id=product_id,
                token=token,
            )

        return {
            "token": token,
            "download_url": (
                "/pages/download.html?token=" + token
            ),
            "gateway_reference": verification.get("ref_id"),
        }


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

            order = _c109_db_order_contract(order_id)

            if order is None:
                self._json_response(
                    404,
                    {
                        "status": "error",
                        "message": "order not found",
                    },
                )
                return

            orders = None

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

                try:
                    crypto_contract = _resolve_crypto_contract(
                        product_id
                    )
                except RuntimeError as exc:
                    raise RuntimeError(
                        str(exc)
                    ) from exc

                # Canonical mapping is authoritative.
                # Never trust wallet/asset/network from order.
                if (
                    str(
                        order.get("market", "")
                    ).lower() != "global"
                    or crypto_contract["amount"] != int(amount)
                    or crypto_contract["currency"] != str(currency)
                ):
                    raise RuntimeError(
                        "CRYPTO_PRODUCT_CONTRACT_MISMATCH"
                    )

                verification = verify_crypto_confirmation(
                    {
                        "order_id": order_id,
                        "product_id": product_id,
                        "amount": crypto_contract["amount"],
                        "currency": crypto_contract["currency"],
                        "payment_method": "crypto",
                        "wallet": crypto_contract["destination"],
                        "asset": crypto_contract["asset"],
                        # Mapping:
                        # network = TRON
                        # standard = TRC20
                        #
                        # Current adapter's NETWORK contract is TRC20,
                        # therefore the verifier-facing value is standard.
                        "network": crypto_contract["standard"],
                    },
                    tx_hash=authority,
                    expected_wallet=crypto_contract["destination"],
                    expected_amount=crypto_contract["amount"],
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
            # C-109 | POSTGRES ATOMIC FINALIZATION
            # ----------------------------------------------------

            finalization = _c109_finalize_verified_payment(
                order_id=order_id,
                product_id=product_id,
                payment_method=payment_method,
                amount=amount,
                currency=currency,
                verification=verification,
            )

            token = finalization["token"]
            download_url = finalization["download_url"]

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
                , "verified": verification.get("verified"), "confirmations": verification.get("confirmations"), "confirmations_required": verification.get("confirmations_required"), "reason": verification.get("reason"), "actual_amount": verification.get("actual_amount"), "expected_amount": verification.get("expected_amount")}
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
