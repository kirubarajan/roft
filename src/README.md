# Documentation 

The annotation tool is built using the Django library for it's MySQL object-relational mapping. Core logic is written in Python in `core/views.py` and the database schema is specified in `core/models.py`. HTML templates are defined (with built-in Javascript scripts) in `core/templates`.

## Usage
1. Install Django using `pip install django`.
2. Populate database using `full_generations.json` by running `python populate.py`.
3. Run `python manage.py runserver`.
4. Dump database to JSON using `python manage.py dumpdata > db.json`.
