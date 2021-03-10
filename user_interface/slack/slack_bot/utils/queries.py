from astropy.time import Time
from datetime import datetime
from db_plugins.db.sql import models
from db_plugins.db.sql import SQLConnection
from sqlalchemy.sql import func
import tzlocal


def get_stamp_classifier_inference(db: SQLConnection) -> str:
    last_day = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    last_mjd = int(Time(last_day).mjd)
    query = (
        db.query(models.Probability.class_name, func.count(models.Probability.oid))
        .join(models.Object)
        .group_by(models.Probability.class_name)
        .filter(models.Probability.ranking == 1)
        .filter(models.Probability.classifier_name == "stamp_classifier")
        .filter(models.Object.firstmjd >= last_mjd)
    )
    result = query.all()
    res = ""
    for r in result:
        res += f"\t\t\t - {r[0]:<8}: {r[1]:>7}\n"
    return res


def get_last_night_objects(db: SQLConnection) -> str:
    last_day = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    last_mjd = int(Time(last_day).mjd)
    tz = tzlocal.get_localzone()
    objects_observed = db.query(models.Object.oid).filter(
        models.Object.lastmjd >= last_mjd
    )
    observed = objects_observed.count()
    today = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S %z")
    if observed == 0:
        res = f""":astronaut: :page_facing_up: ALeRCE's report of today ({today}):
        :red_circle: No alerts today
        """
    else:
        new_objects = db.query(models.Object.oid).filter(
            models.Object.firstmjd >= last_mjd
        )
        new_objects = new_objects.count()
        stamp_classifier_inference = get_stamp_classifier_inference(db)
        res = f""":astronaut:  :page_facing_up: ALeRCE's report of today ({today}):
        • Objects observed last night:        {observed:>7} :night_with_stars:
        • New objects observed last night: {new_objects:>7} :full_moon_with_face:
        • Stamp classifier distribution: \n {stamp_classifier_inference}"""
    return res
