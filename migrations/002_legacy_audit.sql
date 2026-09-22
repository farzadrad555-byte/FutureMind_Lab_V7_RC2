BEGIN;

CREATE TABLE legacy_audit (
    id BIGSERIAL NOT NULL,
    source_type VARCHAR(32) NOT NULL,
    source_identifier VARCHAR(256),
    legacy_order_id VARCHAR(64),
    legacy_token VARCHAR(128),
    legacy_product_id VARCHAR(128),
    legacy_status VARCHAR(64),
    legacy_payload JSONB NOT NULL,
    source_timestamp TIMESTAMP WITH TIME ZONE,
    migration_reason VARCHAR(128) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    PRIMARY KEY (id)
);

COMMIT;
