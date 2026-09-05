from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


app = Flask(__name__)
app.secret_key = "interviewflow-admin-secret-key"



ROOMS = [
    "Assessment Hall A",
    "Room 102",
    "Room 103",
    "Room 104"
]


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db():
    return supabase

# =========================================================
# CREATE DATABASE TABLES
# =========================================================

def init_db():
    print("Supabase database connected.")

init_db()


# =========================================================
# CANDIDATE DATABASE FUNCTIONS
# =========================================================

def get_all_candidates():
    response = (
        supabase
        .table("candidates")
        .select("*")
        .order("id")
        .execute()
    )

    return response.data or []


def find_candidate(candidate_id):
    if not candidate_id:
        return None

    response = (
        supabase
        .table("candidates")
        .select("*")
        .ilike("id", candidate_id)
        .limit(1)
        .execute()
    )

    data = response.data or []

    return data[0] if data else None

# =========================================================
# SCHEDULE DATABASE FUNCTIONS
# =========================================================

def get_schedule(candidate_id):
    response = (
        supabase
        .table("interview_schedules")
        .select("*")
        .eq("candidate_id", candidate_id)
        .limit(1)
        .execute()
    )

    data = response.data or []

    return data[0] if data else None


def get_all_schedules():
    response = (
        supabase
        .table("interview_schedules")
        .select("*")
        .execute()
    )

    return {
        row["candidate_id"]: row
        for row in (response.data or [])
    }

# =========================================================
# CALCULATE INTERVIEW TIMES
# =========================================================

def calculate_interview_times(
    interview_date,
    starting_time,
    buffer_time,
    aptitude_duration,
    technical_duration,
    managerial_duration,
    hr_duration
):

    start_datetime = datetime.strptime(
        f"{interview_date} {starting_time}",
        "%Y-%m-%d %H:%M"
    )

    # Candidate reports 30 minutes before Round 1
    reporting_datetime = (
        start_datetime -
        timedelta(minutes=30)
    )

    # ROUND 1

    round1_start = start_datetime

    round1_end = (
        round1_start +
        timedelta(minutes=aptitude_duration)
    )

    # BUFFER 1

    break1_start = round1_end

    break1_end = (
        break1_start +
        timedelta(minutes=buffer_time)
    )

    # ROUND 2

    round2_start = break1_end

    round2_end = (
        round2_start +
        timedelta(minutes=technical_duration)
    )

    # BUFFER 2

    break2_start = round2_end

    break2_end = (
        break2_start +
        timedelta(minutes=buffer_time)
    )

    # ROUND 3

    round3_start = break2_end

    round3_end = (
        round3_start +
        timedelta(minutes=managerial_duration)
    )

    # BUFFER 3

    break3_start = round3_end

    break3_end = (
        break3_start +
        timedelta(minutes=buffer_time)
    )

    # ROUND 4

    round4_start = break3_end

    round4_end = (
        round4_start +
        timedelta(minutes=hr_duration)
    )

    return {

        "start_datetime": start_datetime,

        "reporting_datetime": reporting_datetime,

        "round1_start": round1_start,
        "round1_end": round1_end,

        "break1_start": break1_start,
        "break1_end": break1_end,

        "round2_start": round2_start,
        "round2_end": round2_end,

        "break2_start": break2_start,
        "break2_end": break2_end,

        "round3_start": round3_start,
        "round3_end": round3_end,

        "break3_start": break3_start,
        "break3_end": break3_end,

        "round4_start": round4_start,
        "round4_end": round4_end
    }


# =========================================================
# CHECK ROOM AVAILABILITY
# =========================================================

def room_is_available(
    room,
    interview_date,
    start_datetime,
    end_datetime,
    ignore_candidate_id=None
):

    response = (
        supabase
        .table("interview_schedules")
        .select(
            "candidate_id,session_start_raw,session_end_raw,room"
        )
        .eq("date", interview_date)
        .eq("room", room)
        .execute()
    )

    rows = response.data or []

    for row in rows:

        existing_candidate_id = row["candidate_id"]

        # Ignore candidate's own old booking while rescheduling
        if (
            ignore_candidate_id
            and
            existing_candidate_id.upper()
            == ignore_candidate_id.upper()
        ):
            continue

        existing_start_string = row["session_start_raw"]
        existing_end_string = row["session_end_raw"]

        if (
            not existing_start_string
            or
            not existing_end_string
        ):
            continue

        existing_start = datetime.strptime(
            existing_start_string,
            "%Y-%m-%d %H:%M"
        )

        existing_end = datetime.strptime(
            existing_end_string,
            "%Y-%m-%d %H:%M"
        )

        # Overlap check
        if (
            existing_start < end_datetime
            and
            existing_end > start_datetime
        ):
            return False

    return True
# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# =========================================================
# CANDIDATE VERIFICATION
# =========================================================

@app.route(
    "/candidate",
    methods=["GET", "POST"]
)
def candidate():

    verified_candidate = None
    error = None

    if request.method == "POST":

        candidate_id = request.form.get(
            "candidate_id",
            ""
        ).strip()

        print()
        print("=" * 55)
        print("           CANDIDATE VERIFICATION")
        print("=" * 55)
        print(f"Candidate ID Entered : {candidate_id}")

        verified_candidate = find_candidate(
            candidate_id
        )

        if verified_candidate is None:

            error = (
                "Invalid Candidate ID. "
                "Please check your ID and try again."
            )

            print("STATUS                : INVALID ID")

        else:

            print(
                f"Candidate Name        : "
                f"{verified_candidate['name']}"
            )

            print(
                f"Candidate Email       : "
                f"{verified_candidate['email']}"
            )

            print("STATUS                : VERIFIED")

        print("=" * 55)
        print()

    return render_template(
        "candidate.html",
        candidate=verified_candidate,
        error=error
    )


# =========================================================
# INTERVIEW PROCESS
# =========================================================

@app.route("/process")
def process():

    candidate_id = request.args.get(
        "candidate_id",
        ""
    ).strip()

    if not candidate_id:

        return redirect(
            url_for("candidate")
        )

    selected_candidate = find_candidate(
        candidate_id
    )

    if selected_candidate is None:

        return redirect(
            url_for("candidate")
        )

    return render_template(
        "process.html",
        candidate=selected_candidate
    )


# =========================================================
# INTERVIEW SCHEDULE
# =========================================================

@app.route("/schedule")
def schedule():

    candidate_id = request.args.get(
        "candidate_id",
        ""
    ).strip()

    if not candidate_id:

        return redirect(
            url_for("candidate")
        )

    selected_candidate = find_candidate(
        candidate_id
    )

    if selected_candidate is None:

        return redirect(
            url_for("candidate")
        )

    schedule_data = get_schedule(
        selected_candidate["id"]
    )

    return render_template(
        "schedule.html",
        candidate=selected_candidate,
        schedule=schedule_data
    )


# =========================================================
# CANDIDATE INSTRUCTIONS
# =========================================================

@app.route("/instructions")
def instructions():

    candidate_id = request.args.get(
        "candidate_id",
        ""
    ).strip()

    if not candidate_id:

        return redirect(
            url_for("candidate")
        )

    selected_candidate = find_candidate(
        candidate_id
    )

    if selected_candidate is None:

        return redirect(
            url_for("candidate")
        )

    schedule_data = get_schedule(
        selected_candidate["id"]
    )

    return render_template(
        "instructions.html",
        candidate=selected_candidate,
        schedule=schedule_data
    )


# =========================================================
# ADMIN LOGIN
# =========================================================

ADMIN_ID = "AD-0001"
ADMIN_PASSWORD = "0000"


@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():

    error = None

    if request.method == "POST":

        admin_id = request.form.get("admin_id", "").strip()
        password = request.form.get("password", "").strip()

        print()
        print("=" * 55)
        print("                ADMIN LOGIN")
        print("=" * 55)
        print(f"Admin ID Entered : {admin_id}")

        if admin_id == ADMIN_ID and password == ADMIN_PASSWORD:

            session["admin_logged_in"] = True

            print("STATUS           : LOGIN SUCCESSFUL")
            print("=" * 55)
            print()

            return redirect(url_for("admin"))

        error = "Invalid Admin ID or Password."

        print("STATUS           : LOGIN FAILED")
        print("=" * 55)
        print()

    return render_template(
        "admin_login.html",
        error=error
    )


@app.route("/logout")
def logout():

    session.pop("admin_logged_in", None)

    print()
    print("=" * 55)
    print("                ADMIN LOGOUT")
    print("=" * 55)
    print("STATUS           : LOGGED OUT")
    print("=" * 55)
    print()

    return redirect(url_for("home"))


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route("/admin")
def admin():

    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    reschedule_id = request.args.get(
        "reschedule_id",
        ""
    ).strip()

    reschedule_candidate = None
    current_schedule = None

    if reschedule_id:

        reschedule_candidate = find_candidate(
            reschedule_id
        )

        if reschedule_candidate:

            current_schedule = get_schedule(
                reschedule_candidate["id"]
            )

    all_candidates = get_all_candidates()

    all_schedules = get_all_schedules()

    return render_template(
        "admin.html",
        candidates=all_candidates,
        interview_schedule=all_schedules,
        rooms=ROOMS,
        reschedule_candidate=reschedule_candidate,
        current_schedule=current_schedule
    )


# =========================================================
# ADD CANDIDATE
# =========================================================

@app.route(
    "/add-candidate",
    methods=["POST"]
)

def add_candidate():

    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    name = request.form.get(
        "candidate_name",
        ""
    ).strip()

    email = request.form.get(
        "candidate_email",
        ""
    ).strip()

    print()
    print("=" * 55)
    print("             ADD CANDIDATE")
    print("=" * 55)
    print(f"Candidate Name  : {name}")
    print(f"Candidate Email : {email}")

    if not name or not email:

        print("STATUS          : FAILED - Missing Details")
        print("=" * 55)
        print()

        return redirect(
            url_for("admin")
        )

    response = (
        supabase
        .table("candidates")
        .select("id")
        .order("id", desc=True)
        .limit(1)
        .execute()
    )

    rows = response.data or []

    if rows:

        try:

            last_number = int(
                rows[0]["id"].split("-")[1]
            )

            next_number = (
                last_number + 1
            )

        except (
            ValueError,
            IndexError
        ):

            next_number = 1001

    else:

        next_number = 1001

    candidate_id = (
        f"INT-{next_number}"
    )

    supabase.table("candidates").insert({
        "id": candidate_id,
        "name": name,
        "email": email,
        "status": "Added"
    }).execute()

    print(f"Generated ID    : {candidate_id}")
    print("STATUS          : CANDIDATE ADDED")
    print("=" * 55)
    print()

    return redirect(
        url_for("admin")
    )

# =========================================================
# FIND AVAILABLE ROOMS
# =========================================================

@app.route("/available-rooms")
def available_rooms():

    if not session.get("admin_logged_in"):
        return jsonify({
            "success": False,
            "rooms": [],
            "error": "Admin login required."
        }), 401

    candidate_id = request.args.get(
        "candidate_id",
        ""
    ).strip()

    interview_date = request.args.get(
        "interview_date",
        ""
    ).strip()

    starting_time = request.args.get(
        "starting_time",
        ""
    ).strip()

    try:

        buffer_time = int(
            request.args.get(
                "buffer_time",
                15
            )
        )

        aptitude_duration = int(
            request.args.get(
                "aptitude_duration",
                30
            )
        )

        technical_duration = int(
            request.args.get(
                "technical_duration",
                40
            )
        )

        managerial_duration = int(
            request.args.get(
                "managerial_duration",
                30
            )
        )

        hr_duration = int(
            request.args.get(
                "hr_duration",
                20
            )
        )

    except ValueError:

        return jsonify({
            "success": False,
            "rooms": []
        })

    selected_candidate = find_candidate(
        candidate_id
    )

    if selected_candidate is None:

        return jsonify({
            "success": False,
            "rooms": []
        })

    if (
        not interview_date
        or
        not starting_time
    ):

        return jsonify({
            "success": False,
            "rooms": []
        })

    try:

        times = calculate_interview_times(
            interview_date,
            starting_time,
            buffer_time,
            aptitude_duration,
            technical_duration,
            managerial_duration,
            hr_duration
        )

    except ValueError:

        return jsonify({
            "success": False,
            "rooms": []
        })

    start_datetime = (
        times["start_datetime"]
    )

    end_datetime = (
        times["round4_end"]
    )

    reschedule = (
        request.args.get(
            "reschedule",
            "0"
        ) == "1"
    )

    ignore_candidate_id = None

    if reschedule:

        ignore_candidate_id = (
            selected_candidate["id"]
        )

    available = []

    print()
    print("=" * 55)
    print("          ROOM AVAILABILITY CHECK")
    print("=" * 55)

    print(
        f"Candidate ID : {selected_candidate['id']}"
    )

    print(
        f"Candidate    : {selected_candidate['name']}"
    )

    print(
        f"Date         : "
        f"{start_datetime.strftime('%d %B %Y')}"
    )

    print(
        f"Start Time   : "
        f"{start_datetime.strftime('%I:%M %p')}"
    )

    print(
        f"Session      : "
        f"{start_datetime.strftime('%I:%M %p')} - "
        f"{end_datetime.strftime('%I:%M %p')}"
    )

    print("-" * 55)

    for room in ROOMS:

        available_status = room_is_available(
            room,
            interview_date,
            start_datetime,
            end_datetime,
            ignore_candidate_id
        )

        if available_status:

            available.append(room)

            print(
                f"{room:<20} : AVAILABLE"
            )

        else:

            print(
                f"{room:<20} : UNAVAILABLE"
            )

    print("-" * 55)

    if available:

        print(
            f"STATUS       : {len(available)} ROOM(S) AVAILABLE"
        )

    else:

        print(
            "STATUS       : NO ROOMS AVAILABLE"
        )

    print("=" * 55)
    print()

    return jsonify({

        "success": True,

        "rooms": available,

        "session_start":
            start_datetime.strftime(
                "%I:%M %p"
            ),

        "session_end":
            end_datetime.strftime(
                "%I:%M %p"
            )
    })


# =========================================================
# BOOK ROOM
# =========================================================

@app.route(
    "/book-room",
    methods=["POST"]
)
def book_room():

    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    candidate_id = request.form.get(
        "candidate_id",
        ""
    ).strip()

    interview_date = request.form.get(
        "interview_date",
        ""
    ).strip()

    starting_time = request.form.get(
        "starting_time",
        ""
    ).strip()

    selected_room = request.form.get(
        "selected_room",
        ""
    ).strip()

    reschedule = (
        request.form.get(
            "reschedule",
            "0"
        ) == "1"
    )

    selected_candidate = find_candidate(
        candidate_id
    )

    if selected_candidate is None:

        print()
        print("=" * 55)
        print("             BOOKING ERROR")
        print("=" * 55)
        print("STATUS       : CANDIDATE NOT FOUND")
        print("=" * 55)
        print()

        return redirect(
            url_for("admin")
        )

    if selected_room not in ROOMS:

        print()
        print("=" * 55)
        print("             BOOKING ERROR")
        print("=" * 55)
        print(f"Candidate ID : {candidate_id}")
        print(f"Selected Room: {selected_room}")
        print("STATUS       : INVALID ROOM")
        print("=" * 55)
        print()

        return redirect(
            url_for("admin")
        )

    try:

        buffer_time = int(
            request.form.get(
                "buffer_time",
                15
            )
        )

        number_of_candidates = int(
            request.form.get(
                "number_of_candidates",
                1
            )
        )

        aptitude_duration = int(
            request.form.get(
                "aptitude_duration",
                30
            )
        )

        technical_duration = int(
            request.form.get(
                "technical_duration",
                40
            )
        )

        managerial_duration = int(
            request.form.get(
                "managerial_duration",
                30
            )
        )

        hr_duration = int(
            request.form.get(
                "hr_duration",
                20
            )
        )

    except ValueError:

        return redirect(
            url_for("admin")
        )

    try:

        times = calculate_interview_times(
            interview_date,
            starting_time,
            buffer_time,
            aptitude_duration,
            technical_duration,
            managerial_duration,
            hr_duration
        )

    except ValueError:

        return redirect(
            url_for("admin")
        )

    start_datetime = (
        times["start_datetime"]
    )

    end_datetime = (
        times["round4_end"]
    )

    ignore_candidate_id = None

    if reschedule:

        ignore_candidate_id = (
            selected_candidate["id"]
        )

    # =====================================================
    # FINAL ROOM AVAILABILITY CHECK
    # =====================================================

    if not room_is_available(
        selected_room,
        interview_date,
        start_datetime,
        end_datetime,
        ignore_candidate_id
    ):

        print()
        print("=" * 55)
        print("             BOOKING FAILED")
        print("=" * 55)
        print(
            f"Candidate ID : "
            f"{selected_candidate['id']}"
        )
        print(
            f"Candidate    : "
            f"{selected_candidate['name']}"
        )
        print(
            f"Date         : "
            f"{start_datetime.strftime('%d %B %Y')}"
        )
        print(
            f"Start Time   : "
            f"{start_datetime.strftime('%I:%M %p')}"
        )
        print(
            f"Room         : {selected_room}"
        )
        print(
            "STATUS       : ROOM ALREADY OCCUPIED"
        )
        print("=" * 55)
        print()

        return redirect(
            url_for("admin")
        )

    # =====================================================
    # BOOKING LOG
    # =====================================================

    print()
    print("=" * 55)

    if reschedule:

        print("          INTERVIEW RESCHEDULING")

    else:

        print("             INTERVIEW BOOKING")

    print("=" * 55)

    print(
        f"Candidate ID : "
        f"{selected_candidate['id']}"
    )

    print(
        f"Candidate    : "
        f"{selected_candidate['name']}"
    )

    print(
        f"Email        : "
        f"{selected_candidate['email']}"
    )

    print(
        f"Date         : "
        f"{start_datetime.strftime('%d %B %Y')}"
    )

    print(
        f"Start Time   : "
        f"{start_datetime.strftime('%I:%M %p')}"
    )

    print(
        f"Reporting    : "
        f"{times['reporting_datetime'].strftime('%I:%M %p')}"
    )

    print(
        f"Room         : {selected_room}"
    )

    print(
        f"Session      : "
        f"{start_datetime.strftime('%I:%M %p')} - "
        f"{end_datetime.strftime('%I:%M %p')}"
    )

    print("-" * 55)

    print(
        f"Round 1      : "
        f"{times['round1_start'].strftime('%I:%M %p')} - "
        f"{times['round1_end'].strftime('%I:%M %p')}"
    )

    print(
        f"Buffer 1     : "
        f"{times['break1_start'].strftime('%I:%M %p')} - "
        f"{times['break1_end'].strftime('%I:%M %p')}"
    )

    print(
        f"Round 2      : "
        f"{times['round2_start'].strftime('%I:%M %p')} - "
        f"{times['round2_end'].strftime('%I:%M %p')}"
    )

    print(
        f"Buffer 2     : "
        f"{times['break2_start'].strftime('%I:%M %p')} - "
        f"{times['break2_end'].strftime('%I:%M %p')}"
    )

    print(
        f"Round 3      : "
        f"{times['round3_start'].strftime('%I:%M %p')} - "
        f"{times['round3_end'].strftime('%I:%M %p')}"
    )

    print(
        f"Buffer 3     : "
        f"{times['break3_start'].strftime('%I:%M %p')} - "
        f"{times['break3_end'].strftime('%I:%M %p')}"
    )

    print(
        f"Round 4      : "
        f"{times['round4_start'].strftime('%I:%M %p')} - "
        f"{times['round4_end'].strftime('%I:%M %p')}"
    )

    # =====================================================
# SAVE SCHEDULE TO SUPABASE
# =====================================================

    schedule_data = {

        "candidate_id": selected_candidate["id"],

        "date": interview_date,

        "formatted_date": start_datetime.strftime(
            "%d %B %Y"
        ),

        "weekday": start_datetime.strftime(
            "%A"
        ),

        "starting_time": start_datetime.strftime(
            "%I:%M %p"
        ),

        "starting_time_raw": starting_time,

        "reporting_time": times[
            "reporting_datetime"
        ].strftime(
            "%I:%M %p"
        ),

        "reporting_date": times[
            "reporting_datetime"
        ].strftime(
            "%d %B %Y"
        ),

        "room": selected_room,

        "session_start_raw": start_datetime.strftime(
            "%Y-%m-%d %H:%M"
        ),

        "session_end_raw": end_datetime.strftime(
            "%Y-%m-%d %H:%M"
        ),

        "session_start": start_datetime.strftime(
            "%I:%M %p"
        ),

        "session_end": end_datetime.strftime(
            "%I:%M %p"
        ),

        "buffer_time": buffer_time,

        "number_of_candidates": number_of_candidates,

        "aptitude_duration": aptitude_duration,

        "technical_duration": technical_duration,

        "managerial_duration": managerial_duration,

        "hr_duration": hr_duration,

        "round1_start": times[
            "round1_start"
        ].strftime("%I:%M %p"),

        "round1_end": times[
            "round1_end"
        ].strftime("%I:%M %p"),

        "break1_start": times[
            "break1_start"
        ].strftime("%I:%M %p"),

        "break1_end": times[
            "break1_end"
        ].strftime("%I:%M %p"),

        "round2_start": times[
            "round2_start"
        ].strftime("%I:%M %p"),

        "round2_end": times[
            "round2_end"
        ].strftime("%I:%M %p"),

        "break2_start": times[
            "break2_start"
        ].strftime("%I:%M %p"),

        "break2_end": times[
            "break2_end"
        ].strftime("%I:%M %p"),

        "round3_start": times[
            "round3_start"
        ].strftime("%I:%M %p"),

        "round3_end": times[
            "round3_end"
        ].strftime("%I:%M %p"),

        "break3_start": times[
            "break3_start"
        ].strftime("%I:%M %p"),

        "break3_end": times[
            "break3_end"
        ].strftime("%I:%M %p"),

        "round4_start": times[
            "round4_start"
        ].strftime("%I:%M %p"),

        "round4_end": times[
            "round4_end"
        ].strftime("%I:%M %p")
    }

    supabase.table(
        "interview_schedules"
    ).upsert(
        schedule_data,
        on_conflict="candidate_id"
    ).execute()

    supabase.table(
        "candidates"
    ).update({
        "status": "Scheduled"
    }).eq(
        "id",
        selected_candidate["id"]
    ).execute()

    # =====================================================
    # UPDATE CANDIDATE STATUS
    # =====================================================

    supabase.table(
    "candidates"
).update({
    "status": "Scheduled"
}).eq(
    "id",
    selected_candidate["id"]
).execute()
    print("-" * 55)
    print("STATUS       : BOOKED SUCCESSFULLY")
    print("=" * 55)
    print()

    return redirect(
        url_for("admin")
    )


# =========================================================
# RUN FLASK
# =========================================================

if __name__ == "__main__":

    print()
    print("=" * 55)
    print("              INTERVIEWFLOW")
    print("=" * 55)
    print("Database      : interviewflow.db")
    print("Rooms         : 4")
    print("Server        : http://127.0.0.1:5000")
    print("Admin         : http://127.0.0.1:5000/admin")
    print("Candidate     : http://127.0.0.1:5000/candidate")
    print("=" * 55)
    print()

    app.run(
        debug=True
    )