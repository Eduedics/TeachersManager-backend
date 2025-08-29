#!/bin/bash
# Safe Django reset script
# Removes ONLY your project DB and migration files, never Django itself.

echo "Cleaning files..."

# Remove SQLite database if it exists
if [ -f db.sqlite3 ]; then
  rm db.sqlite3
  echo "Removed db.sqlite3"
else
  echo " No db.sqlite3 found"
fi

# Delete all migrations except __init__.py inside *your apps* only
find . -path "./venv" -prune -o -path "*/migrations/*.py" -not -name "__init__.py" -delete
echo "Removed migration files (excluding __init__.py)"

# Clear __pycache__ files
find . -path "./venv" -prune -o -name "__pycache__" -exec rm -rf {} +
echo "Cleared __pycache__"

# Recreate migrations
python manage.py makemigrations
python manage.py migrate

echo "its a Fresh start ."
echo "Creating default superuser..."

# Auto create superuser (change creds below if you like)
DJANGO_SUPERUSER_USERNAME=admin \
DJANGO_SUPERUSER_EMAIL=admin@example.com \
DJANGO_SUPERUSER_PASSWORD=admin123 \
python manage.py createsuperuser --noinput

echo "superuserCreated. Superuser = admin / admin123"

#usage Make it executable:chmod +x reset_django.sh
#run:./reset_django.sh


