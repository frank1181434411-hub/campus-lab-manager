from functools import wraps

from flask import Flask,abort,flash,redirect,render_template,request,session,url_for

from app import config
from app.db import DatabaseError
from app.services import auth_service,repair_service,room_service,schedule_service,use_log_service


def create_app():
    app=Flask(__name__)
    app.config["SECRET_KEY"]=config.FLASK_SECRET_KEY
    register_filters(app)
    register_routes(app)
    register_errors(app)
    return app


def register_filters(app):
    labels={
        "student":"学生","teacher":"教师","admin":"管理员","active":"启用","disabled":"禁用","locked":"锁定","open":"开放","closed":"关闭","maintenance":"维护","free":"空闲","self_study":"自习中","class_in_use":"上课中","fault":"故障","class":"课堂上机","normal":"正常","late":"迟到","early_leave":"早退","absent":"缺勤","not_applicable":"不适用","pending":"待处理","processing":"处理中","done":"已完成",}

    @app.template_filter("label")
    def label(value):
        return labels.get(value,value)


def login_required(func):
    @wraps(func)
    def wrapper(*args,**kwargs):
        if "user_id" not in session:
            flash("请先登录。","warning")
            return redirect(url_for("login"))
        return func(*args,**kwargs)
    return wrapper


def role_required(*roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args,**kwargs):
            if "user_id" not in session:
                flash("请先登录。","warning")
                return redirect(url_for("login"))
            if session.get("role") not in roles:
                abort(403)
            return func(*args,**kwargs)
        return wrapper
    return decorator


def current_detail():
    return auth_service.get_current_user_detail(session["user_id"],session["role"])


def register_routes(app):
    @app.route("/")
    def index():
        if "role" not in session:
            return redirect(url_for("login"))
        return redirect(url_for(session["role"]))

    @app.route("/login",methods=["GET","POST"])
    def login():
        if request.method=="POST":
            username=request.form.get("username","").strip()
            password=request.form.get("password","")
            try:
                user=auth_service.authenticate_user(username,password)
                if not user:
                    flash("账号或密码错误。","error")
                    return render_template("login.html")
                session.clear()
                session["user_id"]=user["user_id"]
                session["username"]=user["username"]
                session["role"]=user["role"]
                session["display_name"]=user["display_name"]
                flash("登录成功。","success")
                return redirect(url_for(user["role"]))
            except DatabaseError as error:
                flash(str(error),"error")
        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        flash("已退出登录。","success")
        return redirect(url_for("login"))

    @app.route("/student")
    @role_required("student")
    def student():
        detail=current_detail()
        active=use_log_service.get_active_use(detail["student_id"])
        rooms=room_service.get_room_status_summary()
        schedules=schedule_service.get_student_schedules(detail["student_id"])
        history=use_log_service.get_student_history(detail["student_id"])[:5]
        attendance=use_log_service.get_student_attendance(detail["student_id"])[:5]
        repairs=repair_service.get_user_repairs(session["user_id"])[:5]
        return render_template(
            "student_dashboard.html",detail=detail,active=active,rooms=rooms,schedules=schedules,history=history,attendance=attendance,repairs=repairs,)

    @app.route("/teacher")
    @role_required("teacher")
    def teacher():
        detail=current_detail()
        schedules=schedule_service.get_teacher_schedules(detail["teacher_id"])
        rooms=room_service.get_room_status_summary()
        repairs=repair_service.get_user_repairs(session["user_id"])[:5]
        return render_template(
            "teacher_dashboard.html",detail=detail,schedules=schedules,rooms=rooms,repairs=repairs,)

    @app.route("/admin")
    @role_required("admin")
    def admin():
        counts=auth_service.get_counts()
        users=auth_service.get_all_users()
        students=auth_service.get_students()
        teachers=auth_service.get_teachers()
        usage=use_log_service.get_room_usage_statistics()
        logs=use_log_service.get_recent_logs()
        return render_template(
            "admin_dashboard.html",counts=counts,users=users,students=students,teachers=teachers,usage=usage,logs=logs,)

    @app.post("/admin/users/<int:user_id>/status")
    @role_required("admin")
    def admin_update_user_status(user_id):
        try:
            auth_service.update_user_status(user_id,request.form["status"])
            flash("账号状态已更新。","success")
        except DatabaseError as error:
            flash(str(error),"error")
        return redirect(url_for("admin"))

    @app.post("/password")
    @login_required
    def change_password():
        password=request.form.get("password","")
        if len(password)<6:
            flash("新密码至少 6 位。","error")
        else:
            try:
                auth_service.change_password(session["user_id"],password)
                flash("密码已修改。","success")
            except DatabaseError as error:
                flash(str(error),"error")
        return redirect(url_for(session["role"]))

    @app.route("/rooms")
    @login_required
    def rooms():
        room_id=request.args.get("room_id")
        summaries=room_service.get_room_status_summary()
        seats=room_service.get_room_seats(room_id) if room_id else []
        return render_template("room_list.html",rooms=summaries,seats=seats,selected_room=room_id)

    @app.post("/admin/rooms/create")
    @role_required("admin")
    def admin_create_room():
        try:
            room_service.create_room(
                request.form["room_id"],request.form["room_location"],int(request.form["total_seats"]),request.form["open_status"],)
            flash("机房已创建。","success")
        except (DatabaseError,ValueError) as error:
            flash(str(error),"error")
        return redirect(url_for("rooms"))

    @app.post("/admin/rooms/<room_id>/update")
    @role_required("admin")
    def admin_update_room(room_id):
        try:
            room_service.update_room(
                room_id,request.form["room_location"],int(request.form["total_seats"]),request.form["open_status"],)
            flash("机房已更新。","success")
        except (DatabaseError,ValueError) as error:
            flash(str(error),"error")
        return redirect(url_for("rooms",room_id=room_id))

    @app.post("/admin/seats/create")
    @role_required("admin")
    def admin_create_seat():
        room_id=request.form["room_id"]
        try:
            room_service.create_seat(
                room_id,request.form["seat_no"],request.form.get("ip_address") or None,request.form.get("machine_config") or None,request.form["seat_status"],)
            flash("机位已创建。","success")
        except DatabaseError as error:
            flash(str(error),"error")
        return redirect(url_for("rooms",room_id=room_id))

    @app.post("/admin/seats/update")
    @role_required("admin")
    def admin_update_seat():
        room_id=request.form["room_id"]
        try:
            room_service.update_seat(
                room_id,request.form["seat_no"],request.form.get("ip_address") or None,request.form.get("machine_config") or None,request.form["seat_status"],)
            flash("机位已更新。","success")
        except DatabaseError as error:
            flash(str(error),"error")
        return redirect(url_for("rooms",room_id=room_id))

    @app.post("/student/use/start")
    @role_required("student")
    def start_use():
        detail=current_detail()
        try:
            mode=request.form["mode"]
            if mode=="class":
                use_log_service.start_class_use(
                    detail["student_id"],request.form["room_id"],request.form["seat_no"],int(request.form["schedule_id"]),)
            else:
                use_log_service.start_free_use(
                    detail["student_id"],request.form["room_id"],request.form["seat_no"],)
            flash("上机记录已创建。","success")
        except (DatabaseError,ValueError) as error:
            flash(str(error),"error")
        return redirect(url_for("student"))

    @app.post("/student/use/finish")
    @role_required("student")
    def finish_use():
        detail=current_detail()
        try:
            use_log_service.finish_use(int(request.form["log_id"]),detail["student_id"])
            flash("下机成功。","success")
        except (DatabaseError,ValueError) as error:
            flash(str(error),"error")
        return redirect(url_for("student"))

    @app.route("/student/history")
    @role_required("student")
    def student_history():
        detail=current_detail()
        rows=use_log_service.get_student_history(detail["student_id"])
        return render_template("use_history.html",rows=rows)

    @app.route("/student/attendance")
    @role_required("student")
    def student_attendance():
        detail=current_detail()
        rows=use_log_service.get_student_attendance(detail["student_id"])
        return render_template("attendance_list.html",rows=rows,schedule=None)

    @app.route("/teacher/schedules")
    @role_required("teacher")
    def teacher_schedules():
        detail=current_detail()
        schedules=schedule_service.get_teacher_schedules(detail["teacher_id"])
        return render_template("schedule_list.html",schedules=schedules,owner="teacher")

    @app.route("/teacher/attendance/<int:schedule_id>")
    @role_required("teacher")
    def teacher_attendance(schedule_id):
        detail=current_detail()
        schedule=schedule_service.get_schedule_detail(schedule_id)
        if not schedule or schedule["teacher_id"]!=detail["teacher_id"]:
            abort(403)
        rows=use_log_service.get_schedule_attendance(schedule_id)
        return render_template("attendance_list.html",rows=rows,schedule=schedule)

    @app.route("/admin/schedules")
    @role_required("admin")
    def admin_schedules():
        schedules=schedule_service.get_all_schedules()
        courses=schedule_service.get_courses()
        teachers=auth_service.get_teachers()
        classes=auth_service.get_classes()
        rooms=room_service.get_all_rooms()
        return render_template(
            "schedule_list.html",schedules=schedules,courses=courses,teachers=teachers,classes=classes,rooms=rooms,owner="admin",)

    @app.post("/admin/schedules/create")
    @role_required("admin")
    def admin_schedule_create():
        try:
            schedule_service.create_schedule(
                request.form["semester"],request.form["week_no"],int(request.form["weekday"]),request.form["class_period"],request.form["teacher_id"],request.form["class_id"],request.form["course_id"],request.form["room_id"],)
            flash("排课已创建。","success")
        except (DatabaseError,ValueError) as error:
            flash(str(error),"error")
        return redirect(url_for("admin_schedules"))

    @app.post("/admin/schedules/<int:schedule_id>/edit")
    @role_required("admin")
    def admin_schedule_edit(schedule_id):
        try:
            schedule_service.update_schedule(
                schedule_id,request.form["semester"],request.form["week_no"],int(request.form["weekday"]),request.form["class_period"],request.form["teacher_id"],request.form["class_id"],request.form["course_id"],request.form["room_id"],)
            flash("排课已更新。","success")
        except (DatabaseError,ValueError) as error:
            flash(str(error),"error")
        return redirect(url_for("admin_schedules"))

    @app.post("/admin/schedules/<int:schedule_id>/delete")
    @role_required("admin")
    def admin_schedule_delete(schedule_id):
        try:
            schedule_service.delete_schedule(schedule_id)
            flash("排课已删除。","success")
        except DatabaseError as error:
            flash(str(error),"error")
        return redirect(url_for("admin_schedules"))

    @app.route("/repairs")
    @login_required
    def repairs():
        if session["role"]=="admin":
            rows=repair_service.get_all_repairs(
                status=request.args.get("status") or None,room_id=request.args.get("room_id") or None,)
        else:
            rows=repair_service.get_user_repairs(session["user_id"])
        return render_template("repair_list.html",repairs=rows)

    @app.post("/repairs/create")
    @role_required("student","teacher")
    def repair_create():
        try:
            repair_service.submit_repair(
                session["user_id"],request.form["room_id"],request.form["seat_no"],request.form["fault_description"],)
            flash("报修已提交。","success")
        except DatabaseError as error:
            flash(str(error),"error")
        return redirect(url_for("repairs"))

    @app.post("/repairs/<int:repair_id>/assign")
    @role_required("admin")
    def repair_assign(repair_id):
        try:
            repair_service.assign_repair(repair_id,session["user_id"])
            flash("报修已分配给当前管理员。","success")
        except DatabaseError as error:
            flash(str(error),"error")
        return redirect(url_for("repairs"))

    @app.post("/repairs/<int:repair_id>/status")
    @role_required("admin")
    def repair_status(repair_id):
        try:
            repair_service.update_repair_status(repair_id,session["user_id"],request.form["repair_status"])
            flash("维修状态已更新。","success")
        except DatabaseError as error:
            flash(str(error),"error")
        return redirect(url_for("repairs"))


def register_errors(app):
    @app.errorhandler(403)
    def forbidden(error):
        return render_template("error.html",code=403,message="没有权限访问该页面。"),403

    @app.errorhandler(404)
    def not_found(error):
        return render_template("error.html",code=404,message="页面不存在。"),404

    @app.errorhandler(500)
    def server_error(error):
        return render_template("error.html",code=500,message="服务器内部错误。"),500


app=create_app()


if __name__=="__main__":
    app.run(host=config.FLASK_HOST,port=config.FLASK_PORT,debug=config.FLASK_DEBUG)
