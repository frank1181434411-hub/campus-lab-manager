from app.db import fetch_all,fetch_one,transaction


def submit_repair(submitter_user_id,room_id,seat_no,description):
    with transaction() as connection:
        with connection.cursor() as cursor:
            # 机位故障状态由 trg_repair_lock_seat 自动维护。
            cursor.execute(
                """
                INSERT INTO repair(submitter_user_id,handler_user_id,room_id,seat_no,report_time,fault_description,repair_status)
                VALUES(%s,NULL,%s,%s,NOW(),%s,'pending')
                """,(submitter_user_id,room_id,seat_no,description),)


def get_user_repairs(user_id):
    return fetch_all(
        """
        SELECT repair_id,room_id,seat_no,report_time,fault_description,repair_status,submitter_username,handler_username
        FROM v_repair_detail
        WHERE submitter_username=(
            SELECT username FROM user_account WHERE user_id=%s
        )
        ORDER BY report_time DESC
        """,(user_id,),)


def get_all_repairs(status=None,room_id=None,submitter_user_id=None):
    sql="""
        SELECT rp.repair_id,rp.submitter_user_id,rp.handler_user_id,rp.room_id,rp.seat_no,rp.report_time,rp.fault_description,rp.repair_status,submitter.username AS submitter_username,handler.username AS handler_username
        FROM repair rp
        JOIN user_account submitter ON rp.submitter_user_id=submitter.user_id
        LEFT JOIN user_account handler ON rp.handler_user_id=handler.user_id
        WHERE 1=1
    """
    params=[]
    if status:
        sql+=" AND rp.repair_status=%s"
        params.append(status)
    if room_id:
        sql+=" AND rp.room_id=%s"
        params.append(room_id)
    if submitter_user_id:
        sql+=" AND rp.submitter_user_id=%s"
        params.append(submitter_user_id)
    sql+=" ORDER BY rp.report_time DESC"
    return fetch_all(sql,tuple(params))


def get_repair_detail(repair_id):
    return fetch_one(
        """
        SELECT rp.repair_id,rp.submitter_user_id,rp.handler_user_id,rp.room_id,rp.seat_no,rp.report_time,rp.fault_description,rp.repair_status,submitter.username AS submitter_username,handler.username AS handler_username
        FROM repair rp
        JOIN user_account submitter ON rp.submitter_user_id=submitter.user_id
        LEFT JOIN user_account handler ON rp.handler_user_id=handler.user_id
        WHERE rp.repair_id=%s
        """,(repair_id,),)


def assign_repair(repair_id,handler_user_id):
    with transaction() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE repair
                SET handler_user_id=%s,repair_status='processing'
                WHERE repair_id=%s
                """,(handler_user_id,repair_id),)


def update_repair_status(repair_id,handler_user_id,status):
    with transaction() as connection:
        with connection.cursor() as cursor:
            # 维修完成后的机位恢复由 trg_repair_release_seat 自动维护。
            cursor.execute(
                """
                UPDATE repair
                SET handler_user_id=%s,repair_status=%s
                WHERE repair_id=%s
                """,(handler_user_id,status,repair_id),)
