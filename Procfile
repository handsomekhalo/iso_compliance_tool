release: python manage.py wait_for_db && python manage.py migrate
web: gunicorn iso_compliance.wsgi --bind 0.0.0.0:${PORT:-8000} --log-file -