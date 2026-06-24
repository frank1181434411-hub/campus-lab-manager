from datetime import datetime,timedelta

from app import config
from app.db import DatabaseError,fetch_all,fetch_one,transaction


def _now():
    return datetime.now().replace(microsecond=0)


def _attendance_for_start(schedule,start_time):
    period=config.CLASS_PERIODS.get(schedule["class_period"])
    if not period:
        return "normal"
    start_text=period[0]
    class_start=datetime.combine(start_time.date(),datetime.strptime(start_text,"%H:%M").time())
    late_limit=class_start+timedelta(minutes=config.ATTENDANCE_LATE_MINUTES)
    return "normal" if start_time<=late_limit else "late"


def _early_leave_status(schedule,end_time):
    period=config.CLASS_PERIODS.get(schedule["class_period"])
    if not period:
        return None
    end_text=period[1]
    class_end=datetime.combine(end_time.date(),datetime.strptime(end_text,"%H:%M").time())
    early_limit=class_end-timedelta(minutes=config.ATTENDANCE_EARLY_LEAVE_MINUTES)
    return "early_leave" if end_time<early_limit else None


def get_active_use(student_id):
    return fetch_one(
        """
        SELECT ul.log_id,ul.student_id,ul.room_id,r.room_location,ul.seat_no,ul.schedule_id,ul.start_time,ul.use_type,ul.attendance_status
        FROM use_log ul
        JOIN room r ON ul.room_id=r.room_id
        WHERE ul.student_id=%s AND ul.end_time IS NULL
        ORDER BY ul.start_time DESC
        LIMIT 1
        """,(student_id,),)


def start_free_use(student_id,room_id,seat_no):
    if get_active_use(student_id):
        raise DatabaseError("你已经有未结束的上机记录，请先下机。")
    with transaction() as connection:
        with connection.cursor() as cursor:
            # 数据库触发器继续验证机房开放、机位空闲和状态联动。
            cursor.execute(
                """
                INSERT INTO use_log(student_id,room_id,seat_no,schedule_id,start_time,end_time,use_type,attendance_status)
                VALUES(%s,%s,%s,NULL,%s,NULL,'free','not_applicable')
                """,(student_id,room_id,seat_no,_now()),)


def start_class_use(student_id,room_id,seat_no,schedule_id):
    if get_active_use(student_id):
        raise DatabaseError("你已经有未结束的上机记录，请先下机。")
    schedule=fetch_one(
        """
        SELECT schedule_id,class_period
        FROM schedule
        WHERE schedule_id=%s
        """,(schedule_id,),)
    if not schedule:
        raise DatabaseError("排课不存在。")
    start_time=_now()
    attendance_status=_attendance_for_start(schedule,start_time)
    with transaction() as connection:
        with connection.cursor() as cursor:
            # 课堂上机由触发器最终校验班级、机房和机位。
            cursor.execute(
                """
                INSERT INTO use_log(student_id,room_id,seat_no,schedule_id,start_time,end_time,use_type,attendance_status)
                VALUES(%s,%s,%s,%s,%s,NULL,'class',%s)
                """,(student_id,room_id,seat_no,schedule_id,start_time,attendance_status),)


def finish_use(log_id,student_id):
    active=fetch_one(
        """
        SELECT ul.log_id,ul.schedule_id,ul.attendance_status,sc.class_period
        FROM use_log ul
        LEFT JOIN schedule sc ON ul.schedule_id=sc.schedule_id
        WHERE ul.log_id=%s AND ul.student_id=%s AND ul.end_time IS NULL
        """,(log_id,student_id),)
    if not active:
        raise DatabaseError("没有找到属于你的未结束上机记录。")
    end_time=_now()
    status=active["attendance_status"]
    if active["schedule_id"]:
        early=_early_leave_status(active,end_time)
        if early:
            status=early
    with transaction() as connection:
        with connection.cursor() as cursor:
            # 下机只更新当前学生自己的未结束记录，释放机位由触发器完成。
            cursor.execute(
                """
                UPDATE use_log
                SET end_time=%s,attendance_status=%s
                WHERE log_id=%s AND student_id=%s AND end_time IS NULL
                """,(end_time,status,log_id,student_id),)


def get_student_history(student_id):
    return fetch_all(
        """
        SELECT *
        FROM v_student_use_history
        WHERE student_id=%s
        ORDER BY start_time DESC
        """,(student_id,),)


def get_student_attendance(student_id):
    return fetch_all(
        """
        SELECT ul.log_id,ul.schedule_id,c.course_name,sc.semester,sc.week_no,sc.weekday,sc.class_period,r.room_id,r.room_location,ul.start_time,ul.end_time,ul.attendance_status
        FROM use_log ul
        JOIN schedule sc ON ul.schedule_id=sc.schedule_id
        JOIN course c ON sc.course_id=c.course_id
        JOIN room r ON sc.room_id=r.room_id
        WHERE ul.student_id=%s AND ul.use_type='class'
        ORDER BY ul.start_time DESC
        """,(student_id,),)


def get_schedule_attendance(schedule_id):
    return fetch_all(
        """
        SELECT s.student_id,s.student_name,ul.log_id,ul.start_time,ul.end_time,COALESCE(ul.attendance_status,'absent') AS attendance_status
        FROM schedule sc
        JOIN student s ON sc.class_id=s.class_id
        LEFT JOIN use_log ul
            ON ul.schedule_id=sc.schedule_id
           AND ul.student_id=s.student_id
        WHERE sc.schedule_id=%s
        ORDER BY s.student_id
        """,(schedule_id,),)


def get_recent_logs(limit=20):
    return fetch_all(
        """
        SELECT ul.log_id,s.student_name,ul.room_id,ul.seat_no,ul.start_time,ul.end_time,ul.use_type,ul.attendance_status
        FROM use_log ul
        JOIN student s ON ul.student_id=s.student_id
        ORDER BY ul.start_time DESC
        LIMIT %s
        """,(limit,),)


def get_room_usage_statistics(room_id=None,start_time=None,end_time=None):
    sql="""
        SELECT r.room_id,r.room_location,COUNT(ul.log_id) AS use_count,COALESCE(SUM(TIMESTAMPDIFF(MINUTE,ul.start_time,COALESCE(ul.end_time,NOW()))),0) AS used_minutes
        FROM room r
        LEFT JOIN use_log ul ON r.room_id=ul.room_id
    """
    params=[]
    where=[]
    if room_id:
        where.append("r.room_id=%s")
        params.append(room_id)
    if start_time:
        where.append("(ul.start_time IS NULL OR ul.start_time>=%s)")
        params.append(start_time)
    if end_time:
        where.append("(ul.start_time IS NULL OR ul.start_time<=%s)")
        params.append(end_time)
    if where:
        sql+=" WHERE "+" AND ".join(where)
    sql+=" GROUP BY r.room_id,r.room_location ORDER BY r.room_id"
    return fetch_all(sql,tuple(params))
