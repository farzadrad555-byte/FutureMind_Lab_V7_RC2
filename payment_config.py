
# FutureMind Lab V6.5 Crypto Payment Configuration

PAYMENT_PROVIDER = "CRYPTO"

CRYPTO_CONFIG = {
    "currency": "USDT",
    "network": "TRC20",
    "wallet_address": "TWZ14JzzPTfaR659Avy7XgQgMeKH98NEbC",
    "enabled": True
}

STRIPE_CONFIG = {
    "enabled": False,
    "secret_key": ""
}

TEST_CONFIG = {
    "enabled": True
}


# ================================================================
# FUTUREMIND GLOBAL CRYPTO CANONICAL CONTRACT — V49
# SANDBOX / FAIL-CLOSED
# ================================================================

GLOBAL_CRYPTO_CONTRACT = {
    "market": "global",
    "product_id": "hunter-x-v44",
    "amount": 49,
    "currency": "USD",
    "payment": "crypto",
    "asset": "USDT",
    "network": "TRON",
    "standard": "TRC20",
}

# Security gates — MUST remain fail-closed.
REAL_GATEWAY_ENABLED = False
SANDBOX = True
BLOCKCHAIN_RPC_ENABLED = False
WALLET_API_ENABLED = False
TOKEN_CREATION_ENABLED = False
DOWNLOAD_AUTHORIZATION_ENABLED = False
PRODUCTION_WRITE_ENABLED = False

# Never use a placeholder as a real destination.
CRYPTO_DESTINATION = "TEST_DESTINATION_ONLY"
