
from pathlib import Path
import json
from datetime import datetime


BASE = Path(
"/content/drive/MyDrive/FutureMind_Lab_V6.5_LANGUAGE_FIXED_FINAL_20260728"
)


LOG_FILE = (
    BASE /
    "emails" /
    "email_log.json"
)


def save_email_log(
    order_id,
    email,
    product,
    portal_link
):

    if LOG_FILE.exists():

        logs = json.loads(
            LOG_FILE.read_text(
                encoding="utf-8"
            )
        )

    else:

        logs = []


    logs.append({

        "order_id": order_id,

        "email": email,

        "product": product,

        "portal_link": portal_link,

        "status": "READY",

        "date": str(datetime.now())

    })


    LOG_FILE.write_text(

        json.dumps(
            logs,
            indent=2,
            ensure_ascii=False
        ),

        encoding="utf-8"

    )


    return True
