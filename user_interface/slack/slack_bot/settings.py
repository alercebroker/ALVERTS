import os
import datetime

STAGE = os.getenv("BOT_STAGE", "develop")

# SLACK API SECTION
SLACK_CREDENTIALS = {
    "SLACK_BOT_TOKEN": os.getenv("SLACK_BOT_TOKEN", ""),
    "SLACK_SIGNATURE": os.getenv("SLACK_SIGNATURE"),
}
PROFILE = False

# DATABASE SECTION
HOST_PROD = os.getenv("DB_HOST_PROD", "localhost")
DATABASE_PROD = os.getenv("DB_DATABASE_PROD", "local")
USER_PROD = os.getenv("DB_USER_PROD", "user")
PASSWORD_PROD = os.getenv("DB_PASSWORD_PROD", "pass")
PORT_PROD = os.getenv("DB_PORT_PROD", 5432)

HOST_STAGE = os.getenv("DB_HOST_STAGE", "localhost")
DATABASE_STAGE = os.getenv("DB_DATABASE_STAGE", "local")
USER_STAGE = os.getenv("DB_USER_STAGE", "user")
PASSWORD_STAGE = os.getenv("DB_PASSWORD_STAGE", "pass")
PORT_STAGE = os.getenv("DB_PORT_STAGE", 5432)

OLD_DATABASE_CONFIG = {
    "SQL": {
        "ENGINE": "postgresql",
        "HOST": HOST_STAGE,
        "USER": USER_STAGE,
        "PORT": PORT_STAGE,
        "PASSWORD": PASSWORD_STAGE,
        "DATABASE": DATABASE_STAGE,
        "SQLALCHEMY_DATABASE_URL": f"postgresql://{USER_STAGE}:{PASSWORD_STAGE}@{HOST_STAGE}:{PORT_STAGE}/{DATABASE_STAGE}",
    },
}

DATABASE_CONFIG = [
    {
        "table_identifiers": ["objectId", "candid"],
        "db_url": f"postgresql://{USER_PROD}:{PASSWORD_PROD}@{HOST_PROD}:{PORT_PROD}/{DATABASE_PROD}",
        "table_name": "detections",
    },
    {
        "table_identifiers": ["objectId", "candid"],
        "db_url": f"postgresql://{USER_STAGE}:{PASSWORD_STAGE}@{HOST_STAGE}:{PORT_STAGE}/{DATABASE_STAGE}",
        "table_name": "detections",
    },
]

# SLACK SCHEDULE SECTION
if STAGE == "production":
    LAST_NIGHT_STATS_CHANNELS = ["chikigang", "recentsupernova"]
    LAST_NIGHT_STATS_SCHEDULE = ["10:00", "11:00", "12:00"]

elif STAGE == "develop":
    LAST_NIGHT_STATS_CHANNELS = ["test-bots"]
    LAST_NIGHT_STATS_SCHEDULE = ["10:00", "11:00", "12:00"]

SLACK_SCHEDULE_CONFIG = {
    "every_day": {
        "last_night_stats": {
            "channels": LAST_NIGHT_STATS_CHANNELS,
            "schedule": LAST_NIGHT_STATS_SCHEDULE,
        },
        "stream_lag_report": {
            "channels": LAST_NIGHT_STATS_CHANNELS,
            "schedule": LAST_NIGHT_STATS_SCHEDULE,
        },
        "detections_report": {
            "channels": LAST_NIGHT_STATS_CHANNELS,
            "schedule": LAST_NIGHT_STATS_SCHEDULE,
        },
    }
}
