from flask import Flask, render_template, request, redirect, session, jsonify
from database import add_user, process_chunk, log_in, get_summary, get_notes
import os

app = Flask(__name__)
app.secret_key = "asdf;lkjplanet1"

@app.route("/")
def home_redirect():
    if "username" in session:
        return redirect("/home")
    return redirect("/signin")

@app.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "GET":
        return render_template("signin.html")

    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    result = log_in(username, password)
    print(type(result))
    if result:
        session["username"] = username
        session["logged_in"] = True
        return jsonify({"status": "ok"})
    else:
        return jsonify({"status": "error", "message": result})

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")

    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    print(username)
    print(password)
    result = add_user(username, password)
    print(result)
    if result == "Attempt successful.":
        print("phutt1")
        session["username"] = username
        session["logged_in"] = True
        return jsonify({"status": "ok"})
    else:
        print("phutt2")
        return jsonify({"status": "error", "message": result})

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect("/signin")

@app.route("/home")
def home():
    if "username" not in session:
        return redirect("/signin")
    return render_template("home.html", username=session["username"])

@app.route("/uploadmeeting")
def upload_page():
    if request.method == "GET":
        if "username" not in session:
            return redirect("/signin")
        return render_template("uploadmeeting.html")
    

@app.route("/upload", methods=["POST"])
def upload_chunk():
    print("received request")
    try:
        # Get metadata
        username = request.form.get("username")
        print(username)
        meeting_name = request.form.get("meetingName")
        print(meeting_name)
        chunk_number = int(request.form.get("chunkNumber"))
        print(chunk_number)
        total_chunks = int(request.form.get("totalChunks"))
        print(total_chunks)

        # Get audio file bytes
        file = request.files["file"]
        audio_bytes = file.read()

        # Call DB method
        process_chunk(username, meeting_name, chunk_number, total_chunks, audio_bytes)
        print(f"received chunk {chunk_number}")

        return jsonify({
            "status": "success",
            "chunk": chunk_number
        }), 200

    except Exception as e:
        print(e)
        return jsonify({"status": "error", "message": str(e)}), 500
    
@app.route("/findmeeting", methods=["GET", "POST"])
def find_meeting():
    if request.method == "GET":
        if "username" not in session:
            return redirect("/signin")
        return render_template("findmeeting.html")

    username = request.form.get("username")
    meeting_name = request.form.get("meetingName")

    summary = get_summary(username, meeting_name)
    notes = get_notes(username, meeting_name)
    return jsonify({"summary": summary, "notes": notes})


if __name__ == "__main__":
    app.run(debug=True, port=5000)