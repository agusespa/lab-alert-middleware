FROM python:3.11-slim-bookworm

# Set work directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements or pyproject.toml
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy project files
COPY src/ /app/src/
RUN pip install --no-cache-dir .

# Expose port
EXPOSE 5001

# Command to run the application
CMD ["uvicorn", "lab_alert_middleware.main:app", "--host", "0.0.0.0", "--port", "5001"]
