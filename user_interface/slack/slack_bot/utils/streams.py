import datetime


def get_kafka_streams_lag_report():
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
    return KAFKA_STREAMS_LAG_REPORT


def get_kafka_streams_detections_report():
    yesterday = datetime.datetime.today() - datetime.timedelta(1)
    date = yesterday.strftime("%Y%m%d%H%M%S")
    KAFKA_STREAMS_DETECTIONS_REPORT = [
        {
            "topic": f"ztf_{date}_programid1_aux",
            "bootstrap_servers": "kafka1.alerce.online:9092,kafka2.alerce.online:9092,kafka3.alerce.online:9092",
            "group_id": f"report_{date}",
            "batch_size": 500,
        },
        {
            "topic": f"ztf_{date}_programid1_aux",
            "bootstrap_servers": "10.0.2.14:9092,10.0.2.181:9092,10.0.2.62:9092",
            "group_id": f"report_{date}",
            "batch_size": 500,
        },
    ]
    return KAFKA_STREAMS_DETECTIONS_REPORT
