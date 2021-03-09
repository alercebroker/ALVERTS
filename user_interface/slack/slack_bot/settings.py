import os

STAGE = os.getenv("BOT_STAGE", "develop")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_SIGNATURE = os.getenv("SLACK_SIGNATURE")


PROFILE = False

HOST = os.getenv("DB_HOST", "localhost")
DATABASE = os.getenv("DB_DATABASE", "local")
USER = os.getenv("DB_USER", "user")
PASSWORD = os.getenv("DB_PASSWORD", "pass")
PORT = os.getenv("DB_PORT", 5432)
SQLALCHEMY_DATABASE_URL = f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}"

DATABASE = {"SQL": {"SQLALCHEMY_DATABASE_URL": SQLALCHEMY_DATABASE_URL}}

if STAGE == "production":
    LAST_NIGHT_STATS_CHANNELS = ["chikigang", "recentsupernova"]
    LAST_NIGHT_STATS_SCHEDULE = ["10:00", "11:00", "12:00"]

elif STAGE == "develop":
    LAST_NIGHT_STATS_CHANNELS = ["blog-javier"]
    LAST_NIGHT_STATS_SCHEDULE = ["17:15", "17:16"]
else:
    LAST_NIGHT_STATS_CHANNELS = ["chikigang"]
    LAST_NIGHT_STATS_SCHEDULE = ["10:00", "11:00", "12:00"]

CONFIG = {
    "every_day": {
        "last_night_stats": {
            "channels": LAST_NIGHT_STATS_CHANNELS,
            "schedule": LAST_NIGHT_STATS_SCHEDULE,
        }
    }
}
