import os

from dotenv import load_dotenv


load_dotenv()


def _get_bool(name,default):
    value=os.getenv(name)
    if value is None:
        return default
    return value.lower() in ("1","true","yes","on")


def _get_int(name,default):
    value=os.getenv(name)
    if value is None or value=="":
        return default
    return int(value)


FLASK_SECRET_KEY=os.getenv("FLASK_SECRET_KEY","dev-secret-change-me")
DB_HOST=os.getenv("DB_HOST","127.0.0.1")
DB_PORT=_get_int("DB_PORT",3306)
DB_USER=os.getenv("DB_USER","root")
DB_PASSWORD=os.getenv("DB_PASSWORD","")
DB_NAME=os.getenv("DB_NAME","campus_lab_manager")
FLASK_HOST=os.getenv("FLASK_HOST","127.0.0.1")
FLASK_PORT=_get_int("FLASK_PORT",5000)
FLASK_DEBUG=_get_bool("FLASK_DEBUG",True)

ATTENDANCE_LATE_MINUTES=_get_int("ATTENDANCE_LATE_MINUTES",10)
ATTENDANCE_EARLY_LEAVE_MINUTES=_get_int("ATTENDANCE_EARLY_LEAVE_MINUTES",10)

# 与 sample_data.sql 中的 class_period 保持一致。
CLASS_PERIODS={
    "1-2":("08:00","09:40"),"3-4":("10:00","11:40"),"5-6":("14:00","15:40"),"7-8":("16:00","17:40"),}
