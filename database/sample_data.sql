-- Optional sample data for Campus Lab Manager
-- Run database/schema.sql before this file.

USE campus_lab_manager;

SET NAMES utf8mb4;

INSERT INTO user_account (user_id, username, password, role, status, phone) VALUES
(1, 'stu001', '123456', 'student', 'active', '13800000001'),
(2, 'stu002', '123456', 'student', 'active', '13800000002'),
(3, 't001', '123456', 'teacher', 'active', '13800000003'),
(4, 'admin001', '123456', 'admin', 'active', '13800000004'),
(5, 'stu003', '123456', 'student', 'active', '13800000005')
ON DUPLICATE KEY UPDATE
    username = VALUES(username),
    password = VALUES(password),
    role = VALUES(role),
    status = VALUES(status),
    phone = VALUES(phone);

INSERT INTO class_info (class_id, class_name, major, total_number) VALUES
('CS2301', '计算机2301班', '计算机科学与技术', 3),
('SE2301', '软件2301班', '软件工程', 0)
ON DUPLICATE KEY UPDATE
    class_name = VALUES(class_name),
    major = VALUES(major),
    total_number = VALUES(total_number);

INSERT INTO student (student_id, user_id, student_name, gender, grade, class_id) VALUES
('20230001', 1, '张三', '男', '2023', 'CS2301'),
('20230002', 2, '李四', '女', '2023', 'CS2301'),
('20230003', 5, '王五', '男', '2023', 'CS2301')
ON DUPLICATE KEY UPDATE
    user_id = VALUES(user_id),
    student_name = VALUES(student_name),
    gender = VALUES(gender),
    grade = VALUES(grade),
    class_id = VALUES(class_id);

INSERT INTO teacher (teacher_id, user_id, teacher_name, title) VALUES
('T001', 3, '赵老师', '讲师')
ON DUPLICATE KEY UPDATE
    user_id = VALUES(user_id),
    teacher_name = VALUES(teacher_name),
    title = VALUES(title);

INSERT INTO admin (admin_id, user_id, admin_name) VALUES
('A001', 4, '系统管理员')
ON DUPLICATE KEY UPDATE
    user_id = VALUES(user_id),
    admin_name = VALUES(admin_name);

INSERT INTO course (course_id, course_name, total_hours, course_type) VALUES
('DB001', '数据库原理与应用', 48, '必修'),
('LAB001', '计算机基础实验', 32, '实验')
ON DUPLICATE KEY UPDATE
    course_name = VALUES(course_name),
    total_hours = VALUES(total_hours),
    course_type = VALUES(course_type);

INSERT INTO room (room_id, room_location, total_seats, open_status) VALUES
('R101', '一号教学楼 101', 5, 'open'),
('R102', '一号教学楼 102', 5, 'open')
ON DUPLICATE KEY UPDATE
    room_location = VALUES(room_location),
    total_seats = VALUES(total_seats),
    open_status = VALUES(open_status);

INSERT INTO seat (room_id, seat_no, ip_address, machine_config, seat_status) VALUES
('R101', '01', '192.168.1.101', 'i5/16GB/512GB', 'free'),
('R101', '02', '192.168.1.102', 'i5/16GB/512GB', 'free'),
('R101', '03', '192.168.1.103', 'i5/16GB/512GB', 'free'),
('R102', '01', '192.168.2.101', 'i7/16GB/512GB', 'free'),
('R102', '02', '192.168.2.102', 'i7/16GB/512GB', 'free')
ON DUPLICATE KEY UPDATE
    ip_address = VALUES(ip_address),
    machine_config = VALUES(machine_config),
    seat_status = VALUES(seat_status);

INSERT INTO schedule (
    schedule_id,
    semester,
    week_no,
    weekday,
    class_period,
    teacher_id,
    class_id,
    course_id,
    room_id
) VALUES
(1, '2025-2026-1', '1-16', 1, '1-2', 'T001', 'CS2301', 'DB001', 'R101'),
(2, '2025-2026-1', '1-16', 3, '3-4', 'T001', 'CS2301', 'LAB001', 'R102')
ON DUPLICATE KEY UPDATE
    semester = VALUES(semester),
    week_no = VALUES(week_no),
    weekday = VALUES(weekday),
    class_period = VALUES(class_period),
    teacher_id = VALUES(teacher_id),
    class_id = VALUES(class_id),
    course_id = VALUES(course_id),
    room_id = VALUES(room_id);

INSERT INTO repair (
    repair_id,
    submitter_user_id,
    handler_user_id,
    room_id,
    seat_no,
    report_time,
    fault_description,
    repair_status
) VALUES
(1, 1, NULL, 'R101', '03', '2026-06-18 09:00:00', '显示器无法正常点亮', 'pending')
ON DUPLICATE KEY UPDATE
    submitter_user_id = VALUES(submitter_user_id),
    handler_user_id = VALUES(handler_user_id),
    room_id = VALUES(room_id),
    seat_no = VALUES(seat_no),
    report_time = VALUES(report_time),
    fault_description = VALUES(fault_description),
    repair_status = VALUES(repair_status);
