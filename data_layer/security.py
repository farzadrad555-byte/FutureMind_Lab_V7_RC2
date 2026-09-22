from __future__ import annotations

from decimal import Decimal
from typing import Any, Mapping


MAX_DOWNLOADS = 3


class SecurityContractError(RuntimeError):
    """Raised when a security invariant is violated."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SecurityContractError(message)


def require_verified_payment(
    *,
    verified: bool,
    server_verified: bool,
) -> None:
    require(
        verified is True,
        "payment is not verified",
    )
    require(
        server_verified is True,
        "payment is not server-verified",
    )


def require_paid_transition(
    *,
    current_status: str,
    verified: bool,
    server_verified: bool,
) -> None:
    require(
        current_status != "PAID",
        "order is already PAID",
    )
    require_verified_payment(
        verified=verified,
        server_verified=server_verified,
    )


def require_token_issuance(
    *,
    payment_verified: bool,
    payment_server_verified: bool,
) -> None:
    require_verified_payment(
        verified=payment_verified,
        server_verified=payment_server_verified,
    )


def require_active_token(status: str) -> None:
    require(
        status == "ACTIVE",
        "download token is not ACTIVE",
    )


def require_download_limit(download_count: int) -> None:
    require(
        isinstance(download_count, int) and not isinstance(download_count, bool),
        "download_count must be an integer",
    )
    require(
        download_count < MAX_DOWNLOADS,
        "maximum download count reached",
    )


def require_production_authorization(
    *,
    order_status: str,
    payment_method: str,
    is_test_data: bool,
    is_legacy_data: bool,
) -> None:
    require(
        is_test_data is False,
        "test data cannot authorize production download",
    )
    require(
        is_legacy_data is False,
        "legacy data cannot authorize production download",
    )
    require(
        order_status == "PAID",
        "order is not PAID",
    )
    require(
        payment_method.strip() != "",
        "payment method is missing",
    )


def require_known_product(product_id: str | None) -> None:
    require(
        isinstance(product_id, str) and bool(product_id.strip()),
        "unknown product",
    )


def require_authoritative_amount_currency(
    *,
    amount: int,
    currency: str,
) -> None:
    require(
        isinstance(amount, int) and not isinstance(amount, bool),
        "amount must be an integer",
    )
    require(
        amount > 0,
        "amount must be positive",
    )
    require(
        isinstance(currency, str) and bool(currency.strip()),
        "currency is missing",
    )


def reject_client_payment_fields(
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    forbidden = {
        "tx_hash",
        "transaction_hash",
        "gateway_reference",
        "verified",
        "server_verified",
        "payment_status",
        "payment_method",
        "amount",
        "currency",
        "wallet",
        "wallet_address",
        "asset",
        "network",
        "standard",
    }

    return {
        key: value
        for key, value in payload.items()
        if key not in forbidden
    }


def require_database_available(database_ok: bool) -> None:
    require(
        database_ok is True,
        "database unavailable",
    )
