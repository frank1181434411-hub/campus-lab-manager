from app.db import DatabaseError,fetch_all,fetch_one,transaction


def get_all_schedules():
    return fetch_all(
        """
        SELECT sc.schedule_id,sc.semester,sc.week_no,sc.weekday,sc.class_period,sc.teacher_id,t.teacher_name,sc.class_id,ci.class_name,sc.course_id,c.course_name,sc.room_id,r.room_location
        FROM schedule sc
        JOIN teacher t ON sc.teacher_id=t.teacher_id
        JOIN class_info ci ON sc.class_id=ci.class_id
        JOIN course c ON sc.course_id=c.course_id
        JOIN room r ON sc.room_id=r.room_id
        ORDER BY sc.semester,sc.weekday,sc.class_period,sc.schedule_id
        """
    )


def get_teacher_schedules(teacher_id):
    return fetch_all(
        """
        SELECT *
        FROM v_teacher_schedule
        WHERE teacher_id=%s
        ORDER BY semester,weekday,class_period
        """,(teacher_id,),)


def get_student_schedules(student_id):
    return fetch_all(
        """
        SELECT sc.schedule_id,sc.semester,sc.week_no,sc.weekday,sc.class_period,c.course_name,t.teacher_name,r.room_id,r.room_location
        FROM student s
        JOIN schedule sc ON s.class_id=sc.class_id
        JOIN course c ON sc.course_id=c.course_id
        JOIN teacher t ON sc.teacher_id=t.teacher_id
        JOIN room r ON sc.room_id=r.room_id
        WHERE s.student_id=%s
        ORDER BY sc.semester,sc.weekday,sc.class_period
        """,(student_id,),)


def get_schedule_detail(schedule_id):
    return fetch_one(
        """
        SELECT sc.schedule_id,sc.semester,sc.week_no,sc.weekday,sc.class_period,sc.teacher_id,t.teacher_name,sc.class_id,ci.class_name,sc.course_id,c.course_name,sc.room_id,r.room_location
        FROM schedule sc
        JOIN teacher t ON sc.teacher_id=t.teacher_id
        JOIN class_info ci ON sc.class_id=ci.class_id
        JOIN course c ON sc.course_id=c.course_id
        JOIN room r ON sc.room_id=r.room_id
        WHERE sc.schedule_id=%s
        """,(schedule_id,),)


def _assert_exists(table,column,value,label):
    row=fetch_one(f"SELECT {column} FROM {table} WHERE {column}=%s",(value,))
    if not row:
        raise DatabaseError(label+"不存在。")


def create_schedule(semester,week_no,weekday,class_period,teacher_id,class_id,course_id,room_id):
    _assert_exists("teacher","teacher_id",teacher_id,"教师")
    _assert_exists("class_info","class_id",class_id,"班级")
    _assert_exists("course","course_id",course_id,"课程")
    room=fetch_one("SELECT room_id,open_status FROM room WHERE room_id=%s",(room_id,))
    if not room:
        raise DatabaseError("机房不存在。")
    if room["open_status"]!="open":
        raise DatabaseError("机房不是开放状态，不能排课。")
    with transaction() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO schedule(semester,week_no,weekday,class_period,teacher_id,class_id,course_id,room_id)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
                """,(semester,week_no,weekday,class_period,teacher_id,class_id,course_id,room_id),)


def update_schedule(schedule_id,semester,week_no,weekday,class_period,teacher_id,class_id,course_id,room_id):
    _assert_exists("teacher","teacher_id",teacher_id,"教师")
    _assert_exists("class_info","class_id",class_id,"班级")
    _assert_exists("course","course_id",course_id,"课程")
    _assert_exists("room","room_id",room_id,"机房")
    with transaction() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE schedule
                SET semester=%s,week_no=%s,weekday=%s,class_period=%s,teacher_id=%s,class_id=%s,course_id=%s,room_id=%s
                WHERE schedule_id=%s
                """,(semester,week_no,weekday,class_period,teacher_id,class_id,course_id,room_id,schedule_id),)


def delete_schedule(schedule_id):
    with transaction() as connection:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM schedule WHERE schedule_id=%s",(schedule_id,))


def get_current_or_available_schedules(student_id=None,room_id=None):
    sql="""
        SELECT sc.schedule_id,sc.semester,sc.week_no,sc.weekday,sc.class_period,c.course_name,ci.class_name,t.teacher_name,r.room_id,r.room_location
        FROM schedule sc
        JOIN course c ON sc.course_id=c.course_id
        JOIN class_info ci ON sc.class_id=ci.class_id
        JOIN teacher t ON sc.teacher_id=t.teacher_id
        JOIN room r ON sc.room_id=r.room_id
    """
    params=[]
    where=[]
    if student_id:
        sql+=" JOIN student s ON s.class_id=sc.class_id"
        where.append("s.student_id=%s")
        params.append(student_id)
    if room_id:
        where.append("sc.room_id=%s")
        params.append(room_id)
    if where:
        sql+=" WHERE "+" AND ".join(where)
    sql+=" ORDER BY sc.weekday,sc.class_period,sc.schedule_id"
    return fetch_all(sql,tuple(params))


def get_courses():
    return fetch_all("SELECT course_id,course_name FROM course ORDER BY course_id")
