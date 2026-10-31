# Brightloop Subscription Management

Subscriptions, recurring invoices, payments and revenue reporting for a subscription business. Built with Django and PostgreSQL.

## Setup

```
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Database

Without configuration the project uses a local SQLite file, which is enough to try it out. To use PostgreSQL, create a database and set these environment variables before running `migrate`:

| Variable | Default |
|---|---|
| `DB_NAME` | (required to switch to PostgreSQL) |
| `DB_USER` | `postgres` |
| `DB_PASSWORD` | empty |
| `DB_HOST` | `localhost` |
| `DB_PORT` | `5432` |

## Email

Password reset and invoice emails print to the console by default. To send real mail set `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend` along with `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD`.
