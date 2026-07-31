
def purchase_confirmation(
    name,
    product,
    order_id,
    download_link
):

    return f"""
FutureMind Lab

Hello {name},

Your purchase has been confirmed.

Product:
{product}

Order ID:
{order_id}

Your secure download link:

{download_link}

Download limit:
3 times

Thank you for choosing FutureMind Lab.

Support:
support@futuremindlab.com
"""
