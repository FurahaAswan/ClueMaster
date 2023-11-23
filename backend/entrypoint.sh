#!/bin/sh

mkdir game/migrations
touch game/migrations/__init__.py

python manage.py makemigrations
python manage.py migrate --no-input
python manage.py collectstatic

daphne -b 0.0.0.0 -p 8000 cluemaster.asgi:application