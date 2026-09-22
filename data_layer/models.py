from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class OrderModel(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    order_id: Mapped[str] = mapped_column(String(64), nullable=False)
    product_id: Mapped[str] = mapped_column(String(128), nullable=False)
    market: Mapped[str] = mapped_column(String(32), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(32), nullable=False)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str | None] = mapped_column(Text, nullable=True)
    email: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("order_id", name="uq_orders_order_id"),
        Index("ix_orders_product_id", "product_id"),
        Index("ix_orders_market", "market"),
        Index("ix_orders_payment_method", "payment_method"),
        Index("ix_orders_status", "status"),
    )


class PaymentModel(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    order_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("orders.id"),
        nullable=False,
    )
    payment_method: Mapped[str] = mapped_column(String(32), nullable=False)
    gateway: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )
    gateway_reference: Mapped[str | None] = mapped_column(
        String(256),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(16), nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, nullable=False)
    server_verified: Mapped[bool] = mapped_column(Boolean, nullable=False)
    verification_data: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    __table_args__ = (
        Index("ix_payments_order_id", "order_id"),
        Index("ix_payments_payment_method", "payment_method"),
        Index("ix_payments_gateway_reference", "gateway_reference"),
        Index("ix_payments_status", "status"),
    )


class DownloadTokenModel(Base):
    __tablename__ = "download_tokens"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    order_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("orders.id"),
        nullable=False,
    )
    product_id: Mapped[str] = mapped_column(String(128), nullable=False)
    token: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "token",
            name="uq_download_tokens_token",
        ),
        Index("ix_download_tokens_order_id", "order_id"),
        Index("ix_download_tokens_product_id", "product_id"),
        Index("ix_download_tokens_status", "status"),
    )


class DownloadHistoryModel(Base):
    __tablename__ = "download_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    order_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("orders.id"),
        nullable=False,
    )
    token_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("download_tokens.id"),
        nullable=False,
    )
    product_id: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    downloaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_download_history_token_id", "token_id"),
        Index("ix_download_history_order_id", "order_id"),
        Index("ix_download_history_product_id", "product_id"),
        Index(
            "ix_download_history_downloaded_at",
            "downloaded_at",
        ),
    )


class LegacyAuditModel(Base):
    __tablename__ = "legacy_audit"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    source_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )
    source_identifier: Mapped[str | None] = mapped_column(
        String(256),
        nullable=True,
    )
    legacy_order_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )
    legacy_token: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )
    legacy_product_id: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )
    legacy_status: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )
    legacy_payload: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )
    source_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    migration_reason: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
