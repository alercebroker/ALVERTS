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
KAFKA_STREAMS_LAG_REPORT = [
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

KAFKA_STREAMS_DETECTIONS_REPORT = [
    {
        "topic": f"ztf_{date}_programid1_aux",
        "bootstrap_servers": "kafka1.alerce.online:9092,kafka2.alerce.online:9092,kafka3.alerce.online:9092",
        "group_id": "report",
    },
    {
        "topic": f"ztf_{date}_programid1_aux",
        "bootstrap_servers": "10.0.2.14:9092,10.0.2.181:9092,10.0.2.62:9092",
        "group_id": "report",
    },
]

KAFKA_STREAMS = {
    "lag_report": KAFKA_STREAMS_LAG_REPORT,
    "detections_report": KAFKA_STREAMS_DETECTIONS_REPORT,
}

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


DATABASE_CONFIG = [
    {
        "table_identifiers": ["oid", "candid"],
        "db_url": f"postgresql://{USER_PROD}:{PASSWORD_PROD}@{HOST_PROD}:{PORT_PROD}/{DATABASE_PROD}",
        "table_name": "detections",
    },
    {
        "table_identifiers": ["oid", "candid"],
        "db_url": f"postgresql://{USER_STAGE}:{PASSWORD_STAGE}@{HOST_STAGE}:{PORT_STAGE}/{DATABASE_STAGE}",
        "table_name": "detections",
    },
]

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
            "channels": ["chikigang"],
            "schedule": ["09:00", "10:00", "11:00", "12:00", "09:46"],
        },
    }
}
