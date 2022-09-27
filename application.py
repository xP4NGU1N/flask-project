import os

import sqlite3 as lite
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from flask_mail import Mail, Message
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
from datetime import datetime


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("email") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


# Configure application
app = Flask(__name__)
# configure email
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_DEFAULT_SENDER"] = "connectnotice50@gmail.com"
app.config["MAIL_USERNAME"] = "connectnotice50@gmail.com"
app.config["MAIL_PASSWORD"] = "Computer1!"
mail = Mail(app)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure to SQLite database
db = lite.connect("connect.db")

# List of hobbies
HOBBIES = ["Badminton", "Cycling", "Fishing", "Golf", "Running", "Soccer", "Tennis"]


@app.route("/register", methods=["GET", "POST"])
def register():
    """register user"""

    # link user to registration page
    if request.method == "GET":
        return render_template("register.html")

    # after user enters registration page and fills up details
    if request.method == "POST":
        email = request.form.get("email")
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # data validation
        if not email:
            flash("Input an email.")
            render_template("register.html")
        if "@gmail.com" not in email:
            flash("Invalid gmail account.")
            return render_template("register.html")
        email_count = db.execute("SELECT * FROM users WHERE email = ?", email)
        if len(email_count) != 0:
            flash("Email already taken.")
            return render_template("register.html")
        if not username:
            flash("Input a username.")
            return render_template("register.html")
        username_count = db.execute("SELECT * FROM users WHERE username = ?", username)
        if len(username_count) != 0:
            flash("Username already taken.")
            return render_template("register.html")
        if not password:
            flash("Input a password.")
            return render_template("register.html")
        if not confirmation:
            flash("Confirm password.")
            return render_template("register.html")
        if confirmation != password:
            flash("Passwords do not match, confirm again.")
            return render_template("register.html")

        # generate hash
        hash = generate_password_hash(password, method="pbkdf2:sha256", salt_length=8)

        # update main database with user's login information
        db.execute("INSERT INTO users (username, hash, email) VALUES (?, ?, ?)", username, hash, email)

        # return to login page
        flash("Account registered.")
        return redirect("/")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any email
    session.clear()

    # link to log-in page
    if request.method == "GET":
        return render_template("login.html")

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # data validation
        if not request.form.get("username"):
            flash("Must provide username")
            return render_template("login.html")
        elif not request.form.get("password"):
            flash("Must provide password")
            return render_template("login.html")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            flash("Invalid username/password")
            return render_template("login.html")

        # Remember which user has logged in
        session["email"] = rows[0]["email"]
        session["username"] = rows[0]["username"]

        # Redirect user to home page
        return redirect("/")


@app.route("/")
@login_required
def index():
    """Show user's hobby, signed up events, upcoming events with option to join"""

    # user's homepage
    welcome_user = db.execute("SELECT username FROM users WHERE email = ?", session["email"])

    # refresh and check if event is over
    db.execute("DELETE FROM participant WHERE event_id IN (SELECT event_id FROM activities WHERE date < (SELECT date('now')))")
    db.execute("DELETE FROM activities WHERE date < (SELECT date('now'))")

    # create table to show upcoming events
    participants = db.execute(
        "SELECT * FROM activities WHERE event_id IN (SELECT event_id FROM participant WHERE username = ?) ORDER BY date ASC", session["username"])
    if len(participants) == 0:
        flash("No upcoming events, join one now!")
        return redirect("/events")
    return render_template("index.html", welcome_user=welcome_user[0]["username"], participants=participants)


@app.route("/for_you")
@login_required
def for_you():
    """Identify user's interest and suggest similar events to join"""

    hobby_count = db.execute(
        "SELECT hobby, count(hobby) AS count FROM participant WHERE email = ? GROUP BY hobby ORDER BY count DESC, hobby ASC", session["email"])

    # no data to generate information
    if len(hobby_count) == 0:
        flash("Let's explore some events first!")
        return redirect("/events")

    else:
        main_interest = hobby_count[0]["hobby"]

        if len(hobby_count) > 1:
            sub_interest = hobby_count[1]["hobby"]

        else:
            sub_interest = ""

        # show user events based on the user's most registered hobby
        more_events = db.execute(
            "SELECT * FROM activities WHERE hobby = ? AND event_id NOT IN (SELECT event_id FROM participant WHERE email = ?) ORDER BY hobby ASC, date ASC", main_interest, session["email"])
        return render_template("for_you.html", welcome_user=session["username"], activities=more_events, sub_interest=sub_interest)


@app.route("/events", methods=["GET", "POST"])
@login_required
def events():
    """Search for all upcoming events via hobby, able to view participating members and join"""

    # load every event
    all_activities = db.execute(
        "SELECT email, event_id, hobby, location, date, participant_count, organiser, comment, max, equipment FROM activities GROUP BY event_id ORDER BY hobby, date ASC")

    # link to event page
    if request.method == "GET":

        # display every event
        return render_template("events.html", activities=all_activities, hobbies=HOBBIES, hobby="All")

    # when user submits filter request
    if request.method == "POST":
        hobby = request.form.get("hobby")

        # data validation
        if not hobby:
            flash("Select hobby.")
            return render_template("events.html", activities=all_activities, hobbies=HOBBIES, hobby="All")
        if hobby not in HOBBIES:
            flash("Select hobby from dropdown list.")
            return render_template("events.html", activities=all_activities, hobbies=HOBBIES, hobby="All")

        # filter events by hobby
        filtered = db.execute(
            "SELECT email, event_id, hobby, location, date, participant_count, organiser, comment, max, equipment FROM activities WHERE hobby = ? GROUP BY event_id ORDER BY date ASC", hobby)
        return render_template("events.html", activities=filtered, hobby=hobby, hobbies=HOBBIES)


@app.route("/join_event", methods=["POST"])
@login_required
def join_event():
    """let user join events, send email to them upon confirmation"""

    # user requests to join event
    if request.method == "POST":
        # event details
        event_id = request.form.get("event_id")
        participant_count = int(request.form.get("participant_count"))
        max_participant = int(request.form.get("max"))
        hobby = request.form.get("hobby")
        location = request.form.get("location")
        date = request.form.get("date")

        # data validation
        check_join = db.execute("SELECT * FROM participant WHERE event_id = ? AND email = ?", event_id, session["email"])
        if len(check_join) != 0:
            flash("You already joined this event.")
            return redirect("/events")
        if participant_count == max_participant:
            flash("Sorry, event is fully booked.")
            return redirect("/events")

        # update participant list and count
        else:
            db.execute("UPDATE activities SET participant_count = ? WHERE event_id = ?", participant_count + 1, event_id)
            db.execute("INSERT INTO participant (event_id, username, email, hobby) VALUES (?, ?, ?, ?)",
                       event_id, session["username"], session["email"], hobby)

        email = session["email"]
        message = Message(subject="Event Confirmation", recipients=[email],
                          html="<h2>You have successfully registered for an event on Connect.</h2><hr><h3>Event: {}<br>Location: {}<br>Date: {}</h3>".format(hobby, location, date))
        mail.send(message)
        flash("Successfully joined event.")
        return redirect("/")


@app.route("/withdraw", methods=["POST"])
@login_required
def cancel():
    """let user cancel events, send email to them upon confirmation"""

    # user submits withdrawal request
    event_id = request.form.get("event_id")
    participant_count = int(request.form.get("participant_count"))
    organiser = request.form.get("organiser")

    # if event has no participants after withdrawal
    if participant_count == 1:
        db.execute("DELETE FROM activities WHERE event_id = ?", event_id)
        db.execute("DELETE FROM participant WHERE username = ? AND event_id = ?", session["username"], event_id)
        flash("Event Cancelled.")
        return redirect("/")

    # remove participant
    else:
        db.execute("DELETE FROM participant WHERE username = ? AND event_id = ?", session["username"], event_id)
        db.execute("UPDATE activities SET participant_count = ? WHERE event_id = ?", participant_count - 1, event_id)
        flash("Sucessfully withdrawn from event.")
        return redirect("/")


@app.route("/create", methods=["GET", "POST"])
@login_required
def join():
    """let user create events"""

    # link to page
    if request.method == "GET":
        return render_template("create.html", hobbies=HOBBIES)

    # upon submitting form to create event
    if request.method == "POST":
        hobby = request.form.get("hobby")
        location = request.form.get("location")
        date = request.form.get("date")
        comment = request.form.get("comment")
        max_participant = request.form.get("max")
        equipment = request.form.get("equipment")

    # data validation
    if not hobby:
        flash("Input hobby.")
        return render_template("create.html", hobbies=HOBBIES)
    if hobby not in HOBBIES:
        flash("Select hobby from the dropdown list.")
        return render_template("create.html", hobbies=HOBBIES)
    if not location:
        flash("Input address.")
        return render_template("create.html", hobbies=HOBBIES)
    if not date:
        flash("Input date.")
        return render_template("create.html", hobbies=HOBBIES)
    db.execute("INSERT INTO date_checker (date) VALUES(?)", date)
    check_date = db.execute("SELECT * FROM date_checker WHERE date < (SELECT date('now'))")
    if len(check_date) != 0:
        flash("Invalid date.")
        db.execute("DELETE FROM date_checker")
        return render_template("create.html", hobbies=HOBBIES)
    db.execute("DELETE FROM date_checker")
    if len(comment) > 100:
        flash("Maximum 100 characters")
        return render_template("create.html", hobbies=HOBBIES)
    if not comment:
        comment = "-"
    if not max_participant:
        flash("Input maximum group size.")
        return render_template("create.html", hobbies=HOBBIES)
    if int(max_participant) < 2:
        flash("Invalid group size.")
        return render_template("create.html", hobbies=HOBBIES)
    if not equipment:
        flash("State if equipment provided.")
        return render_template("create.html", hobbies=HOBBIES)
    if equipment != "yes" and equipment != "Yes" and equipment != "no" and equipment != "No":
        flash("Input yes/no only under equipment provided.")
        return render_template("create.html", hobbies=HOBBIES)
    if equipment == "yes" or equipment == "Yes":
        equipment = "Provided"
    if equipment == "no" or equipment == "No":
        equipment = "Not provided"

    # obtain data and update into hobby/ event database
    organiser = db.execute("SELECT username FROM USERS WHERE email = ?", session["email"])
    db.execute("INSERT INTO activities (email, hobby, location, date, organiser, comment, max, equipment) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
               session["email"], hobby, location, date, organiser[0]["username"], comment, max_participant, equipment)

    last_line = db.execute("SELECT max(event_id) AS event_id FROM activities")
    db.execute("INSERT INTO participant (email, username, event_id, hobby) VALUES (?, ?, ?, ?)",
               session["email"], session["username"], last_line[0]["event_id"], hobby)

    # send email to creator
    email = session["email"]
    message = Message(subject="Event Created!", recipients=[email],
                      html="<h2>You have successfully created an event on Connect.</h2><hr><h3>Event: {}<br>Location: {}<br>Date: {}</h3>".format(hobby, location, date))
    mail.send(message)

    flash("Event created.")
    return redirect("/")


@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    """change password"""

    # obtain user information
    users = db.execute("SELECT * FROM users WHERE email = ?", session["email"])

    # link to change password
    if request.method == "GET":
        return render_template("change_password.html", user_username=users[0]["username"])

    # after user submits change password request
    if request.method == "POST":
        # obtain passwords
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirmation = request.form.get("confirmation")

        # data validation
        if not current_password:
            flash("Input current password.")
            return render_template("change_password.html", user_username=users[0]["username"])
        if not check_password_hash(users[0]["hash"], current_password):
            flash("Wrong password.")
            return render_template("change_password.html", user_username=users[0]["username"])
        if not new_password:
            flash("Input new password.")
            return render_template("change_password.html", user_username=users[0]["username"])
        if not confirmation:
            flash("Confirm new password.")
            return render_template("change_password.html", user_username=users[0]["username"])
        if confirmation != new_password:
            flash("Passwords do not match, confirm again.")
            return render_template("change_password.html", user_username=users[0]["username"])
        if new_password == current_password:
            flash("New password is the same as current password.")
            return render_template("change_password.html", user_username=users[0]["username"])

        else:
            # generate hash and update user's password
            hash = generate_password_hash(new_password, method="pbkdf2:sha256", salt_length=8)
            db.execute("UPDATE users SET hash = ? WHERE email = ?", hash, session["email"])

            flash("Password changed.")
            return redirect("/")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any email
    session.clear()

    # Redirect user to login form
    return redirect("/")

