from flask_security.utils import hash_password, verify_password
from flask import current_app as app
from flask import (
    request,
    redirect,
    url_for,
    flash,
    session,
    jsonify,
)

from .api import *
from .models import *
from .task import *
from .security import *
from .database import *
from .cache import cache

import os
import base64
import os.path as osp
import time
from matplotlib.figure import Figure


@app.before_first_request
def database():
    db.create_all()


@app.route("/")
def home():
    return jsonify({"resp": "ok", "msg": "The Tracker App is Running"})


# -------------------------REGISTER-------------------------#


@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        data = request.get_json()

        username, email, pwd, sec_Q, sec_A = (
            data["username"],
            data["email"],
            data["password"],
            data["sec_que"],
            data["sec_ans"],
        )

        if User.query.filter_by(email=email).first():
            return jsonify(
                {
                    "resp": "not ok",
                    "msg": "Email is already registered",
                }
            )
        elif User.query.filter_by(username=username).first():
            return jsonify(
                {
                    "resp": "not ok",
                    "msg": "Username is already taken",
                }
            )
        else:
            user_datastore.create_user(
                email=email,
                username=username,
                password=hash_password(pwd),
                sec_ques=sec_Q,
                sec_ans=base64.b64encode(sec_A.encode("ascii")),
            )
            db.session.commit()
            user_fig_dir = f"../frontend/myapp/src/assets/{username}"
            if not osp.exists(user_fig_dir):
                os.makedirs(user_fig_dir)

            return jsonify({"resp": "ok", "msg": "Account created"})
    else:
        return jsonify(
            {
                "resp": "not ok",
                "msg": f"Welcome to Register page ({request.method} request received)",
            }
        )


# -------------------------LOGIN-------------------------#


@app.route("/login_page", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        data = request.get_json()

        user_data = User.query.filter_by(email=data["email"]).first()

        if not user_data:
            return jsonify({"resp": "not ok", "msg": "User does not exists"})

        else:
            pswd = user_data.password
            username = user_data.username
            if verify_password(data["password"], pswd):
                session["email"], session["pwd"], session["username"] = (
                    data["email"],
                    data["password"],
                    username,
                )
                return jsonify(
                    {"resp": "ok", "msg": "Log in success", "stuff": str(username)}
                )
            else:
                return jsonify({"resp": "not ok", "msg": "Incorrect password"})
    else:
        return jsonify(
            {
                "resp": "not ok",
                "msg": f"Welcome to Log in page ({request.method} request received)",
            }
        )


# -------------------------DASHBOARD-------------------------#


@app.route("/dashboard/<string:username>", methods=["GET"])
@cache.memoize()
def dashboard(username):
    user_data = User.query.filter_by(username=username).first()
    trackerObjs = user_data.trackers

    tracker_list = []
    for trackerObj in trackerObjs:
        tracker_list.append(trackerObj)

    tracker_dict = {}
    for idx, tracker in enumerate(tracker_list):
        tracker_dict[idx] = {
            "id": tracker.id,
            "name": tracker.name,
            "description": tracker.description,
            "type": tracker.type,
            "date_created": tracker.date_created,
        }
    return jsonify({"resp": "ok", "msg": "Trackers parsed", "stuff": tracker_dict})


# -------------------------LOGOUT-------------------------#


@app.route("/logout_page", methods=["GET"])
def logout():
    session.clear()
    cache.clear()
    return jsonify({"resp": "ok", "msg": "Logged out"})


# -------------------------CREATE_TRACKER-------------------------#


@app.route("/dashboard/<string:username>/create_tracker", methods=["POST", "GET"])
def create_tracker(username):
    cache.delete_memoized(dashboard, username)
    if request.method == "POST":
        data = request.get_json()

        trackerName, trackerDescription, trackerType = (
            data["tracker_name"],
            data["tracker_des"],
            data["tracker_type"],
        )

        new_tracker = Tracker(
            name=trackerName, description=trackerDescription, type=trackerType
        )

        user = User.query.filter_by(username=username).first()
        user.trackers.append(new_tracker)
        db.session.add(new_tracker)
        db.session.commit()
        fig = Figure()
        axis = fig.add_subplot(1, 1, 1)
        axis.set(xlabel="Time Stamp", ylabel="Value")
        fig.savefig(f"../frontend/myapp/src/assets/{username}/{new_tracker.id}.png")
        return jsonify({"resp": "ok", "msg": "tracker successfully created"})
    else:
        return jsonify(
            {
                "resp": "not ok",
                "msg": f"Welcome to AddTracker page ({request.method} request received)",
            }
        )


# -------------------------UPDATE_TRACKER-------------------------#


@app.route("/<string:username>/<int:trackerID>/update", methods=["POST"])
def update(username, trackerID):
    cache.delete_memoized(dashboard, username)
    tracker = Tracker.query.filter_by(id=trackerID).first()
    data = request.get_json()
    if tracker:
        tracker.name, tracker.description = data["tracker_name"], data["tracker_des"]
        db.session.commit()
        return jsonify({"resp": "ok", "msg": "tracker updated successfully"})


# -------------------------CREATE_LOGS-------------------------#


@app.route("/<string:username>/<int:trackerID>/logs", methods=["GET"])
@cache.memoize()
def log(username, trackerID):
    parent_tracker = Tracker.query.filter_by(id=trackerID).first()
    if request.method == "GET":
        time.sleep(5)
        all_logs = parent_tracker.logs
        img_pth = f"../frontend/myapp/src/assets/{username}/{trackerID}.png"
        log_list = []
        for log in all_logs:
            log_list.append(log)
        data = {}
        if parent_tracker.type == "numeric":
            data = {x.timestamp: x.value for x in all_logs}
        else:
            data = {x.timestamp: 1 if x.value == "Yes" else 0 for x in all_logs}
        fig = Figure()
        axis = fig.add_subplot(1, 1, 1)
        axis.plot(data.keys(), data.values())
        axis.set(xlabel="Time Stamp", ylabel="Value")
        fig.savefig(img_pth)
        with open(img_pth, "rb") as image_file:
            encodedImage = str(base64.b64encode(image_file.read()).decode("utf-8"))

        log_dict = {}
        for idx, log in enumerate(log_list):
            Dlog = {
                "log": log.log,
                "logID": log.id,
                "value": log.value,
                "note": log.note,
                "timestamp": log.timestamp,
            }
            log_dict[idx] = Dlog
        return jsonify(
            {
                "resp": "ok",
                "msg": "logs parsed",
                "stuff": {"logData": log_dict, "encodedImage": encodedImage},
            }
        )


@app.route("/<string:username>/<int:trackerID>/bounce_log_cache", methods=["POST"])
def bounce_log_cache(username, trackerID):
    cache.delete_memoized(log, username, trackerID)
    parent_tracker = Tracker.query.filter_by(id=trackerID).first()
    img_pth = f"../frontend/myapp/src/assets/{username}/{trackerID}.png"
    data = request.get_json()

    new_log = Logs(
        value=data["log_value"], note=data["log_note"], log=parent_tracker.type
    )
    parent_tracker.logs.append(new_log)
    db.session.add(new_log)
    db.session.commit()

    with open(img_pth, "rb") as image_file:
        encodedImage = str(base64.b64encode(image_file.read()).decode("utf-8"))

    all_logs = parent_tracker.logs
    log_list = []
    for mylog in all_logs:
        log_list.append(mylog)
    log_dict = {}
    for idx, mylog in enumerate(log_list):
        Dlog = {
            "log": mylog.log,
            "logID": mylog.id,
            "value": mylog.value,
            "note": mylog.note,
            "timestamp": mylog.timestamp,
        }
        log_dict[idx] = Dlog
    return jsonify(
        {
            "resp": "ok",
            "msg": "new log added and log cache cleared successfully",
            "stuff": {"logData": log_dict, "encodedImage": encodedImage},
        }
    )


# -------------------------DELETE_TRACKER-------------------------#


@app.route("/<string:username>/<int:trackerID>/delete", methods=["GET"])
def delete(username, trackerID):
    cache.delete_memoized(dashboard, username)
    targetTracker = Tracker.query.get_or_404(trackerID)
    try:
        db.session.delete(targetTracker)
        db.session.commit()
        return jsonify({"resp": "ok", "msg": "Tracker deleted successfully."})
    except:

        return jsonify(
            {
                "resp": "not ok",
                "msg": "Problem encountered while trying to delete tracker",
            }
        )


# -------------------------DELETE_LOGS-------------------------#


@app.route("/<string:username>/<int:trackerID>/<int:logID>/delete", methods=["GET"])
def delete_log(username, trackerID, logID):
    cache.delete_memoized(log, username, trackerID)
    myLog = Logs.query.get_or_404(logID)
    try:
        db.session.delete(myLog)
        db.session.commit()
        return jsonify({"resp": "ok", "msg": "Event deleted succesfully"})
    except:
        return jsonify(
            {
                "resp": "not ok",
                "msg": "Problem encountered while trying to delete event",
            }
        )


# -------------------------UPDATE_LOGS-------------------------#


@app.route("/<string:username>/<int:trackerID>/<int:logID>/update", methods=["POST"])
def update_log(username, trackerID, logID):
    cache.delete_memoized(log, username, trackerID)
    myLog = Logs.query.filter_by(id=logID).first()
    data = request.get_json()
    if myLog:
        myLog.value, myLog.note = data["log_value"], data["log_note"]
        db.session.commit()
        return jsonify({"resp": "ok", "msg": "log updated successfully"})


@app.route("/<string:username>/export_trackers", methods=["GET", "POST"])
def export_tracker(username):
    if request.method == "POST":
        job = trigerred_summary_export(username)
        return jsonify(
            {"resp": "ok", "msg": f"{str(job)}. Exported successfully. Status: 200"}
        )
    else:
        return jsonify({"resp": "not ok", "msg": "GET request received"})


@app.route("/<string:username>/<int:trackerID>/export_events", methods=["GET", "POST"])
def export_events(username, trackerID):
    if request.method == "POST":
        job = trigerred_events_export(username, trackerID)
        return jsonify(
            {"resp": "ok", "msg": f"{str(job)}. Exported successfully. Status: 200"}
        )
    else:
        return jsonify({"resp": "not ok", "msg": "GET request received"})
