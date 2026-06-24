from app.db import fetch_all,fetch_one,transaction


def get_all_rooms():
    return fetch_all(
        """
        SELECT room_id,room_location,total_seats,open_status
        FROM room
        ORDER BY room_id
        """
    )


def get_room_detail(room_id):
    return fetch_one(
        """
        SELECT room_id,room_location,total_seats,open_status
        FROM room
        WHERE room_id=%s
        """,(room_id,),)


def get_room_seats(room_id):
    return fetch_all(
        """
        SELECT room_id,room_location,open_status,seat_no,ip_address,machine_config,seat_status
        FROM v_room_seat_status
        WHERE room_id=%s
        ORDER BY seat_no
        """,(room_id,),)


def get_available_seats(room_id):
    return fetch_all(
        """
        SELECT room_id,seat_no,ip_address,machine_config
        FROM v_room_seat_status
        WHERE room_id=%s
          AND open_status='open'
          AND seat_status='free'
        ORDER BY seat_no
        """,(room_id,),)


def get_room_status_summary():
    return fetch_all(
        """
        SELECT
            r.room_id,r.room_location,r.open_status,r.total_seats,COUNT(se.seat_no) AS actual_seats,SUM(CASE WHEN se.seat_status='free' THEN 1 ELSE 0 END) AS free_count,SUM(CASE WHEN se.seat_status='self_study' THEN 1 ELSE 0 END) AS self_study_count,SUM(CASE WHEN se.seat_status='class_in_use' THEN 1 ELSE 0 END) AS class_in_use_count,SUM(CASE WHEN se.seat_status='fault' THEN 1 ELSE 0 END) AS fault_count
        FROM room r
        LEFT JOIN seat se ON r.room_id=se.room_id
        GROUP BY r.room_id,r.room_location,r.open_status,r.total_seats
        ORDER BY r.room_id
        """
    )


def create_room(room_id,room_location,total_seats,open_status):
    with transaction() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO room(room_id,room_location,total_seats,open_status)
                VALUES(%s,%s,%s,%s)
                """,(room_id,room_location,total_seats,open_status),)


def update_room(room_id,room_location,total_seats,open_status):
    with transaction() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE room
                SET room_location=%s,total_seats=%s,open_status=%s
                WHERE room_id=%s
                """,(room_location,total_seats,open_status,room_id),)


def create_seat(room_id,seat_no,ip_address,machine_config,seat_status):
    with transaction() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO seat(room_id,seat_no,ip_address,machine_config,seat_status)
                VALUES(%s,%s,%s,%s,%s)
                """,(room_id,seat_no,ip_address,machine_config,seat_status),)


def update_seat(room_id,seat_no,ip_address,machine_config,seat_status):
    with transaction() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE seat
                SET ip_address=%s,machine_config=%s,seat_status=%s
                WHERE room_id=%s AND seat_no=%s
                """,(ip_address,machine_config,seat_status,room_id,seat_no),)


def delete_room(room_id):
    with transaction() as connection:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM room WHERE room_id=%s",(room_id,))


def delete_seat(room_id,seat_no):
    with transaction() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM seat WHERE room_id=%s AND seat_no=%s",(room_id,seat_no),)
