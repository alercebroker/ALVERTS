import os
import datetime

STAGE = os.getenv("BOT_STAGE", "develop")


# SLACK API SECTION
SLACK_CREDENTIALS = {
    "SLACK_BOT_TOKEN": os.getenv("SLACK_BOT_TOKEN", ""),
    "SLACK_SIGNATURE": os.getenv("SLACK_SIGNATURE"),
}

PROFILE = False


# KAFKA TOPICS SECTION
yesterday = datetime.datetime.today() - datetime.timedelta(1)
date = yesterday.strftime("%Y%m%d")
KAFKA_STREAMS = [
    {
        "topic": f"ztf_{date}_programid1_aux",
        "bootstrap_servers": "kafka1.alerce.online:9092,kafka2.alerce.online:9092,kafka3.alerce.online:9092",
        "group_id": "ALeRCE_v4_20200330_v1",
    },
    {
        "topic": f"ztf_{date}_programid1_aux",
        "bootstrap_servers": "kafka1.alerce.online:9092,kafka2.alerce.online:9092,kafka3.alerce.online:9092",
        "group_id": "ALERCE_stamp_classifier_v2_XXX",
    },
    {
        "topic": "xmatch",
        "bootstrap_servers": "10.0.2.14:9092,10.0.2.181:9092,10.0.2.62:9092",
        "group_id": "correction_consumer",
    },
    {
        "topic": "correction",
        "bootstrap_servers": "10.0.2.14:9092,10.0.2.181:9092,10.0.2.62:9092",
        "group_id": "feature_consumer",
    },
    {
        "topic": "feature",
        "bootstrap_servers": "10.0.2.14:9092,10.0.2.181:9092,10.0.2.62:9092",
        "group_id": "lc_classifier_consumer",
    },
    {
        "topic": f"ztf_{date}_programid1_aux",
        "bootstrap_servers": "10.0.2.14:9092,10.0.2.181:9092,10.0.2.62:9092",
        "group_id": "xmatch_consumer",
    },
    {
        "topic": f"ztf_{date}_programid1_aux",
        "bootstrap_servers": "10.0.2.14:9092,10.0.2.181:9092,10.0.2.62:9092",
        "group_id": "early_consumer",
    },
]

# DATABASE SECTION
HOST = os.getenv("DB_HOST", "localhost")
DATABASE = os.getenv("DB_DATABASE", "local")
USER = os.getenv("DB_USER", "user")
PASSWORD = os.getenv("DB_PASSWORD", "pass")
PORT = os.getenv("DB_PORT", 5432)
SQLALCHEMY_DATABASE_URL = f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}"

DATABASE = {"SQL": {"SQLALCHEMY_DATABASE_URL": SQLALCHEMY_DATABASE_URL}}

# SLACK SCHEDULE SECTION
if STAGE == "production":
    LAST_NIGHT_STATS_CHANNELS = ["chikigang", "recentsupernova"]
    LAST_NIGHT_STATS_SCHEDULE = ["10:00", "11:00", "12:00"]

elif STAGE == "develop":
    LAST_NIGHT_STATS_CHANNELS = ["blog-javier"]
    LAST_NIGHT_STATS_SCHEDULE = ["17:15", "17:16"]
else:
    LAST_NIGHT_STATS_CHANNELS = ["chikigang"]
    LAST_NIGHT_STATS_SCHEDULE = ["10:00", "11:00", "12:00"]

SLACK_SCHEDULE_CONFIG = {
    "every_day": {
        "last_night_stats": {
            "channels": LAST_NIGHT_STATS_CHANNELS,
            "schedule": LAST_NIGHT_STATS_SCHEDULE,
        },
        "stream_lag_report": {
            "channels": "chikigang",
            "schedule": ["09:00", "10:00", "11:00", "12:00"],
        },
    }
}


ALERT_SYSTEM_CONFIG = {"streams": KAFKA_STREAMS, "slack": SLACK_CREDENTIALS}
