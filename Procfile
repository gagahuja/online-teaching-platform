release: python manage.py migrate courses --fake && python manage.py migrate --fake
web: gunicorn core.wsgi:application

