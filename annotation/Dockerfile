
FROM python:3.6-slim

LABEL maintainer="Catacomb"

# Install build dependencies
RUN apt-get update && apt-get install --no-install-recommends -y gcc libpq-dev mime-support python-dev  \
    && rm -rf /var/lib/apt/lists/*

# Install pipenv
RUN pip install pipenv

RUN mkdir /app/
WORKDIR /app/

# Copy project dependencies
COPY Pipfile* /app/

# Install project dependencies
RUN pipenv install --deploy

# Copy project files
COPY . /app/

RUN pipenv run python /app/manage.py collectstatic --noinput
RUN pipenv run python /app/manage.py migrate

CMD ["pipenv", "run", "gunicorn", "-b", "0.0.0.0:80", "trick.wsgi"]