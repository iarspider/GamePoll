from .base import *

DEBUG = False

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "vote.iarazumov.com", "bote.iarazumov.com"]
SQLITE_PATH = os.getenv("DJANGO_SQLITE_PATH", str(BASE_DIR / "db/db.sqlite3"))
