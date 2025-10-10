#!/bin/bash
set -e

# Install the package in editable mode (now that volumes are mounted)
echo "Installing wagtail-seotoolkit in editable mode..."
cd /app
pip install -e . --no-deps

# Go back to testproject directory
cd /app/testproject

# Wait for database to be ready
echo "Waiting for database..."
until python -c "import psycopg2; psycopg2.connect('$DATABASE_URL')" 2>/dev/null; do
  echo "Database is unavailable - sleeping"
  sleep 1
done
echo "Database is ready!"

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Load initial data only if not already loaded
echo "Checking if initial data needs to be loaded..."
if ! python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); exit(0 if User.objects.filter(username='admin').exists() else 1)" 2>/dev/null; then
    echo "Loading initial data..."
    python manage.py load_initial_data
else
    echo "Initial data already loaded, skipping..."
fi

echo "Starting development server..."

# Execute the command passed to the container
exec "$@"
