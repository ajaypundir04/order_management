# Order Management Solution

## Overview
This solution implements a REST API for placing stock orders via a `POST /orders` endpoint, as per the provided task requirements. The system uses Python with FastAPI, SQLAlchemy, and MySQL to store orders, process them asynchronously, and place them on a stock exchange. 

## Decisions and Assumptions

### Technology Stack
- **Python**: 
- **FastAPI**: 
- **SQLAlchemy**: Selected for ORM to manage database interactions, providing flexibility and transaction safety.
- **MySQL**: 
- **pytest**: 

### Database Schema
- **Orders Table**:
  - Stores order details: `id`, `order_id` (UUID), `created_at`, `type`, `side`, `status`, `instrument`, `limit_price`, `quantity`.
  - `status` uses an ENUM (`OPEN`, `PARTIAL`, `MATCHED`, `SUBMITTED`, `FAILED`) to track order lifecycle.
- **Order Matching Table**:
  - Added to record matches between buy and sell orders: `id`, `order_buy_id`, `order_sell_id`, `matched_quantity`, `matched_at`, `instrument`.
  - Foreign keys ensure referential integrity with `orders`.

**Assumption**: The stock exchange (`place_order`) may be unreliable (e.g., connection errors), so orders are stored and enqueued before placement to ensure reliability.

### Architecture
- **Service Layer (`OrderService`)**:
  - Handles `POST /orders` requests, validates input via `OrderRequest` DTO, maps to `Order` entity, saves to database, and enqueues for processing.
  - Uses dependency injection for `Session` and `StockExchangeProcessor`.
- **Processor Layer (`StockExchangeProcessor`)**:
  - Runs a background thread to process orders asynchronously from a queue.
  - Matches buy and sell orders internally before calling `place_order`.
  - Implements retry logic for transient `OrderPlacementError` (e.g., connection issues).
- **Repository Layer**:
  - `OrderRepository` and `OrderMatchingRepository` encapsulate database operations, ensuring clean separation of concerns.
- **Entity Layer**:
  - `Order` and `OrderMatching` entities map to database tables, using a shared `declarative_base` to avoid foreign key issues.
- **DTOs and Mappers**:
  - `OrderRequest` and `OrderResponse` DTOs validate input/output.
  - `OrderMapper` converts between DTOs and entities.

**Assumption**: Orders are limit orders, and matching occurs when buy `limit_price` ≥ sell `limit_price` for the same `instrument`.

### Scalability and Reliability
- **Asynchronous Processing**:
  - Orders are enqueued in a thread-safe `queue.Queue` and processed in a background thread, decoupling the API from stock exchange reliability.
  - Ensures the `POST /orders` endpoint returns quickly (201 status) after saving and enqueuing, meeting requirement 3.
- **Retry Mechanism**:
  - Handles transient `OrderPlacementError` with up to 3 retries and 5-second delays, improving reliability.
- **Database Transactions**:
  - Uses SQLAlchemy sessions with explicit commits/rollbacks to ensure data consistency.
- **Order Matching**:
  - Matches orders internally to reduce external `place_order` calls, improving efficiency and simulating a basic order book.
- **Error Handling**:
  - Catches exceptions in `OrderService` and `StockExchangeProcessor`, returning 500 with `{"message": "Internal server error while placing the order"}` for API errors.
  - Logs detailed errors for debugging.

**Assumption**: The stock exchange does not provide immediate confirmation, so enqueuing guarantees eventual placement.


### Key Code Components
- **OrderService**:
  - Validates input, saves orders, enqueues for processing, and returns response.
  - Uses dependency injection for `Session` and `StockExchangeProcessor`.
- **StockExchangeProcessor**:
  - Processes orders in a background thread.
  - Matches orders based on `instrument`, `side`, and `limit_price`.
  - Records matches in `order_matching` table via `OrderMatchingRepository`.
  - Retries `place_order` for transient errors.
- **Entities and Repositories**:
  - `Order` and `OrderMatching` entities map to database tables.
  - `OrderRepository` and `OrderMatchingRepository` handle database operations.
- **Migration**:
  - Creates `orders` and `order_matching` tables with foreign keys and indexes.

## Bonus Tasks 
### High Volume of Async Updates via Socket Connection
To handle async updates (e.g., execution information) from the stock exchange:
- **WebSocket Integration**:
  - Add a WebSocket endpoint in FastAPI to receive updates from the stock exchange.
  - Example: `/ws/orders/updates` to handle execution messages.
- **Message Queue**:
  - Use a message broker (e.g., RabbitMQ, Kafka) to process updates asynchronously.
  - Publish updates to a queue, consumed by a worker to update `orders` and `order_matching` tables.
- **Database Updates**:
  - Add an `executions` table: `id`, `order_id`, `executed_quantity`, `executed_price`, `executed_at`.
  - Update `orders.quantity` and `status` based on execution data (e.g., `MATCHED` if fully executed).
- **Event-Driven Processing**:
  - Use an event loop to process updates, ensuring scalability for high volumes.
  - Implement idempotency to handle duplicate updates (e.g., using execution IDs).
- **Scalability**:
  - Deploy multiple worker instances to consume updates from the queue.
  - Use database connection pooling to handle concurrent updates.
- **Reliability**:
  - Store incoming updates in a persistent queue before processing to prevent data loss.
  - Implement retry logic for database update failures.


## Future Improvements
1. **Distributed Processing**:
   - Replace `queue.Queue` with a distributed queue (e.g., RabbitMQ) for multi-instance processing.
   - Deploy `StockExchangeProcessor` as a separate service with multiple workers.
2. **Advanced Order Matching**:
  Use a more efficient data structure for price-time precedence, such as a balanced binary search tree (e.g., AVL or Red-Black tree) or a heap-based priority queue for each price level.
  - Reduces time complexity for inserting and removing orders (from O(n log n) for sorting to O(log n) for tree operations).
  - Improves matching performance for large order books
3. **Monitoring and Metrics**:
   - Add Prometheus metrics for order processing rate, match rate, and error rate.
   - Integrate with a logging service (e.g., ELK stack) for centralized logs.
4. **Database Optimization**:
   - Add indexes on `orders` (`instrument`, `status`, `limit_price`) for faster matching.
   - Use partitioning for `order_matching` to handle high volumes.
5. **Security**:
   - Add authentication/authorization to the API (e.g., JWT).
   - Validate `instrument` against a known list to prevent invalid data.
6. **Testing Enhancements**:
   - Add performance tests to simulate high order volumes.
   - Implement chaos testing to verify reliability under stock exchange failures.
7. **Async Updates**:
   - Fully implement the WebSocket/message queue solution for execution updates.
   - Add a status update API (e.g., `GET /orders/{id}`) to query execution details.

## Challenges Faced

- **Order Matching Issue**:
  - Implementing order matching was my first attempt at building an order book-like system using python.
- **Asynchronous Processing**:
  - Using a background thread in `StockExchangeProcessor` to process orders was new to me. I had issues with thread safety and ensuring the queue didn’t block the API response.
  - **Challenge**: Learning Python’s `threading` and `queue` modules, and debugging why some orders weren’t processed, was a steep learning curve.  
- Ensuring consistency between `orders` (use transactions).

## Assumptions
- The API doesn’t need authentication for this task.
- Simple Order matching with audits can be found in the order_matching table.
- **Basic Error Handling**: I assumed catching all exceptions and rolling back is sufficient, but database errors might need retries or better status updates.
- **Specific Retry Condition**: I assumed retries only for “Connection not available” errors are enough, but other errors might need retries too.
- **Single-Threaded Processing Sufficient**: I assumed one background thread in `StockExchangeProcessor` is enough for now, but  it might not handle many orders quickly, which could be a problem for scalability.
- **In-Memory Queue Safe**: I assumed using `queue.Queue` is fine, but  if the app crashes, enqueued orders could be lost, which might break the guarantee of order placement.
- Handling high throughput (optimize database queries, use batch updates).

## Conclusion
The solution meets all requirements with a scalable, reliable architecture. The `OrderService` and `StockExchangeProcessor` handle order creation, storage, matching, and placement, with robust error handling and logging. Tests cover unit, integration, and end-to-end scenarios, and bonus tasks are addressed with proposed implementations. Future improvements focus on distributed processing, advanced matching, and monitoring to handle real-world trading volumes.