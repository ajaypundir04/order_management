-- migrate:up
CREATE TABLE orders (
    id VARCHAR(36) PRIMARY KEY,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    type VARCHAR(10) NOT NULL,
    side VARCHAR(10) NOT NULL,
    instrument VARCHAR(12) NOT NULL,
    limit_price FLOAT,
    quantity INTEGER NOT NULL
);

-- migrate:down
DROP TABLE orders;