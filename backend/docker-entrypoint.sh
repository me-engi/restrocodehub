#!/bin/sh

set -e

cd /opt/app

# Apply database migrations
echo "================== Applying Migrations =================="
python manage.py migrate --noinput

# Collect static files
echo "================== Collecting Static Files =================="
python manage.py collectstatic --noinput

# Start the application
echo "================== Starting Gunicorn =================="
exec gunicorn --bind 0.0.0.0:8000 culinary_api.wsgi:application