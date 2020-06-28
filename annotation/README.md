# Documentation

The annotation tool is built using the Django library for it's SQLite object-relational mapping. Core logic is written in Python in `core/views.py` and the database schema is specified in `core/models.py`. HTML templates are defined (with built-in Javascript scripts) in `core/templates`.

Dependency and virtual environment management is handled using pipenv.

## Usage
1. Install dependencies using `pipenv install`.
2. Create and structure SQLite database using `pipenv run python manage.py migrate`.
3. Populate database by running `pipenv run python populate.py generations.json`.
4. Run `pipenv run python manage.py runserver`.
5. Dump database to JSON using `pipenv run python manage.py dumpdata > db.json`.

## Troubleshooting
If you are getting an error that your building wheel for mysqlclient failed
after running `pipenv install` on OSX, then run this line:
`export LIBRARY_PATH=$LIBRARY_PATH:/usr/local/opt/openssl/lib/`
