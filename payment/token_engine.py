
import secrets
import json
from pathlib import Path
from datetime import datetime


BASE = Path("/content/drive/MyDrive/FutureMind_Lab_V7_RC2_LANGUAGE_COMPLETE_20260730_0740")

TOKENS_FILE = BASE / "orders" / "download_tokens.json"


def create_download_token(order_id, product):

    token = secrets.token_hex(16)

    if TOKENS_FILE.exists():
        tokens = json.loads(
            TOKENS_FILE.read_text(encoding="utf-8")
        )
    else:
        tokens = []

    tokens.append({
        "token": token,
        "order_id": order_id,
        "product": product,
        "status": "ACTIVE",
        "created": str(datetime.now()),
        "downloads": 0
    })

    TOKENS_FILE.write_text(
        json.dumps(tokens, indent=2),
        encoding="utf-8"
    )

    return {
        "token": token,
        "download_url": "/pages/download.html?token=" + token
    }
