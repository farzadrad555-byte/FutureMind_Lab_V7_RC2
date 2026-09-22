from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import (
    DownloadHistoryModel,
    DownloadTokenModel,
    OrderModel,
    PaymentModel,
)
from .security import (
    require_active_token,
    require_authoritative_amount_currency,
    require_database_available,
    require_download_limit,
    require_known_product,
    require_paid_transition,
    require_production_authorization,
    require_token_issuance,
    require_verified_payment,
    reject_client_payment_fields,
)


class RepositoryError(RuntimeError):
    """Raised when a repository operation cannot be completed safely."""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _require_session(session: Session) -> None:
    require_database_available(session is not None)


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value if value else None


def create_order(
    session: Session,
    *,
    order_id: str,
    product_id: str,
    market: str,
    payment_method: str,
    amount: int,
    currency: str,
    name: str | None = None,
    email: str | None = None,
) -> OrderModel:
    _require_session(session)

    require_known_product(product_id)
    require_authoritative_amount_currency(
        amount=amount,
        currency=currency,
    )

    if not order_id or not order_id.strip():
        raise RepositoryError("order_id is required")

    if not market or not market.strip():
        raise RepositoryError("market is required")

    if not payment_method or not payment_method.strip():
        raise RepositoryError("payment_method is required")

    existing = session.scalar(
        select(OrderModel).where(
            OrderModel.order_id == order_id.strip()
        )
    )

    if existing is not None:
        raise RepositoryError("order_id already exists")

    now = _utcnow()

    order = OrderModel(
        order_id=order_id.strip(),
        product_id=product_id.strip(),
        market=market.strip(),
        payment_method=payment_method.strip(),
        amount=amount,
        currency=currency.strip(),
        status="PENDING",
        name=_clean(name),
        email=_clean(email),
        created_at=now,
        updated_at=now,
    )

    session.add(order)
    session.flush()

    return order


def get_order(
    session: Session,
    order_id: str,
) -> OrderModel | None:
    _require_session(session)

    return session.scalar(
        select(OrderModel).where(
            OrderModel.order_id == order_id.strip()
        )
    )


def get_order_for_update(
    session: Session,
    order_id: str,
) -> OrderModel | None:
    _require_session(session)

    return session.scalar(
        select(OrderModel)
        .where(OrderModel.order_id == order_id.strip())
        .with_for_update()
    )


def mark_order_paid(
    session: Session,
    order: OrderModel,
    *,
    verified: bool,
    server_verified: bool,
) -> OrderModel:
    _require_session(session)

    require_paid_transition(
        current_status=order.status,
        verified=verified,
        server_verified=server_verified,
    )

    order.status = "PAID"
    order.updated_at = _utcnow()

    session.flush()

    return order


def create_payment_attempt(
    session: Session,
    *,
    order: OrderModel,
    payment_method: str,
    gateway: str | None,
    amount: int,
    currency: str,
) -> PaymentModel:
    _require_session(session)

    if order.status == "PAID":
        raise RepositoryError("cannot create payment attempt for PAID order")

    require_authoritative_amount_currency(
        amount=amount,
        currency=currency,
    )

    if amount != order.amount:
        raise RepositoryError("payment amount does not match order")

    if currency.strip() != order.currency:
        raise RepositoryError("payment currency does not match order")

    now = _utcnow()

    payment = PaymentModel(
        order_id=order.id,
        payment_method=payment_method.strip(),
        gateway=_clean(gateway),
        gateway_reference=None,
        status="PENDING",
        amount=amount,
        currency=currency.strip(),
        verified=False,
        server_verified=False,
        verification_data=None,
        created_at=now,
        verified_at=None,
    )

    session.add(payment)
    session.flush()

    return payment


def get_payment(
    session: Session,
    payment_id: int,
) -> PaymentModel | None:
    _require_session(session)

    return session.get(PaymentModel, payment_id)


def record_payment_verification(
    session: Session,
    payment: PaymentModel,
    *,
    verified: bool,
    server_verified: bool,
    gateway_reference: str | None = None,
    verification_data: Mapping[str, Any] | None = None,
) -> PaymentModel:
    _require_session(session)

    require_verified_payment(
        verified=verified,
        server_verified=server_verified,
    )

    payment.verified = True
    payment.server_verified = True
    payment.status = "VERIFIED"

    if gateway_reference is not None:
        payment.gateway_reference = gateway_reference.strip()

    if verification_data is not None:
        payment.verification_data = dict(verification_data)

    payment.verified_at = _utcnow()

    session.flush()

    return payment


def create_download_token(
    session: Session,
    *,
    order: OrderModel,
    product_id: str,
    token: str,
) -> DownloadTokenModel:
    _require_session(session)

    require_known_product(product_id)

    if order.status != "PAID":
        raise RepositoryError(
            "download token requires PAID order"
        )

    if not token or not token.strip():
        raise RepositoryError("token is required")

    # Token issuance is only allowed after a verified payment exists.
    verified_payment = session.scalar(
        select(PaymentModel)
        .where(
            PaymentModel.order_id == order.id,
            PaymentModel.verified.is_(True),
            PaymentModel.server_verified.is_(True),
        )
        .order_by(PaymentModel.id.desc())
    )

    if verified_payment is None:
        raise RepositoryError(
            "no server-verified payment exists"
        )

    require_token_issuance(
        payment_verified=True,
        payment_server_verified=True,
    )

    existing = session.scalar(
        select(DownloadTokenModel).where(
            DownloadTokenModel.token == token.strip()
        )
    )

    if existing is not None:
        raise RepositoryError("token already exists")

    now = _utcnow()

    download_token = DownloadTokenModel(
        order_id=order.id,
        product_id=product_id.strip(),
        token=token.strip(),
        status="ACTIVE",
        created_at=now,
        expires_at=None,
    )

    session.add(download_token)
    session.flush()

    return download_token


def get_download_token(
    session: Session,
    token: str,
) -> DownloadTokenModel | None:
    _require_session(session)

    return session.scalar(
        select(DownloadTokenModel).where(
            DownloadTokenModel.token == token.strip()
        )
    )


def get_active_download_token_for_order(
    session,
    order_id: str,
) -> DownloadTokenModel | None:
    """Return the active download token for an order, if one exists."""
    _require_session(session)

    order = get_order(session, order_id)
    if order is None:
        return None

    return session.execute(
        select(DownloadTokenModel)
        .where(
            DownloadTokenModel.order_id == order.id,
            DownloadTokenModel.status == "ACTIVE",
        )
        .order_by(DownloadTokenModel.id.desc())
    ).scalars().first()


def authorize_download(
    session: Session,
    *,
    token: DownloadTokenModel,
) -> OrderModel:
    _require_session(session)

    require_active_token(token.status)

    order = session.scalar(
        select(OrderModel)
        .where(OrderModel.id == token.order_id)
        .with_for_update()
    )

    if order is None:
        raise RepositoryError("order not found")

    require_production_authorization(
        order_status=order.status,
        payment_method=order.payment_method,
        is_test_data=order.payment_method.upper() == "TEST",
        is_legacy_data=False,
    )

    count = count_downloads(
        session,
        token_id=token.id,
    )

    require_download_limit(count)

    return order


def record_download(
    session: Session,
    *,
    token: DownloadTokenModel,
    order: OrderModel,
) -> DownloadHistoryModel:
    _require_session(session)

    require_active_token(token.status)

    count = count_downloads(
        session,
        token_id=token.id,
    )

    require_download_limit(count)

    event = DownloadHistoryModel(
        order_id=order.id,
        token_id=token.id,
        product_id=token.product_id,
        status="DOWNLOADED",
        downloaded_at=_utcnow(),
    )

    session.add(event)
    session.flush()

    return event


def count_downloads(
    session: Session,
    *,
    token_id: int,
) -> int:
    _require_session(session)

    count = session.scalar(
        select(func.count(DownloadHistoryModel.id)).where(
            DownloadHistoryModel.token_id == token_id,
            DownloadHistoryModel.status == "DOWNLOADED",
        )
    )

    return int(count or 0)
