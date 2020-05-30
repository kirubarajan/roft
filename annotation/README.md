# Documentation 

The annotation tool is built using the Django library for it's SQLite object-relational mapping. Core logic is written in Python in `core/views.py` and the database schema is specified in `core/models.py`. HTML templates are defined (with built-in Javascript scripts) in `core/templates`.

## Usage
1. Install Django using `pip install django`.
2. Create and structure SQLite database using `python manage.py migrate`.
3. Populate database using `full_generations.json` by running `python populate.py`.
4. Run `python manage.py runserver`.
5. Dump database to JSON using `python manage.py dumpdata > db.json`.

## To-do
- Revise then display highlighting