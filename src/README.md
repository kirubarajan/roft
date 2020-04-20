# Documentation 

The annotation tool is built using the Django library for it's MySQL object-relational mapping.

## Usage
1. Install Django using `pip install django`.
2. Run `python manage.py runserver`.
3. Create Prompts, Evaluation Texts, and Tags at `/admin` (after running `python3 manage.py createsuperuser`).
4. Dump database to JSON using `python manage.py dumpdata > db.json`.