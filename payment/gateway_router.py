"""
FutureMind Lab
Multi-Gateway Router

PRIMARY:
    ZarinPal

FAILOVER:
    IDPay

SECURITY:
    FAIL-CLOSED

IMPORTANT:
    Router never creates download tokens.
    Router never directly changes order to PAID.
"""

import json
from pathlib import Path

from .zarinpal_gateway import ZarinPalGateway
from .idpay_gateway import IDPayGateway


class MultiGatewayRouter:

    def __init__(self, root):
        self.root = Path(root)

        config_path = (
            self.root /
            "payment" /
            "gateway_config.json"
        )

        self.config = json.loads(
            config_path.read_text(
                encoding="utf-8"
            )
        )

        self.primary = (
            self.config["routing"]["primary"]
        )

        self.fallback = (
            self.config["routing"]["fallback"]
        )

        self.gateways = {
            "zarinpal": ZarinPalGateway(
                sandbox=True
            ),
            "idpay": IDPayGateway(
                sandbox=True
            )
        }

    def status(self):
        return {
            "mode": self.config["mode"],
            "real_gateway_enabled":
                self.config["real_gateway_enabled"],
            "primary": self.primary,
            "fallback": self.fallback,
            "gateways": {
                name: gateway.status()
                for name, gateway
                in self.gateways.items()
            }
        }

    def create_payment(self, order):
        """
        Fail-closed.

        A disabled gateway cannot create a payment.
        """

        if not self.config["real_gateway_enabled"]:
            return {
                "ok": False,
                "reason": "REAL_GATEWAY_DISABLED"
            }

        primary = self.gateways[self.primary]

        result = primary.create_payment(order)

        if result.get("ok"):
            return result

        # Failover is allowed only for creation failure.
        fallback = self.gateways[self.fallback]

        return fallback.create_payment(order)

    def verify_payment(self, gateway, order, callback):

        if not self.config["real_gateway_enabled"]:
            return {
                "verified": False,
                "reason": "REAL_GATEWAY_DISABLED"
            }

        if gateway not in self.gateways:
            return {
                "verified": False,
                "reason": "UNKNOWN_GATEWAY"
            }

        return self.gateways[gateway].verify_payment(
            order,
            callback
        )

    def security_contract(self):

        return {
            "router_creates_tokens": False,
            "router_sets_paid": False,
            "server_side_verification_required": True,
            "order_binding_required": True,
            "product_binding_required": True,
            "amount_match_required": True,
            "currency_match_required": True
        }
