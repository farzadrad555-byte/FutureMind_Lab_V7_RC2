"""
FutureMind Lab
IDPay Gateway Adapter

SAFE CONTRACT:
- No credentials hardcoded
- No PAID transition
- No token creation
- Server-side verification required
"""

import os


class IDPayGateway:

    name = "idpay"

    def __init__(self, sandbox=True):
        self.sandbox = bool(sandbox)

        self.api_key = os.getenv(
            "IDPAY_API_KEY"
        )

        self.callback_url = os.getenv(
            "IDPAY_CALLBACK_URL"
        )

    def status(self):
        return {
            "gateway": self.name,
            "enabled": bool(
                self.api_key and
                self.callback_url
            ),
            "credentials_present": bool(
                self.api_key
            ),
            "callback_configured": bool(
                self.callback_url
            ),
            "sandbox": self.sandbox,
            "real_transaction": False
        }

    def create_payment(self, order):

        if not self.api_key:
            return {
                "ok": False,
                "reason": "IDPAY_API_KEY_NOT_CONFIGURED"
            }

        if not self.callback_url:
            return {
                "ok": False,
                "reason": "IDPAY_CALLBACK_NOT_CONFIGURED"
            }

        return {
            "ok": False,
            "reason": "REAL_GATEWAY_LIVE_DISABLED",
            "gateway": self.name
        }

    def verify_payment(self, order, callback):

        return {
            "verified": False,
            "gateway": self.name,
            "reason": "REAL_GATEWAY_VERIFY_NOT_CONFIGURED"
        }
