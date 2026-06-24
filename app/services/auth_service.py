from werkzeug.security import check_password_hash,generate_password_hash

from app.db import DatabaseError,fetch_all,fetch_one,transaction


def _is_hash(password):
    return password.startswith("scrypt:") or password.startswith("pbkdf2:")


def authenticate_user(username,password):
    user=fetch_one(
        """
        SELECT user_id,username,password,role,status,phone
        FROM user_account
        WHERE username=%s
        """,(username,),)
    if not user:
        return None
    if user["status"]!="active":
        raise DatabaseError("账号不是 active 状态，不能登录。")
    stored=user["password"]
    ok=check_password_hash(stored,password) if _is_hash(stored) else stored==password
    if not ok:
        return None
    detail=get_current_user_detail(user["user_id"],user["role"])
    user["detail"]=detail
    user["display_name"]=detail.get("display_name") if detail else user["username"]
    return user


def get_current_user_detail(user_id,role):
    if role=="student":
        row=fetch_one(
            """
            SELECT s.student_id,s.student_name AS display_name,s.gender,s.grade,s.class_id,ci.class_name
            FROM student s
            JOIN class_info ci ON s.class_id=ci.class_id
            WHERE s.user_id=%s
            """,(user_id,),)
    elif role=="teacher":
        row=fetch_one(
            """
            SELECT teacher_id,teacher_name AS display_name,title
            FROM teacher
            WHERE user_id=%s
            """,(user_id,),)
    elif role=="admin":
        row=fetch_one(
            """
            SELECT admin_id,admin_name AS display_name
            FROM admin
            WHERE user_id=%s
            """,(user_id,),)
    else:
        row=None
    return row or {}


def create_user_account(username,password,role,phone,profile):
    hashed=generate_password_hash(password)
    # 用户账号和角色扩展必须处于同一事务，触发器负责最终角色约束。
    with transaction() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO user_account(username,password,role,status,phone)
                VALUES(%s,%s,%s,'active',%s)
                """,(username,hashed,role,phone),)
            user_id=cursor.lastrowid
            if role=="student":
                cursor.execute(
                    """
                    INSERT INTO student(student_id,user_id,student_name,gender,grade,class_id)
                    VALUES(%s,%s,%s,%s,%s,%s)
                    """,(
                        profile["student_id"],user_id,profile["student_name"],profile.get("gender"),profile.get("grade"),profile["class_id"],),)
            elif role=="teacher":
                cursor.execute(
                    """
                    INSERT INTO teacher(teacher_id,user_id,teacher_name,title)
                    VALUES(%s,%s,%s,%s)
                    """,(
                        profile["teacher_id"],user_id,profile["teacher_name"],profile.get("title"),),)
            elif role=="admin":
                cursor.execute(
                    """
                    INSERT INTO admin(admin_id,user_id,admin_name)
                    VALUES(%s,%s,%s)
                    """,(profile["admin_id"],user_id,profile["admin_name"]),)
            else:
                raise DatabaseError("不支持的用户角色。")
    return user_id


def update_user_status(user_id,status):
    with transaction() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE user_account SET status=%s WHERE user_id=%s",(status,user_id),)


def change_password(user_id,new_password):
    hashed=generate_password_hash(new_password)
    with transaction() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE user_account SET password=%s WHERE user_id=%s",(hashed,user_id),)


def get_all_users(role=None,status=None):
    sql="""
        SELECT user_id,username,role,status,phone
        FROM user_account
        WHERE 1=1
    """
    params=[]
    if role:
        sql+=" AND role=%s"
        params.append(role)
    if status:
        sql+=" AND status=%s"
        params.append(status)
    sql+=" ORDER BY user_id"
    return fetch_all(sql,tuple(params))


def get_counts():
    return fetch_one(
        """
        SELECT
            (SELECT COUNT(*) FROM user_account) AS user_count,(SELECT COUNT(*) FROM student) AS student_count,(SELECT COUNT(*) FROM teacher) AS teacher_count,(SELECT COUNT(*) FROM room) AS room_count,(SELECT COUNT(*) FROM seat WHERE seat_status IN ('self_study','class_in_use')) AS occupied_seat_count,(SELECT COUNT(*) FROM seat WHERE seat_status='fault') AS fault_seat_count,(SELECT COUNT(*) FROM repair WHERE repair_status IN ('pending','processing')) AS pending_repair_count,(SELECT COUNT(*) FROM schedule) AS schedule_count
        """
    )


def get_students():
    return fetch_all(
        """
        SELECT s.student_id,s.student_name,s.gender,s.grade,ci.class_id,ci.class_name,ci.major
        FROM student s
        JOIN class_info ci ON s.class_id=ci.class_id
        ORDER BY ci.class_id,s.student_id
        """
    )


def get_teachers():
    return fetch_all(
        """
        SELECT teacher_id,teacher_name,title
        FROM teacher
        ORDER BY teacher_id
        """
    )


def get_classes():
    return fetch_all(
        """
        SELECT class_id,class_name,major,total_number
        FROM class_info
        ORDER BY class_id
        """
    )
