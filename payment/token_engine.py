"""Legacy token engine retired after C-109.

Operational download-token authority is PostgreSQL.
This module is retained only as a fail-closed
compatibility boundary.
"""


def create_download_token(*args, **kwargs):
    raise RuntimeError(
        "LEGACY_TOKEN_ENGINE_RETIRED"
    )
