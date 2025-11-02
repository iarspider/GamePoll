from .base import *

DEBUG = True

ALLOWED_HOSTS = ["vote.iarazumov.com", "bote.iarazumov.com", "127.0.0.1"]
SQLITE_PATH = os.getenv("DJANGO_SQLITE_PATH", str(BASE_DIR / "db.sqlite3"))