-- Common test and defense queries for Campus Lab Manager

USE campus_lab_manager;

SET NAMES utf8mb4;

-- 1. 查询所有用户账号
SELECT
    user_id,username,role,status,phone
FROM user_account
ORDER BY user_id;

-- 2. 查询学生信息和所属班级
SELECT
    s.student_id,s.student_name,s.gender,s.grade,ci.class_id,ci.class_name,ci.major
FROM student s
JOIN class_info ci ON s.class_id=ci.class_id
ORDER BY ci.class_id,s.student_id;

-- 3. 查询教师课表
-- 修改 teacher_id 可以查询指定教师课表。
SELECT
    teacher_id,teacher_name,schedule_id,course_name,class_name,room_id,room_location,semester,week_no,weekday,class_period
FROM v_teacher_schedule
WHERE teacher_id='T001'
ORDER BY semester,weekday,class_period;

-- 4. 查询机房空闲机位
SELECT
    room_id,room_location,COUNT(*) AS free_seat_count
FROM v_room_seat_status
WHERE open_status='open'
  AND seat_status='free'
GROUP BY room_id,room_location
ORDER BY room_id;

-- 5. 查询学生上机历史
-- 修改 student_id 可以查询指定学生。
SELECT
    student_id,student_name,room_id,room_location,seat_no,start_time,end_time,use_type,attendance_status
FROM v_student_use_history
WHERE student_id='20230001'
ORDER BY start_time DESC;

-- 6. 查询某节课考勤记录
-- 修改 schedule_id 可以查询指定排课的考勤。
SELECT
    schedule_id,course_name,class_name,teacher_name,student_id,student_name,start_time,end_time,attendance_status
FROM v_class_attendance
WHERE schedule_id=1
ORDER BY student_id;

-- 7. 查询待处理报修记录
SELECT
    repair_id,room_id,seat_no,report_time,fault_description,repair_status,submitter_username,submitter_role
FROM v_repair_detail
WHERE repair_status IN ('pending','processing')
ORDER BY report_time ASC;

-- 8. 查询某机房故障机位
-- 修改 room_id 可以查询指定机房。
SELECT
    room_id,room_location,seat_no,ip_address,machine_config,seat_status
FROM v_room_seat_status
WHERE room_id='R101'
  AND seat_status='fault'
ORDER BY seat_no;

-- 9. 统计某班课程出勤率
-- 这里按 schedule_id 统计某次课程安排的正常出勤率。
SELECT
    sc.schedule_id,ci.class_id,ci.class_name,c.course_id,c.course_name,COUNT(s.student_id) AS total_students,SUM(CASE WHEN ul.attendance_status='normal' THEN 1 ELSE 0 END) AS normal_count,SUM(CASE WHEN ul.attendance_status='late' THEN 1 ELSE 0 END) AS late_count,SUM(CASE WHEN ul.attendance_status='early_leave' THEN 1 ELSE 0 END) AS early_leave_count,SUM(CASE WHEN ul.log_id IS NULL OR ul.attendance_status='absent' THEN 1 ELSE 0 END) AS absent_count,ROUND(
        SUM(CASE WHEN ul.attendance_status IN ('normal','late','early_leave') THEN 1 ELSE 0 END)
        / COUNT(s.student_id) * 100,2
    ) AS attendance_rate_percent
FROM schedule sc
JOIN class_info ci ON sc.class_id=ci.class_id
JOIN course c ON sc.course_id=c.course_id
JOIN student s ON s.class_id=ci.class_id
LEFT JOIN use_log ul
    ON ul.schedule_id=sc.schedule_id
   AND ul.student_id=s.student_id
WHERE sc.schedule_id=1
GROUP BY
    sc.schedule_id,ci.class_id,ci.class_name,c.course_id,c.course_name;

-- 10. 统计机房使用率
-- 按当前机位状态统计某机房使用率。修改 room_id 可以查询指定机房。
SELECT
    r.room_id,r.room_location,COUNT(se.seat_no) AS total_seats,SUM(CASE WHEN se.seat_status IN ('self_study','class_in_use') THEN 1 ELSE 0 END) AS using_seats,SUM(CASE WHEN se.seat_status='free' THEN 1 ELSE 0 END) AS free_seats,SUM(CASE WHEN se.seat_status='fault' THEN 1 ELSE 0 END) AS fault_seats,ROUND(
        SUM(CASE WHEN se.seat_status IN ('self_study','class_in_use') THEN 1 ELSE 0 END)
        / COUNT(se.seat_no) * 100,2
    ) AS current_usage_rate_percent
FROM room r
JOIN seat se ON r.room_id=se.room_id
WHERE r.room_id='R101'
GROUP BY r.room_id,r.room_location;
