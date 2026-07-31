
from datetime import datetime


def create_download_email(
    name,
    product,
    order_id,
    token
):

    link = (
        "/pages/download.html?token="
        + token
    )

    email = f"""
FutureMind Lab

Hello {name},

Your order is ready.

Product:
{product}

Order ID:
{order_id}

Secure Download Portal:

{link}

Download Limit:
3 times

Created:
{datetime.now()}

Thank you.
FutureMind Lab
"""

    return email
