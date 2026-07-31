
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
