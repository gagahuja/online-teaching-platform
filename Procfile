release: python manage.py migrate --fake courses zero && python manage.py migrate --fake-initial && python manage.py migrate
web: gunicorn core.wsgi:application


