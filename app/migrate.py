import os
import mysql.connector
from mysql.connector import Error
import time

def run_migrations():
    max_retries = 5
    retry_delay = 5  # seconds
    db_host = os.environ.get("DB_HOST", "localhost")
    db_user = os.environ.get("DB_USER", "root")
    db_password = os.environ.get("DB_PASSWORD", "password")
    db_name = os.environ.get("DB_NAME", "lemon_markets")
    for attempt in range(max_retries):
        try:
            # Connect to the database
            connection = mysql.connector.connect(
                host=db_host,
                user=db_user,
                password=db_password,
                database=db_name
            )

            cursor = connection.cursor()
            print("Connected to database: lemon_markets")

            # Define migration queries
            migration_queries = [
                """
                CREATE TABLE IF NOT EXISTS orders (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    order_id VARCHAR(36) UNIQUE NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    type VARCHAR(10) NOT NULL,
                    side VARCHAR(10) NOT NULL,
                    status VARCHAR(10) NOT NULL,
                    instrument VARCHAR(12) NOT NULL,
                    limit_price FLOAT,
                    quantity INTEGER NOT NULL
                );
                """,
                """
                CREATE TABLE IF NOT EXISTS order_matching (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    order_buy_id INT NOT NULL,
                    order_sell_id INT NOT NULL,
                    matched_quantity INT NOT NULL,
                    matched_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    instrument VARCHAR(12) NOT NULL,
                    FOREIGN KEY (order_buy_id) REFERENCES orders(id) ON DELETE RESTRICT,
                    FOREIGN KEY (order_sell_id) REFERENCES orders(id) ON DELETE RESTRICT,
                    CHECK (matched_quantity > 0)
                );
                """
            ]

            # Execute migration queries
            for query in migration_queries:
                cursor.execute(query)
                print("Executed migration query successfully")

            # Commit changes
            connection.commit()
            print("Database migrations completed successfully")
            break  # Exit retry loop on success

        except Error as e:
            print(f"Error during migration (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("Max retries reached. Migration failed.")
                raise
        finally:
            # Close cursor and connection if they exist
            if 'cursor' in locals():
                cursor.close()
            if 'connection' in locals() and connection.is_connected():
                connection.close()
                print("Database connection closed")

if __name__ == "__main__":
    run_migrations()