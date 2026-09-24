
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse, parse_qs
import secrets
import sys

sys.path.append(
    "/content/drive/MyDrive/FutureMind_Lab_V5/admin/security"
)

from admin.security.auth import check_login

from payment_config import CRYPTO_CONFIG

from payment.crypto_gateway import create_crypto_payment, confirm_crypto_payment
from payment.gateway_router import MultiGatewayRouter


BASE = Path(__file__).resolve().parent
ORDERS = BASE / "orders" / "orders.json"

SESSIONS = set()


class Handler(SimpleHTTPRequestHandler):

    def end_headers(self):

        if self.path.endswith(".html") or self.path == "/":
            self.send_header(
                "Content-Type",
                "text/html; charset=utf-8"
            )

        super().end_headers()


    def secure_download(self):

        from urllib.parse import urlparse, parse_qs

        query = parse_qs(
            urlparse(self.path).query
        )

        token = query.get(
            "token",
            [""]
        )[0]


        tokens_file = BASE / "orders" / "download_tokens.json"


        if not tokens_file.exists():

            self.send_error(404)
            return


        tokens = json.loads(
            tokens_file.read_text(
                encoding="utf-8"
            )
        )


        valid = None

        for item in tokens:

            if item.get("token") == token and item.get("status") == "ACTIVE":

                valid = item
                break


        # Check PAID order status

        if valid:

            orders_file = BASE / "orders" / "orders.json"

            if orders_file.exists():

                orders = json.loads(
                    orders_file.read_text(
                        encoding="utf-8"
                    )
                )

                paid = False

                for order in orders:

                    if (
                        order.get("order_id") == valid.get("order_id")
                        and order.get("status") == "PAID"
                    ):
                        paid = True
                        break


                if not paid:

                    self.send_error(403)
                    return


        if not valid:

            self.send_error(403)

            return


        # Dynamic Product Download Engine
        # V7 RC2 Multi Product

        mapping_file = BASE / "store_integration" / "payment_mapping.json"

        mappings = json.loads(
            mapping_file.read_text(
                encoding="utf-8"
            )
        )

        product_id = valid.get("product_id")

        package = None

        if product_id in mappings:
            package = mappings[product_id].get(
                "download_package"
            )


        if not package:
            self.send_error(404)
            return


        file_path = (
            BASE /
            "downloads" /
            package
        )


        if not file_path.exists():

            self.send_error(404)

            return


        # Download Limit V6.2

        MAX_DOWNLOADS = 3

        history_file = BASE / "orders" / "download_history.json"

        if history_file.exists():

            history_check = json.loads(
                history_file.read_text(
                    encoding="utf-8"
                )
            )

        else:

            history_check = []

        download_count = sum(
            1 for item in history_check
            if item.get("token") == token
        )

        if download_count >= MAX_DOWNLOADS:
            self.send_error(403)
            return


        self.send_response(200)

        self.send_header(
            "Content-Type",
            "application/zip"
        )

        self.end_headers()


        # Save Download History V6.2

        history_file = BASE / "orders" / "download_history.json"

        if history_file.exists():

            history = json.loads(
                history_file.read_text(
                    encoding="utf-8"
                )
            )

        else:

            history = []


        history.append({

            "order_id": valid.get("order_id"),

            "product_id": valid.get("product_id"),

            "token": token,

            "date": str(datetime.now()),

            "status": "DOWNLOADED"

        })


        history_file.write_text(

            json.dumps(
                history,
                indent=2,
                ensure_ascii=False
            ),

            encoding="utf-8"

        )


        with open(file_path,"rb") as f:

            self.wfile.write(
                f.read()
            )


    def do_GET(self):
        # ZarinPal callback — SERVER-SIDE VERIFICATION
        if self.path.startswith("/api/zarinpal/callback"):
            from urllib.parse import urlparse, parse_qs
            from payment.zarinpal_gateway import verify_payment
            from api.payment_confirm import (
                _c109_db_order_contract,
                _c109_finalize_verified_payment,
                _safe_product_contract,
            )

            parsed = urlparse(self.path)
            qs = parse_qs(parsed.query)

            order_id = qs.get("order_id", [None])[0]
            authority = qs.get("Authority", [None])[0]
            status = qs.get("Status", [None])[0]

            response = {
                "ok": False,
                "gateway": "zarinpal",
                "order_id": order_id,
                "gateway_reference": authority,
                "token_created": False,
                "paid": False,
            }

            try:
                if not order_id or not authority:
                    raise ValueError("Missing order_id or Authority")

                if str(status).upper() != "OK":
                    raise ValueError("ZARINPAL_CALLBACK_NOT_SUCCESS")

                order = _c109_db_order_contract(order_id)

                if order is None:
                    raise ValueError("Order not found")

                if order.get("status") == "PAID":
                    raise ValueError("ORDER_ALREADY_PAID")

                product_id, amount, currency = _safe_product_contract(order)

                verification = verify_payment(
                    order,
                    authority
                )

                if not isinstance(verification, dict):
                    raise ValueError("Invalid verification response")

                if verification.get("verified") is not True:
                    raise ValueError("PAYMENT_NOT_VERIFIED")

                if verification.get("server_verified") is not True:
                    raise ValueError("SERVER_VERIFICATION_REQUIRED")

                payment_method = str(
                    order.get("payment_method", "zarinpal")
                ).lower()

                finalization = _c109_finalize_verified_payment(
                    order_id=order_id,
                    product_id=product_id,
                    payment_method=payment_method,
                    amount=amount,
                    currency=currency,
                    verification=verification,
                )

                response.update({
                    "ok": True,
                    "payment_verified": True,
                    "download_authorized": True,
                    "token_created": True,
                    "download_url": finalization["download_url"],
                    "paid": True,
                    "gateway_reference": (
                        finalization.get("gateway_reference")
                        or verification.get("ref_id")
                        or authority
                    ),
                })

            except Exception as e:
                response.update({
                    "error": str(e),
                    "payment_verified": False,
                    "download_authorized": False,
                })

            self.send_response(200)
            self.send_header(
                "Content-Type",
                "application/json; charset=utf-8"
            )
            self.end_headers()

            self.wfile.write(
                json.dumps(
                    response,
                    ensure_ascii=False
                ).encode("utf-8")
            )
            return


        # ----------------------------------------------------------
        # R98-STATIC-DOWNLOAD-FAIL-CLOSED
        # ----------------------------------------------------------
        # Product ZIP packages must NEVER be served through the
        # SimpleHTTPRequestHandler static fallback.
        #
        # Authorized delivery is handled only by the explicit
        # token/payment-protected download routes above.
        #
        # This blocks direct public access such as:
        #   /downloads/Hunter-X_Professional.zip
        #
        # IMPORTANT:
        #   - no payment state is created here
        #   - no token is accepted here
        #   - no product file is served here
        #   - explicit secure-download route remains unchanged
        # ----------------------------------------------------------

        from urllib.parse import urlparse

        _r98_path = urlparse(self.path).path

        if (
            _r98_path == "/downloads"
            or _r98_path.startswith("/downloads/")
        ):
            self.send_error(403, "Direct download access forbidden")
            return

        # ----------------------------------------------------------
        # R98-STATIC-DOWNLOAD-FAIL-CLOSED END
        # ----------------------------------------------------------

        # C-109 | POSTGRES AUTHORITATIVE DOWNLOAD INFO
        if self.path.startswith("/api/download-info"):
            try:
                from urllib.parse import urlparse, parse_qs
                from data_layer.db import (
                    build_engine,
                    build_session_factory,
                    get_database_url,
                    transaction,
                )
                from data_layer.repository import (
                    get_download_token,
                    authorize_download,
                    count_downloads,
                )
                from data_layer.security import MAX_DOWNLOADS

                query = parse_qs(urlparse(self.path).query)
                token_value = query.get("token", [""])[0].strip()

                if not token_value:
                    self.send_error(400, "missing token")
                    return

                engine = build_engine(get_database_url())
                SessionFactory = build_session_factory(engine)

                with transaction(SessionFactory) as session:
                    token = get_download_token(session, token_value)

                    if token is None:
                        self.send_error(403, "invalid download token")
                        return

                    order = authorize_download(
                        session,
                        token=token,
                    )

                    downloads = count_downloads(
                        session,
                        token_id=token.id,
                    )

                    mapping_file = BASE / "store_integration" / "payment_mapping.json"
                    mappings = json.loads(
                        mapping_file.read_text(encoding="utf-8")
                    )

                    product_id = token.product_id
                    mapping = mappings.get(product_id)

                    if not isinstance(mapping, dict):
                        self.send_error(404, "unknown product")
                        return

                    product_name = mapping.get(
                        "product_name",
                        product_id,
                    )

                    order_public_id = getattr(
                        order,
                        "order_id",
                        str(order.id),
                    )

                    payload = {
                        "product": product_name,
                        "order_id": order_public_id,
                        "downloads": downloads,
                        "limit": MAX_DOWNLOADS,
                        "remaining": max(0, MAX_DOWNLOADS - downloads),
                        "token_status": token.status,
                    }

                body = json.dumps(
                    payload,
                    ensure_ascii=False,
                ).encode("utf-8")

                self.send_response(200)
                self.send_header(
                    "Content-Type",
                    "application/json; charset=utf-8"
                )
                self.send_header(
                    "Content-Length",
                    str(len(body))
                )
                self.end_headers()
                self.wfile.write(body)
                return

            except Exception as e:
                self.send_error(403, str(e))
                return

        # C-109 | POSTGRES AUTHORITATIVE SECURE DOWNLOAD
        if self.path.startswith("/api/secure-download"):
            try:
                from urllib.parse import urlparse, parse_qs
                from data_layer.db import (
                    build_engine,
                    build_session_factory,
                    get_database_url,
                    transaction,
                )
                from data_layer.repository import (
                    get_download_token,
                    authorize_download,
                    record_download,
                )

                query = parse_qs(urlparse(self.path).query)
                token_value = query.get("token", [""])[0].strip()

                if not token_value:
                    self.send_error(400, "missing token")
                    return

                mapping_file = BASE / "store_integration" / "payment_mapping.json"
                mappings = json.loads(
                    mapping_file.read_text(encoding="utf-8")
                )

                engine = build_engine(get_database_url())
                SessionFactory = build_session_factory(engine)

                with transaction(SessionFactory) as session:
                    token = get_download_token(session, token_value)

                    if token is None:
                        self.send_error(403, "invalid download token")
                        return

                    order = authorize_download(
                        session,
                        token=token,
                    )

                    product_id = token.product_id
                    mapping = mappings.get(product_id)

                    if not isinstance(mapping, dict):
                        self.send_error(404, "unknown product")
                        return

                    package = mapping.get("download_package")

                    if not isinstance(package, str) or not package.strip():
                        self.send_error(404, "download package missing")
                        return

                    file_path = (
                        BASE /
                        "downloads" /
                        package
                    )

                    if not file_path.exists() or not file_path.is_file():
                        self.send_error(404, "download file not found")
                        return

                    record_download(
                        session,
                        token=token,
                        order=order,
                    )

                file_size = file_path.stat().st_size

                self.send_response(200)
                self.send_header(
                    "Content-Type",
                    "application/zip"
                )
                self.send_header(
                    "Content-Disposition",
                    f'attachment; filename="{file_path.name}"'
                )
                self.send_header(
                    "Content-Length",
                    str(file_size)
                )
                self.end_headers()

                with file_path.open("rb") as f:
                    while True:
                        chunk = f.read(1024 * 1024)
                        if not chunk:
                            break
                        self.wfile.write(chunk)

                return

            except Exception as e:
                self.send_error(403, str(e))
                return

        # SECURITY BOUNDARY — FAIL CLOSED FOR INTERNAL FILES
        from urllib.parse import urlparse

        _static_path = urlparse(self.path).path

        # Product packages must never be served directly.
        if (
            _static_path == "/downloads"
            or _static_path.startswith("/downloads/")
        ):
            self.send_error(403, "Direct download access forbidden")
            return

        _blocked_exact = {
            "/api",
            "/api/",
            "/server.py",
        }

        _blocked_suffixes = (
            ".py",
            ".pyc",
            ".pyo",
            ".env",
            ".ini",
            ".yaml",
            ".yml",
            ".toml",
        )

        if (
            _static_path in _blocked_exact
            or _static_path.endswith(_blocked_suffixes)
            or "/__pycache__/" in _static_path
            or "/.git/" in _static_path
        ):
            self.send_error(403, "Access forbidden")
            return

        # Public storefront/static assets remain available.
        from urllib.parse import urlparse

        _static_path = urlparse(self.path).path

        # Product packages must never be served directly.
        if (
            _static_path == "/downloads"
            or _static_path.startswith("/downloads/")
        ):
            self.send_error(403, "Direct download access forbidden")
            return

        _blocked_exact = {
            "/api",
            "/api/",
            "/server.py",
        }

        _blocked_suffixes = (
            ".py",
            ".pyc",
            ".pyo",
            ".env",
            ".ini",
            ".yaml",
            ".yml",
            ".toml",
        )

        if (
            _static_path in _blocked_exact
            or _static_path.endswith(_blocked_suffixes)
            or "/__pycache__/" in _static_path
            or "/.git/" in _static_path
        ):
            self.send_error(403, "Access forbidden")
            return

        # Public storefront/static assets remain available.
        return SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):

        length = int(self.headers.get("Content-Length",0))
        data = self.rfile.read(length)

        try:
            body = json.loads(data.decode("utf-8"))
        except:
            body = {}

        # Admin Login
        if self.path == "/api/login":

            username = body.get("username")
            password = body.get("password")

            if check_login(username,password):

                token = secrets.token_hex(16)
                SESSIONS.add(token)

                self.send_response(200)
                self.send_header(
                    "Content-Type",
                    "application/json"
                )
                self.end_headers()

                self.wfile.write(
                    json.dumps({
                        "status":"success",
                        "token":token
                    }).encode()
                )

            else:

                self.send_response(401)
                self.end_headers()

            return



        # Payment Request V6.5 Stripe Checkout Ready
        if self.path == "/api/payment/request":

            payment_id = "PAY-" + secrets.token_hex(4).upper()

            response = {
                "status": "success",
                "payment_id": payment_id,
                "gateway": "TEST",
                "message": "Test payment mode"
            }


            if False:

                try:

                    checkout_url = create_checkout_session(
                        STRIPE_SECRET_KEY,
                        "Hunter-X V44 Professional",
                        49,
                        CURRENCY
                    )

                    response = {
                        "status": "success",
                        "payment_id": payment_id,
                        "gateway": "STRIPE",
                        "checkout_url": checkout_url
                    }


                except Exception as e:

                    response = {
                        "status": "error",
                        "message": str(e)
                    }


            self.send_response(200)
            self.send_header(
                "Content-Type",
                "application/json"
            )
            self.end_headers()

            self.wfile.write(
                json.dumps(response).encode()
            )

            return



        # Payment Confirm — SERVER-SIDE VERIFICATION

        if self.path == "/api/payment/confirm":

            try:
                from api.payment_confirm import (
                    _c109_db_order_contract,
                    _c109_finalize_verified_payment,
                    _safe_product_contract,
                    _resolve_crypto_contract,
                )

                order_id = body.get("order_id")
                authority = (
                    body.get("authority")
                    or body.get("Authority")
                )

                if not order_id or not authority:
                    raise ValueError(
                        "Missing order_id or authority"
                    )

                order = _c109_db_order_contract(order_id)

                if order is None:
                    self.send_response(404)
                    self.send_header(
                        "Content-Type",
                        "application/json; charset=utf-8"
                    )
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "status": "error",
                        "message": "Order not found",
                        "payment_verified": False,
                        "download_authorized": False
                    }).encode("utf-8"))
                    return

                if order.get("status") == "PAID":
                    self.send_response(409)
                    self.send_header(
                        "Content-Type",
                        "application/json; charset=utf-8"
                    )
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "status": "error",
                        "message": "ORDER_ALREADY_PAID",
                        "payment_verified": True,
                        "download_authorized": False
                    }).encode("utf-8"))
                    return

                product_id, amount, currency = (
                    _safe_product_contract(order)
                )

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
                        self.send_error(
                            402,
                            str(exc)
                        )
                        return

                    # Canonical mapping is authoritative.
                    # Never trust wallet/asset/network from order.
                    if (
                        str(
                            order.get("market", "")
                        ).lower() != "global"
                        or crypto_contract["amount"] != int(amount)
                        or crypto_contract["currency"] != str(currency)
                    ):
                        self.send_error(
                            402,
                            "CRYPTO_PRODUCT_CONTRACT_MISMATCH"
                        )
                        return

                    verification = verify_crypto_confirmation(
                        {
                            "order_id": order_id,
                            "product_id": product_id,
                            "amount": crypto_contract["amount"],
                            "currency": crypto_contract["currency"],
                            "payment_method": "crypto",
                            "wallet": crypto_contract["destination"],
                            "asset": crypto_contract["asset"],
                            # Mapping network=TRON and
                            # standard=TRC20. The current adapter's
                            # NETWORK contract is TRC20.
                            "network": crypto_contract["standard"],
                        },
                        tx_hash=authority,
                        expected_wallet=crypto_contract["destination"],
                        expected_amount=crypto_contract["amount"],
                        confirmations_required=1,
                    )
                else:
                    from payment.zarinpal_gateway import verify_payment

                    verification = verify_payment(
                        {
                            "order_id": order_id,
                            "product_id": product_id,
                            "amount": amount,
                            "currency": currency,
                        },
                        authority
                    )

                if not isinstance(verification, dict):
                    raise RuntimeError("INVALID_VERIFY_RESPONSE")

                if not verification.get("verified"):
                    self.send_response(402)
                    self.send_header(
                        "Content-Type",
                        "application/json; charset=utf-8"
                    )
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "status": "error",
                        "message": "Payment verification failed",
                        "payment_verified": False,
                        "download_authorized": False,
                        "reason": verification.get(
                            "reason", "VERIFY_FAILED"
                        )
                    }).encode("utf-8"))
                    return

                if verification.get("server_verified") is not True:
                    self.send_response(402)
                    self.send_header(
                        "Content-Type",
                        "application/json; charset=utf-8"
                    )
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "status": "error",
                        "message": "Server verification flag missing",
                        "payment_verified": False,
                        "download_authorized": False
                    }).encode("utf-8"))
                    return

                # C-109 | POSTGRES ATOMIC FINALIZATION

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

                self.send_response(200)
                self.send_header(
                    "Content-Type",
                    "application/json; charset=utf-8"
                )
                self.end_headers()

                self.wfile.write(json.dumps({
                    "status": "success",
                    "order_id": order_id,
                    "product_id": product_id,
                    "payment_verified": True,
                    "download_authorized": True,
                    "download_token": token,
                    "download_url": download_url,
                    "gateway_reference": verification.get("ref_id")
                }, ensure_ascii=False).encode("utf-8"))

                return

            except Exception as e:
                self.send_response(402)
                self.send_header(
                    "Content-Type",
                    "application/json; charset=utf-8"
                )
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "error",
                    "message": str(e),
                    "payment_verified": False,
                    "download_authorized": False
                }, ensure_ascii=False).encode("utf-8"))
                return








        # C-109 | POSTGRES AUTHORITATIVE DOWNLOAD INFO
        if self.path.startswith("/api/download-info"):
            try:
                from urllib.parse import urlparse, parse_qs
                from data_layer.db import (
                    build_engine,
                    build_session_factory,
                    get_database_url,
                    transaction,
                )
                from data_layer.repository import (
                    get_download_token,
                    authorize_download,
                    count_downloads,
                )
                from data_layer.security import MAX_DOWNLOADS

                query = parse_qs(urlparse(self.path).query)
                token_value = query.get("token", [""])[0].strip()

                if not token_value:
                    self.send_error(400, "missing token")
                    return

                engine = build_engine(get_database_url())
                SessionFactory = build_session_factory(engine)

                with transaction(SessionFactory) as session:
                    token = get_download_token(session, token_value)

                    if token is None:
                        self.send_error(403, "invalid download token")
                        return

                    order = authorize_download(
                        session,
                        token=token,
                    )

                    downloads = count_downloads(
                        session,
                        token_id=token.id,
                    )

                    mapping_file = BASE / "store_integration" / "payment_mapping.json"
                    mappings = json.loads(
                        mapping_file.read_text(encoding="utf-8")
                    )

                    product_id = token.product_id
                    mapping = mappings.get(product_id)

                    if not isinstance(mapping, dict):
                        self.send_error(404, "unknown product")
                        return

                    product_name = mapping.get(
                        "product_name",
                        product_id,
                    )

                    order_public_id = getattr(
                        order,
                        "order_id",
                        str(order.id),
                    )

                    payload = {
                        "product": product_name,
                        "order_id": order_public_id,
                        "downloads": downloads,
                        "limit": MAX_DOWNLOADS,
                        "remaining": max(0, MAX_DOWNLOADS - downloads),
                        "token_status": token.status,
                    }

                body = json.dumps(
                    payload,
                    ensure_ascii=False,
                ).encode("utf-8")

                self.send_response(200)
                self.send_header(
                    "Content-Type",
                    "application/json; charset=utf-8"
                )
                self.send_header(
                    "Content-Length",
                    str(len(body))
                )
                self.end_headers()
                self.wfile.write(body)
                return

            except Exception as e:
                self.send_error(403, str(e))
                return

        # C-109 | POSTGRES AUTHORITATIVE SECURE DOWNLOAD
        if self.path.startswith("/api/secure-download"):
            try:
                from urllib.parse import urlparse, parse_qs
                from data_layer.db import (
                    build_engine,
                    build_session_factory,
                    get_database_url,
                    transaction,
                )
                from data_layer.repository import (
                    get_download_token,
                    authorize_download,
                    record_download,
                )

                query = parse_qs(urlparse(self.path).query)
                token_value = query.get("token", [""])[0].strip()

                if not token_value:
                    self.send_error(400, "missing token")
                    return

                mapping_file = BASE / "store_integration" / "payment_mapping.json"
                mappings = json.loads(
                    mapping_file.read_text(encoding="utf-8")
                )

                engine = build_engine(get_database_url())
                SessionFactory = build_session_factory(engine)

                with transaction(SessionFactory) as session:
                    token = get_download_token(session, token_value)

                    if token is None:
                        self.send_error(403, "invalid download token")
                        return

                    order = authorize_download(
                        session,
                        token=token,
                    )

                    product_id = token.product_id
                    mapping = mappings.get(product_id)

                    if not isinstance(mapping, dict):
                        self.send_error(404, "unknown product")
                        return

                    package = mapping.get("download_package")

                    if not isinstance(package, str) or not package.strip():
                        self.send_error(404, "download package missing")
                        return

                    file_path = (
                        BASE /
                        "downloads" /
                        package
                    )

                    if not file_path.exists() or not file_path.is_file():
                        self.send_error(404, "download file not found")
                        return

                    record_download(
                        session,
                        token=token,
                        order=order,
                    )

                file_size = file_path.stat().st_size

                self.send_response(200)
                self.send_header(
                    "Content-Type",
                    "application/zip"
                )
                self.send_header(
                    "Content-Disposition",
                    f'attachment; filename="{file_path.name}"'
                )
                self.send_header(
                    "Content-Length",
                    str(file_size)
                )
                self.end_headers()

                with file_path.open("rb") as f:
                    while True:
                        chunk = f.read(1024 * 1024)
                        if not chunk:
                            break
                        self.wfile.write(chunk)

                return

            except Exception as e:
                self.send_error(403, str(e))
                return

        # SECURITY BOUNDARY — FAIL CLOSED FOR INTERNAL FILES
        from urllib.parse import urlparse

        _static_path = urlparse(self.path).path

        # Product packages must never be served directly.
        if (
            _static_path == "/downloads"
            or _static_path.startswith("/downloads/")
        ):
            self.send_error(403, "Direct download access forbidden")
            return

        _blocked_exact = {
            "/api",
            "/api/",
            "/server.py",
        }

        _blocked_suffixes = (
            ".py",
            ".pyc",
            ".pyo",
            ".env",
            ".ini",
            ".yaml",
            ".yml",
            ".toml",
        )

        if (
            _static_path in _blocked_exact
            or _static_path.endswith(_blocked_suffixes)
            or "/__pycache__/" in _static_path
            or "/.git/" in _static_path
        ):
            self.send_error(403, "Access forbidden")
            return

        # Public storefront/static assets remain available.
        return super().do_GET()

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', '0'))
        raw_body = self.rfile.read(content_length) if content_length else b'{}'

        try:
            body = json.loads(raw_body.decode('utf-8'))
        except Exception:
            self.send_error(400, 'Invalid JSON body')
            return

        if not isinstance(body, dict):
            self.send_error(400, 'JSON body must be an object')
            return
        # Customer Order
        if self.path.split('?', 1)[0] == '/api/order':

            mapping_file = (
                BASE /
                "store_integration" /
                "payment_mapping.json"
            )

            try:
                mappings = json.loads(
                    mapping_file.read_text(
                        encoding="utf-8"
                    )
                )
            except Exception:
                self.send_error(
                    500,
                    "Payment mapping unavailable"
                )
                return

            product_id = body.get("product_id")

            if not product_id or product_id == "unknown":
                self.send_error(
                    400,
                    "Missing product_id"
                )
                return

            mapping = mappings.get(product_id)

            if not isinstance(mapping, dict):
                self.send_error(
                    404,
                    "Product payment mapping not found"
                )
                return

            if mapping.get("payment_required") is not True:
                self.send_error(
                    400,
                    "Payment is not configured for this product"
                )
                return

            market = str(
                mapping.get("market", "")
            ).lower()

            payment_method = str(
                mapping.get("payment_method", "")
            ).lower()

            if market == "iran":
                if payment_method not in (
                    "zarinpal",
                    "idpay",
                ):
                    self.send_error(
                        400,
                        "Unsupported Iran payment method"
                    )
                    return

            elif (
                market == "global"
                and payment_method == "crypto"
            ):
                try:
                    _resolve_crypto_contract(
                        product_id
                    )
                except RuntimeError as exc:
                    self.send_error(
                        400,
                        str(exc)
                    )
                    return

            else:
                self.send_error(
                    400,
                    "Unsupported market/payment mapping"
                )
                return

            amount = mapping.get("amount")
            currency = mapping.get("currency")

            if amount is None or not currency or not payment_method:
                self.send_error(
                    500,
                    "Incomplete payment contract"
                )
                return

            try:
                amount = int(amount)
            except (TypeError, ValueError):
                self.send_error(
                    500,
                    "Invalid payment amount"
                )
                return

            if amount <= 0:
                self.send_error(
                    500,
                    "Invalid payment amount"
                )
                return

            order_id = (
                "FM-" +
                secrets.token_hex(4).upper()
            )

            # PostgreSQL is authoritative for persisted orders.
            # Client-supplied payment/crypto fields are never persisted.
            from data_layer.db import (
                build_engine,
                build_session_factory,
                get_database_url,
            )
            from data_layer.repository import create_order
            from data_layer.security import reject_client_payment_fields

            clean_body = reject_client_payment_fields(dict(body))

            engine = build_engine(get_database_url())
            SessionFactory = build_session_factory(engine)

            with SessionFactory() as session:
                with session.begin():
                    db_order = create_order(
                        session,
                        order_id=order_id,
                        product_id=product_id,
                        market=market,
                        payment_method=payment_method,
                        amount=amount,
                        currency=currency,
                        name=clean_body.get("name"),
                        email=clean_body.get("email"),
                    )

                order = dict(clean_body)
                order["order_id"] = db_order.order_id
                order["date"] = db_order.created_at.isoformat()
                order["product_id"] = db_order.product_id
                order["amount"] = db_order.amount
                order["currency"] = db_order.currency
                order["payment_method"] = db_order.payment_method
                order["market"] = db_order.market
                order["status"] = db_order.status

            router = MultiGatewayRouter(BASE)

            payment_result = router.create_payment(
                order
            )

            response = {
                "status": (
                    "success"
                    if payment_result.get("ok")
                    else "error"
                ),
                "order_id": order_id,
                "payment_required": True,
                "payment": payment_result
            }

            if payment_result.get("ok"):
                if payment_result.get("payment_url"):
                    response["payment_url"] = (
                        payment_result["payment_url"]
                    )

                response["gateway"] = (
                    payment_result.get("gateway")
                )

            self.send_response(
                200
                if payment_result.get("ok")
                else 503
            )

            self.send_header(
                "Content-Type",
                "application/json"
            )

            self.end_headers()

            self.wfile.write(
                json.dumps(
                    response,
                    ensure_ascii=False
                ).encode("utf-8")
            )

            return

        self.send_error(404)
        return

        # Product Download API V6
        self.send_error(404)



import os

PORT = int(os.environ.get("PORT", 8001))

if __name__ == "__main__":
    print(f"FutureMind Lab Security Server V2 running on {PORT}")

    HTTPServer(
        ("0.0.0.0", PORT),
        Handler
    ).serve_forever()
