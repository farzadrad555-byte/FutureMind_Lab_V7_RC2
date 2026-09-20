BEGIN;

CREATE TABLE orders (
 id BIGSERIAL NOT NULL,
 order_id VARCHAR(64) NOT NULL,
 product_id VARCHAR(128) NOT NULL,
 market VARCHAR(32) NOT NULL,
 payment_method VARCHAR(32) NOT NULL,
 amount BIGINT NOT NULL,
 currency VARCHAR(16) NOT NULL,
 status VARCHAR(32) NOT NULL,
 name TEXT,
 email TEXT,
 created_at TIMESTAMP WITH TIME ZONE NOT NULL,
 updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
 PRIMARY KEY (id),
 CONSTRAINT uq_orders_order_id UNIQUE (order_id)
);

CREATE TABLE payments (
 id BIGSERIAL NOT NULL,
 order_id BIGINT NOT NULL,
 payment_method VARCHAR(32) NOT NULL,
 gateway VARCHAR(64),
 gateway_reference VARCHAR(256),
 status VARCHAR(32) NOT NULL,
 amount BIGINT NOT NULL,
 currency VARCHAR(16) NOT NULL,
 verified BOOLEAN NOT NULL,
 server_verified BOOLEAN NOT NULL,
 verification_data JSONB,
 created_at TIMESTAMP WITH TIME ZONE NOT NULL,
 verified_at TIMESTAMP WITH TIME ZONE,
 PRIMARY KEY (id),
 FOREIGN KEY(order_id) REFERENCES orders (id)
);

CREATE TABLE download_tokens (
 id BIGSERIAL NOT NULL,
 order_id BIGINT NOT NULL,
 product_id VARCHAR(128) NOT NULL,
 token VARCHAR(128) NOT NULL,
 status VARCHAR(32) NOT NULL,
 created_at TIMESTAMP WITH TIME ZONE NOT NULL,
 expires_at TIMESTAMP WITH TIME ZONE,
 PRIMARY KEY (id),
 CONSTRAINT uq_download_tokens_token UNIQUE (token),
 FOREIGN KEY(order_id) REFERENCES orders (id)
);

CREATE TABLE download_history (
 id BIGSERIAL NOT NULL,
 order_id BIGINT NOT NULL,
 token_id BIGINT NOT NULL,
 product_id VARCHAR(128) NOT NULL,
 status VARCHAR(32) NOT NULL,
 downloaded_at TIMESTAMP WITH TIME ZONE NOT NULL,
 PRIMARY KEY (id),
 FOREIGN KEY(order_id) REFERENCES orders (id),
 FOREIGN KEY(token_id) REFERENCES download_tokens (id)
);

COMMIT;
