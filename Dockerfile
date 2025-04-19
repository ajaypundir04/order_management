FROM python:3.9-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && \
    apt-get install -y \
    libmariadb-dev-compat libxslt-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy application and migration files into the container
COPY ./app ./app
COPY ./db ./db

EXPOSE 8000

# Run migrations and then start the app
CMD ["sh", "-c", "python app/migrate.py && uvicorn app.web.order_controller:app --host 0.0.0.0 --port 8000"]
