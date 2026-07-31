from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import sys

BASE = Path("/content/drive/MyDrive/FutureMind_Lab_V7_RC2_LANGUAGE_COMPLETE_20260730_0740")

ORDERS = BASE / "orders" / "orders.json"

sys.path.insert(0, str(BASE))

from payment.crypto_gateway import confirm_crypto_payment
from payment.token_engine import create_download_token


class PaymentConfirmHandler(BaseHTTPRequestHandler):

    def do_POST(self):

        try:

            length = int(self.headers["Content-Length"])
            data = self.rfile.read(length)

            request = json.loads(data.decode("utf-8"))

            order_id = request.get("order_id")
            tx_hash = request.get("tx_hash")

            payment = confirm_crypto_payment(tx_hash)

            orders = json.loads(
                ORDERS.read_text(encoding="utf-8")
            )

            result = {}

            for order in orders:

                if order.get("order_id") == order_id:

                    if "payment" not in order:
                        order["payment"] = {}

                    order["payment"]["tx_hash"] = tx_hash
                    order["payment"]["status"] = payment["status"]
                    order["payment_status"] = "PAID"

                    result = create_download_token(
                        order_id,
                        order.get("product_id")
                    )

                    order["download"] = result


            ORDERS.write_text(
                json.dumps(orders, indent=2),
                encoding="utf-8"
            )

            self.send_response(200)
            self.end_headers()

            self.wfile.write(
                json.dumps({
                    "status": "success",
                    "download": result
                }).encode("utf-8")
            )


        except Exception as e:

            print("PAYMENT ERROR:", repr(e))

            self.send_response(500)
            self.end_headers()

            self.wfile.write(
                json.dumps({
                    "error": str(e)
                }).encode("utf-8")
            )


server = HTTPServer(
    ("0.0.0.0", 9002),
    PaymentConfirmHandler
)

print("Payment Confirm API + Token Engine running on port 9002")

server.serve_forever()
