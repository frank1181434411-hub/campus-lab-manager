-- Campus Lab Manager database schema
-- Target DBMS: MySQL 8.0+

CREATE DATABASE IF NOT EXISTS campus_lab_manager
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE campus_lab_manager;

SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS=0;

DROP VIEW IF EXISTS v_repair_detail;

DROP VIEW IF EXISTS v_room_seat_status;

DROP VIEW IF EXISTS v_class_attendance;

DROP VIEW IF EXISTS v_teacher_schedule;

DROP VIEW IF EXISTS v_student_use_history;

DROP TRIGGER IF EXISTS trg_student_check_user_role;

DROP TRIGGER IF EXISTS trg_teacher_check_user_role;

DROP TRIGGER IF EXISTS trg_admin_check_user_role;

DROP TRIGGER IF EXISTS trg_schedule_check_room;

DROP TRIGGER IF EXISTS trg_use_log_before_insert;

DROP TRIGGER IF EXISTS trg_use_log_occupy_seat;

DROP TRIGGER IF EXISTS trg_use_log_release_seat;

DROP TRIGGER IF EXISTS trg_repair_before_insert;

DROP TRIGGER IF EXISTS trg_repair_before_update;

DROP TRIGGER IF EXISTS trg_repair_lock_seat;

DROP TRIGGER IF EXISTS trg_repair_release_seat;

DROP TABLE IF EXISTS repair;

DROP TABLE IF EXISTS use_log;

DROP TABLE IF EXISTS schedule;

DROP TABLE IF EXISTS seat;

DROP TABLE IF EXISTS room;

DROP TABLE IF EXISTS course;

DROP TABLE IF EXISTS admin;

DROP TABLE IF EXISTS teacher;

DROP TABLE IF EXISTS student;

DROP TABLE IF EXISTS class_info;

DROP TABLE IF EXISTS user_account;

SET FOREIGN_KEY_CHECKS=1;

CREATE TABLE user_account (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    phone VARCHAR(20),
    CHECK (role IN ('student','teacher','admin')),
    CHECK (status IN ('active','disabled','locked'))
) ENGINE=InnoDB;

CREATE TABLE class_info (
    class_id VARCHAR(20) PRIMARY KEY,
    class_name VARCHAR(50) NOT NULL,
    major VARCHAR(50) NOT NULL,
    total_number INT NOT NULL DEFAULT 0,
    CHECK (total_number >=0)
) ENGINE=InnoDB;

CREATE TABLE student (
    student_id VARCHAR(20) PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    student_name VARCHAR(50) NOT NULL,
    gender VARCHAR(10),
    grade VARCHAR(20),
    class_id VARCHAR(20) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user_account(user_id),
    FOREIGN KEY (class_id) REFERENCES class_info(class_id)
) ENGINE=InnoDB;

CREATE TABLE teacher (
    teacher_id VARCHAR(20) PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    teacher_name VARCHAR(50) NOT NULL,
    title VARCHAR(50),
    FOREIGN KEY (user_id) REFERENCES user_account(user_id)
) ENGINE=InnoDB;

CREATE TABLE admin (
    admin_id VARCHAR(20) PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    admin_name VARCHAR(50) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user_account(user_id)
) ENGINE=InnoDB;

CREATE TABLE course (
    course_id VARCHAR(20) PRIMARY KEY,
    course_name VARCHAR(50) NOT NULL,
    total_hours INT NOT NULL,
    course_type VARCHAR(20),
    CHECK (total_hours > 0)
) ENGINE=InnoDB;

CREATE TABLE room (
    room_id VARCHAR(20) PRIMARY KEY,
    room_location VARCHAR(100) NOT NULL,
    total_seats INT NOT NULL,
    open_status VARCHAR(20) NOT NULL DEFAULT 'open',
    CHECK (total_seats >=0),
    CHECK (open_status IN ('open','closed','maintenance'))
) ENGINE=InnoDB;

CREATE TABLE seat (
    room_id VARCHAR(20) NOT NULL,
    seat_no VARCHAR(20) NOT NULL,
    ip_address VARCHAR(50) UNIQUE,
    machine_config VARCHAR(200),
    seat_status VARCHAR(20) NOT NULL DEFAULT 'free',
    PRIMARY KEY (room_id,seat_no),
    FOREIGN KEY (room_id) REFERENCES room(room_id),
    CHECK (seat_status IN ('free','self_study','class_in_use','fault'))
) ENGINE=InnoDB;

CREATE TABLE schedule (
    schedule_id INT PRIMARY KEY AUTO_INCREMENT,
    semester VARCHAR(20) NOT NULL,
    week_no VARCHAR(50) NOT NULL,
    weekday TINYINT NOT NULL,
    class_period VARCHAR(20) NOT NULL,
    teacher_id VARCHAR(20) NOT NULL,
    class_id VARCHAR(20) NOT NULL,
    course_id VARCHAR(20) NOT NULL,
    room_id VARCHAR(20) NOT NULL,
    FOREIGN KEY (teacher_id) REFERENCES teacher(teacher_id),
    FOREIGN KEY (class_id) REFERENCES class_info(class_id),
    FOREIGN KEY (course_id) REFERENCES course(course_id),
    FOREIGN KEY (room_id) REFERENCES room(room_id),
    UNIQUE (room_id,semester,week_no,weekday,class_period),
    CHECK (weekday BETWEEN 1 AND 7)
) ENGINE=InnoDB;

CREATE TABLE use_log (
    log_id INT PRIMARY KEY AUTO_INCREMENT,
    student_id VARCHAR(20) NOT NULL,
    room_id VARCHAR(20) NOT NULL,
    seat_no VARCHAR(20) NOT NULL,
    schedule_id INT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NULL,
    use_type VARCHAR(20) NOT NULL,
    attendance_status VARCHAR(20) NOT NULL DEFAULT 'not_applicable',
    FOREIGN KEY (student_id) REFERENCES student(student_id),
    FOREIGN KEY (room_id,seat_no) REFERENCES seat(room_id,seat_no),
    FOREIGN KEY (schedule_id) REFERENCES schedule(schedule_id),
    CHECK (use_type IN ('free','class')),
    CHECK (attendance_status IN ('normal','late','early_leave','absent','not_applicable')),
    CHECK (end_time IS NULL OR end_time >=start_time),
    CHECK ((use_type='free' AND schedule_id IS NULL) OR (use_type='class' AND schedule_id IS NOT NULL))
) ENGINE=InnoDB;

CREATE TABLE repair (
    repair_id INT PRIMARY KEY AUTO_INCREMENT,
    submitter_user_id INT NOT NULL,
    handler_user_id INT NULL,
    room_id VARCHAR(20) NOT NULL,
    seat_no VARCHAR(20) NOT NULL,
    report_time DATETIME NOT NULL,
    fault_description VARCHAR(500) NOT NULL,
    repair_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    FOREIGN KEY (submitter_user_id) REFERENCES user_account(user_id),
    FOREIGN KEY (handler_user_id) REFERENCES user_account(user_id),
    FOREIGN KEY (room_id,seat_no) REFERENCES seat(room_id,seat_no),
    CHECK (repair_status IN ('pending','processing','done'))
) ENGINE=InnoDB;

CREATE INDEX idx_student_class ON student(class_id);

CREATE INDEX idx_schedule_teacher ON schedule(teacher_id);

CREATE INDEX idx_schedule_class ON schedule(class_id);

CREATE INDEX idx_schedule_room_time
    ON schedule(room_id,
    semester,
    week_no,
    weekday,
    class_period);

CREATE INDEX idx_use_log_student_time ON use_log(student_id,
    start_time);

CREATE INDEX idx_use_log_seat_time ON use_log(room_id,
    seat_no,
    start_time);

CREATE INDEX idx_use_log_schedule ON use_log(schedule_id);

CREATE INDEX idx_repair_status ON repair(repair_status);

CREATE INDEX idx_repair_submitter ON repair(submitter_user_id);

CREATE INDEX idx_repair_handler ON repair(handler_user_id);

CREATE VIEW v_student_use_history AS
SELECT
    s.student_id,
    s.student_name,
    r.room_id,
    r.room_location,
    ul.seat_no,
    ul.start_time,
    ul.end_time,
    ul.use_type,
    ul.attendance_status
FROM use_log ul
JOIN student s
    ON ul.student_id=s.student_id
JOIN room r
    ON ul.room_id=r.room_id;

CREATE VIEW v_teacher_schedule AS
SELECT
    t.teacher_id,
    t.teacher_name,
    sc.schedule_id,
    c.course_name,
    ci.class_name,
    r.room_id,
    r.room_location,
    sc.semester,
    sc.week_no,
    sc.weekday,
    sc.class_period
FROM schedule sc
JOIN teacher t
    ON sc.teacher_id=t.teacher_id
JOIN course c
    ON sc.course_id=c.course_id
JOIN class_info ci
    ON sc.class_id=ci.class_id
JOIN room r
    ON sc.room_id=r.room_id;

CREATE VIEW v_class_attendance AS
SELECT
    sc.schedule_id,
    c.course_name,
    ci.class_name,
    t.teacher_name,
    s.student_id,
    s.student_name,
    ul.start_time,
    ul.end_time,
    ul.attendance_status
FROM schedule sc
JOIN course c
    ON sc.course_id=c.course_id
JOIN class_info ci
    ON sc.class_id=ci.class_id
JOIN teacher t
    ON sc.teacher_id=t.teacher_id
LEFT
JOIN use_log ul
    ON sc.schedule_id=ul.schedule_id
LEFT
JOIN student s
    ON ul.student_id=s.student_id;

CREATE VIEW v_room_seat_status AS
SELECT
    r.room_id,
    r.room_location,
    r.open_status,
    se.seat_no,
    se.ip_address,
    se.machine_config,
    se.seat_status
FROM room r
JOIN seat se
    ON r.room_id=se.room_id;

CREATE VIEW v_repair_detail AS
SELECT
    rp.repair_id,
    rp.room_id,
    rp.seat_no,
    rp.report_time,
    rp.fault_description,
    rp.repair_status,
    submitter.username AS submitter_username,
    submitter.role AS submitter_role,
    handler.username AS handler_username,
    handler.role AS handler_role
FROM repair rp
JOIN user_account submitter
    ON rp.submitter_user_id=submitter.user_id
LEFT
JOIN user_account handler
    ON rp.handler_user_id=handler.user_id;

DELIMITER //

CREATE TRIGGER trg_student_check_user_role
BEFORE INSERT ON student
FOR EACH ROW
BEGIN
    DECLARE account_role VARCHAR(20);

DECLARE role_count INT DEFAULT 0;

SELECT
    role INTO account_role
FROM user_account
WHERE user_id=NEW.user_id;

IF account_role <> 'student' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT='Student user_id must reference a student account.';

END IF;

SELECT
    COUNT(*) INTO role_count
FROM teacher
WHERE user_id=NEW.user_id;

IF role_count > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT='User account already has teacher role extension.';

END IF;

SELECT
    COUNT(*) INTO role_count
FROM admin
WHERE user_id=NEW.user_id;

IF role_count > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT='User account already has admin role extension.';

END IF;

END //

CREATE TRIGGER trg_teacher_check_user_role
BEFORE INSERT ON teacher
FOR EACH ROW
BEGIN
    DECLARE account_role VARCHAR(20);

DECLARE role_count INT DEFAULT 0;

SELECT
    role INTO account_role
FROM user_account
WHERE user_id=NEW.user_id;

IF account_role <> 'teacher' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT='Teacher user_id must reference a teacher account.';

END IF;

SELECT
    COUNT(*) INTO role_count
FROM student
WHERE user_id=NEW.user_id;

IF role_count > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT='User account already has student role extension.';

END IF;

SELECT
    COUNT(*) INTO role_count
FROM admin
WHERE user_id=NEW.user_id;

IF role_count > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT='User account already has admin role extension.';

END IF;

END //

CREATE TRIGGER trg_admin_check_user_role
BEFORE INSERT ON admin
FOR EACH ROW
BEGIN
    DECLARE account_role VARCHAR(20);

DECLARE role_count INT DEFAULT 0;

SELECT
    role INTO account_role
FROM user_account
WHERE user_id=NEW.user_id;

IF account_role <> 'admin' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT='Admin user_id must reference an admin account.';

END IF;

SELECT
    COUNT(*) INTO role_count
FROM student
WHERE user_id=NEW.user_id;

IF role_count > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT='User account already has student role extension.';

END IF;

SELECT
    COUNT(*) INTO role_count
FROM teacher
WHERE user_id=NEW.user_id;

IF role_count > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT='User account already has teacher role extension.';

END IF;

END //

CREATE TRIGGER trg_schedule_check_room
BEFORE INSERT ON schedule
FOR EACH ROW
BEGIN
    DECLARE room_status VARCHAR(20);

SELECT
    open_status INTO room_status
FROM room
WHERE room_id=NEW.room_id;

IF room_status <> 'open' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT='Schedule room must be open.';

END IF;

END //

CREATE TRIGGER trg_use_log_before_insert
BEFORE INSERT ON use_log
FOR EACH ROW
BEGIN
    DECLARE current_seat_status VARCHAR(20);

DECLARE current_room_status VARCHAR(20);

DECLARE active_log_count INT DEFAULT 0;

DECLARE schedule_room_id VARCHAR(20);

DECLARE schedule_class_id VARCHAR(20);

DECLARE student_class_id VARCHAR(20);

SELECT
    se.seat_status,
    r.open_status INTO current_seat_status,
    current_room_status
FROM seat se
JOIN room r
    ON se.room_id=r.room_id
WHERE se.room_id=NEW.room_id
  AND se.seat_no=NEW.seat_no;

IF current_room_status <> 'open' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT='Room is not open.';

END IF;

IF current_seat_status <> 'free' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT='Seat is not available.';

END IF;

SELECT
    COUNT(*) INTO active_log_count
FROM use_log
WHERE room_id=NEW.room_id
  AND seat_no=NEW.seat_no
  AND end_time IS NULL;

IF active_log_count > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT='Seat already has an active use log.';

END IF;

IF NEW.use_type='free' THEN
        SET NEW.attendance_status='not_applicable';

ELSE
        SELECT room_id,
    class_id
        INTO schedule_room_id,
    schedule_class_id
        FROM schedule
        WHERE schedule_id=NEW.schedule_id;

SELECT
    class_id INTO student_class_id
FROM student
WHERE student_id=NEW.student_id;

IF schedule_room_id <> NEW.room_id THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT='Class use log room must match schedule room.';

END IF;

IF schedule_class_id <> student_class_id THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT='Student class must match schedule class.';

END IF;

END IF;

END //

CREATE TRIGGER trg_use_log_occupy_seat
AFTER INSERT ON use_log
FOR EACH ROW
BEGIN
    IF NEW.use_type='class' THEN
        UPDATE seat
        SET seat_status='class_in_use'
        WHERE room_id=NEW.room_id
          AND seat_no=NEW.seat_no;

ELSE
        UPDATE seat
        SET seat_status='self_study'
        WHERE room_id=NEW.room_id
          AND seat_no=NEW.seat_no;

END IF;

END //

CREATE TRIGGER trg_use_log_release_seat
AFTER UPDATE ON use_log
FOR EACH ROW
BEGIN
    IF OLD.end_time IS NULL AND NEW.end_time IS NOT NULL THEN
        UPDATE seat
        SET seat_status='free'
        WHERE room_id=NEW.room_id
          AND seat_no=NEW.seat_no
          AND seat_status <> 'fault';

END IF;

END //

CREATE TRIGGER trg_repair_before_insert
BEFORE INSERT ON repair
FOR EACH ROW
BEGIN
    DECLARE submitter_role VARCHAR(20);

DECLARE handler_role VARCHAR(20);

SELECT
    role INTO submitter_role
FROM user_account
WHERE user_id=NEW.submitter_user_id;

IF submitter_role NOT IN ('student',
    'teacher') THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT='Repair submitter must be student or teacher.';

END IF;

IF NEW.handler_user_id IS NOT NULL THEN
        SELECT role INTO handler_role
        FROM user_account
        WHERE user_id=NEW.handler_user_id;

IF handler_role <> 'admin' THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT='Repair handler must be admin.';

END IF;

END IF;

END //

CREATE TRIGGER trg_repair_before_update
BEFORE UPDATE ON repair
FOR EACH ROW
BEGIN
    DECLARE submitter_role VARCHAR(20);

DECLARE handler_role VARCHAR(20);

SELECT
    role INTO submitter_role
FROM user_account
WHERE user_id=NEW.submitter_user_id;

IF submitter_role NOT IN ('student',
    'teacher') THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT='Repair submitter must be student or teacher.';

END IF;

IF NEW.handler_user_id IS NOT NULL THEN
        SELECT role INTO handler_role
        FROM user_account
        WHERE user_id=NEW.handler_user_id;

IF handler_role <> 'admin' THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT='Repair handler must be admin.';

END IF;

END IF;

END //

CREATE TRIGGER trg_repair_lock_seat
AFTER INSERT ON repair
FOR EACH ROW
BEGIN
    UPDATE seat
    SET seat_status='fault'
    WHERE room_id=NEW.room_id
      AND seat_no=NEW.seat_no;

END //

CREATE TRIGGER trg_repair_release_seat
AFTER UPDATE ON repair
FOR EACH ROW
BEGIN
    IF NEW.repair_status='done' AND OLD.repair_status <> 'done' THEN
        UPDATE seat
        SET seat_status='free'
        WHERE room_id=NEW.room_id
          AND seat_no=NEW.seat_no;

END IF;

END //

DELIMITER ;
