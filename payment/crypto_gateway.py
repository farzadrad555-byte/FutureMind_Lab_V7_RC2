
# FutureMind Lab V6.5 Crypto Gateway

from payment_config import CRYPTO_CONFIG


def create_crypto_payment(product_name, amount):
    return {
        "status": "pending",
        "provider": "CRYPTO",
        "currency": CRYPTO_CONFIG["currency"],
        "network": CRYPTO_CONFIG["network"],
        "product": product_name,
        "amount": amount,
        "wallet": CRYPTO_CONFIG["wallet_address"]
    }


def confirm_crypto_payment(tx_hash):
    if tx_hash:
        return {
            "status": "paid",
            "provider": "CRYPTO",
            "tx_hash": tx_hash
        }

    return {
        "status": "pending"
    }


# ================================================================
# GLOBAL CRYPTO SERVER-SIDE VERIFICATION
# SANDBOX / FAIL-CLOSED
# ================================================================

def verify_crypto_payment(payment_data, tx_hash):
    """
    Global crypto verification boundary.

    This function is intentionally fail-closed.

    No:
      - blockchain RPC
      - wallet API
      - transaction broadcast
      - real payment verification

    A client-supplied tx_hash is NEVER treated as proof.
    """

    if not isinstance(payment_data, dict):
        return {
            "verified": False,
            "server_verified": False,
            "reason": "INVALID_PAYMENT_DATA"
        }

    if not tx_hash:
        return {
            "verified": False,
            "server_verified": False,
            "reason": "MISSING_TX_HASH"
        }

    return {
        "verified": False,
        "server_verified": False,
        "reason": "CRYPTO_SANDBOX_VERIFICATION_DISABLED",
        "tx_hash": str(tx_hash)
    }
