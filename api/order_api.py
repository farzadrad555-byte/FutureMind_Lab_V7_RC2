
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
from datetime import datetime
import sys
import uuid

BASE = Path("/content/drive/MyDrive/FutureMind_Lab_V6.5_CRYPTO_WORK")
ORDERS = BASE / "orders" / "orders.json"

sys.path.insert(0, str(BASE))

from payment.crypto_gateway import create_crypto_payment


def create_order_id():
    return "FM-" + datetime.now().strftime("%Y%m%d") + "-" + uuid.uuid4().hex[:6].upper()


class OrderHandler(BaseHTTPRequestHandler):

    def do_POST(self):

        if self.path.endswith("/order"):

            length = int(self.headers["Content-Length"])
            data = self.rfile.read(length)

            order = json.loads(data.decode("utf-8"))

            order["order_id"] = create_order_id()

            payment = create_crypto_payment(
                order.get("product", "Unknown Product"),
                order.get("amount", 0)
            )

            order["payment"] = payment
            order["payment_status"] = "PENDING_PAYMENT"
            order["date"] = str(datetime.now())

            if ORDERS.exists():
                orders = json.loads(
                    ORDERS.read_text(encoding="utf-8")
                )
            else:
                orders = []

            orders.append(order)

            ORDERS.write_text(
                json.dumps(
                    orders,
                    indent=2
                ),
                encoding="utf-8"
            )

            self.send_response(200)
            self.end_headers()

            self.wfile.write(
                json.dumps({
                    "status": "success",
                    "order_id": order["order_id"],
                    "payment_status": "PENDING_PAYMENT",
                    "payment": payment
                }).encode("utf-8")
            )

        else:
            self.send_response(404)
            self.end_headers()


server = HTTPServer(
    ("0.0.0.0", 9001),
    OrderHandler
)

print("FutureMind Lab V6.5 Crypto Order API with Order ID running on port 9001")

server.serve_forever()
