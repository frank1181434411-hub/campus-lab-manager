from contextlib import contextmanager

import pymysql
from pymysql import MySQLError
from pymysql.cursors import DictCursor

from app import config


class DatabaseError(Exception):
    """面向页面展示的数据库异常。"""


def translate_db_error(error):
    message=str(error)
    mappings={
        "Student user_id must reference a student account.":"用户账号角色必须是学生。","Teacher user_id must reference a teacher account.":"用户账号角色必须是教师。","Admin user_id must reference an admin account.":"用户账号角色必须是管理员。","Schedule room must be open.":"排课机房必须处于开放状态。","Room is not open.":"机房当前未开放。","Seat is not available.":"机位当前不可用。","Seat already has an active use log.":"该机位已有未结束的上机记录。","Class use log room must match schedule room.":"课堂上机机房必须与排课机房一致。","Student class must match schedule class.":"学生班级必须与排课班级一致。","Repair submitter must be student or teacher.":"报修提交人必须是学生或教师。","Repair handler must be admin.":"报修处理人必须是管理员。","Duplicate entry":"数据重复，请检查账号、编号或排课时间是否冲突。","Cannot delete or update a parent row":"该数据已有业务记录引用，不能删除。","foreign key constraint fails":"关联数据不存在或已被业务记录引用。",}
    for key,value in mappings.items():
        if key in message:
            return value
    return "数据库操作失败："+message


def get_connection():
    return pymysql.connect(
        host=config.DB_HOST,port=config.DB_PORT,user=config.DB_USER,password=config.DB_PASSWORD,database=config.DB_NAME,charset="utf8mb4",cursorclass=DictCursor,autocommit=False,)


def fetch_one(sql,params=None):
    connection=get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql,params or ())
            return cursor.fetchone()
    except MySQLError as error:
        raise DatabaseError(translate_db_error(error)) from error
    finally:
        connection.close()


def fetch_all(sql,params=None):
    connection=get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql,params or ())
            return cursor.fetchall()
    except MySQLError as error:
        raise DatabaseError(translate_db_error(error)) from error
    finally:
        connection.close()


def execute(sql,params=None):
    connection=get_connection()
    try:
        with connection.cursor() as cursor:
            affected=cursor.execute(sql,params or ())
            last_id=cursor.lastrowid
        connection.commit()
        return {"affected":affected,"last_id":last_id}
    except MySQLError as error:
        connection.rollback()
        raise DatabaseError(translate_db_error(error)) from error
    finally:
        connection.close()


def execute_many(sql,params_list):
    connection=get_connection()
    try:
        with connection.cursor() as cursor:
            affected=cursor.executemany(sql,params_list)
        connection.commit()
        return affected
    except MySQLError as error:
        connection.rollback()
        raise DatabaseError(translate_db_error(error)) from error
    finally:
        connection.close()


@contextmanager
def transaction():
    connection=get_connection()
    try:
        yield connection
        connection.commit()
    except MySQLError as error:
        connection.rollback()
        raise DatabaseError(translate_db_error(error)) from error
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
