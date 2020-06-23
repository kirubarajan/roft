
FROM python:3.6-slim

RUN apt-get update && apt-get install --no-install-recommends -y gcc libpq-dev mime-support python-dev default-libmysqlclient-dev  \
    && rm -rf /var/lib/apt/lists/*

RUN pip install 'pipenv==2018.11.26'

COPY /annotation/ /app/
WORKDIR /app/

RUN pipenv install

RUN pipenv run python manage.py collectstatic --noinput
RUN pipenv run python manage.py migrate
RUN pipenv run python populate.py https://storage.googleapis.com/roft_datasets/generations/examples-reddit-stories-test-p0.9.json

CMD ["pipenv", "run", "gunicorn", "-b", "0.0.0.0:80", "trick.wsgi"]