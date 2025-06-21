import os

# Get the DATABASE_URL from the environment
database_url = os.environ.get('DATABASE_URL')

# If the DATABASE_URL is available, set it in the environment for the workers
if database_url:
    os.environ['DATABASE_URL'] = database_url

# Gunicorn settings
bind = "0.0.0.0:" + os.environ.get("PORT", "8000")
workers = 3 