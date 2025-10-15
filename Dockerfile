FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=bakerydemo.settings.dev

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy testproject requirements only
COPY testproject/requirements/ /app/testproject/requirements/

# Install Python dependencies (excluding our package for now)
RUN pip install --upgrade pip && \
    pip install -r /app/testproject/requirements/base.txt

# Copy entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Set working directory to testproject for Django commands
WORKDIR /app/testproject

# Expose port
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["docker-entrypoint.sh"]

# Run Django development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
