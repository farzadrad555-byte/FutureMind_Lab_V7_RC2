
"""
FutureMind Iran Gateway Adapter
R-GATEWAY-17

Production rules:
- Credentials NEVER stored in source code.
- Real payment disabled until explicitly configured.
- Callback is NOT payment proof.
- Verification must happen server-side.
- Product/amount/currency/order binding mandatory.
- No token creation here.
"""

import os
from dataclasses import dataclass


class IranGatewayError(Exception):
    pass


@dataclass
class GatewayPaymentRequest:
    gateway: str
    order_id: str
    product_id: str
    amount: int
    currency: str


@dataclass
class GatewayPaymentResult:
    status: str
    gateway: str
    order_id: str
    payment_url: str | None = None
    gateway_reference: str | None = None
    verified: bool = False
    real_transaction: bool = False


class IranGatewayAdapter:

    SUPPORTED = {
        "zarinpal",
        "idpay",
    }

    def __init__(self, gateway_name: str):
        gateway_name = gateway_name.lower().strip()

        if gateway_name not in self.SUPPORTED:
            raise IranGatewayError(
                "UNSUPPORTED_IRAN_GATEWAY"
            )

        self.gateway = gateway_name

        self.enabled = os.getenv(
            f"{gateway_name.upper()}_ENABLED",
            "false"
        ).lower() == "true"

        self.merchant_id = os.getenv(
            f"{gateway_name.upper()}_MERCHANT_ID"
        )

        self.api_key = os.getenv(
            f"{gateway_name.upper()}_API_KEY"
        )

        self.callback_url = os.getenv(
            "PAYMENT_CALLBACK_URL"
        )

    def status(self):
        return {
            "gateway": self.gateway,
            "enabled": self.enabled,
            "credentials_present": bool(
                self.merchant_id or self.api_key
            ),
            "callback_configured": bool(
                self.callback_url
            ),
            "real_transaction": False,
        }

    def create_payment(
        self,
        order_id,
        product_id,
        amount,
        currency
    ):
        """
        Contract only.

        Actual PSP request is intentionally blocked
        until production adapter implementation and
        credentials are explicitly configured.
        """

        if not self.enabled:
            raise IranGatewayError(
                "GATEWAY_DISABLED"
            )

        if not (self.merchant_id or self.api_key):
            raise IranGatewayError(
                "GATEWAY_CREDENTIALS_MISSING"
            )

        if currency != "IRR":
            raise IranGatewayError(
                "IRAN_GATEWAY_CURRENCY_MISMATCH"
            )

        if amount <= 0:
            raise IranGatewayError(
                "INVALID_AMOUNT"
            )

        return GatewayPaymentResult(
            status="ADAPTER_READY",
            gateway=self.gateway,
            order_id=order_id,
            verified=False,
            real_transaction=False,
        )

    def verify_payment(
        self,
        order_id,
        product_id,
        amount,
        currency,
        gateway_reference
    ):
        """
        Server-side verification contract.

        IMPORTANT:
        This method must call the PSP's official verification
        endpoint before returning verified=True.

        Current controlled build deliberately returns
        unverified.
        """

        if not gateway_reference:
            return {
                "verified": False,
                "reason": "NO_GATEWAY_REFERENCE",
                "gateway": self.gateway,
                "order_id": order_id,
            }

        return {
            "verified": False,
            "reason": "REAL_GATEWAY_VERIFY_NOT_CONFIGURED",
            "gateway": self.gateway,
            "gateway_reference": gateway_reference,
            "order_id": order_id,
            "product_id": product_id,
            "amount": amount,
            "currency": currency,
        }

    def handle_callback(self, payload):
        """
        Callback parser only.

        Callback never directly produces PAID.
        """

        if not isinstance(payload, dict):
            raise IranGatewayError(
                "INVALID_CALLBACK"
            )

        return {
            "gateway": self.gateway,
            "order_id": payload.get("order_id"),
            "gateway_reference": (
                payload.get("gateway_reference")
                or payload.get("Authority")
                or payload.get("id")
                or payload.get("track_id")
            ),
            "callback_received": True,
            "verified": False,
            "paid_transition": False,
            "token_created": False,
        }
