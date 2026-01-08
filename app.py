# from flask import Flask, render_template, request, redirect, url_for, session, flash
# from utils.db import get_conn
# from utils.security import hash_password, verify_password
# import os

# app = Flask(__name__)
# app.secret_key = os.urandom(24)

# # Disable Browser Back Button Cache
# @app.after_request
# def after_request(response):
#     response.headers["Cache-Control"] = "no-store"
#     return response


# @app.route('/logout')
# def logout():
#     session.clear()
#     return redirect(url_for('login'))



# # Initialize database
# def init_db():
#     conn = get_conn()
#     cur = conn.cursor()

#     # Create tables
#     cur.executescript("""
#     CREATE TABLE IF NOT EXISTS students (
#         id INTEGER PRIMARY KEY,
#         college_id TEXT UNIQUE,
#         password_hash TEXT,
#         has_voted INTEGER DEFAULT 0
#     );

#     CREATE TABLE IF NOT EXISTS elections (
#         id INTEGER PRIMARY KEY,
#         name TEXT,
#         is_active INTEGER DEFAULT 1
#     );

#     CREATE TABLE IF NOT EXISTS candidates (
#         id INTEGER PRIMARY KEY,
#         election_id INTEGER,
#         name TEXT,
#         photo TEXT,
#         FOREIGN KEY (election_id) REFERENCES elections(id)
#     );

#     CREATE TABLE IF NOT EXISTS votes (
#         id INTEGER PRIMARY KEY,
#         election_id INTEGER,
#         candidate_id INTEGER,
#         timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
#         FOREIGN KEY (election_id) REFERENCES elections(id),
#         FOREIGN KEY (candidate_id) REFERENCES candidates(id)
#     );
#     """)

#     # Insert default data only if no election exists
#     cur.execute("SELECT COUNT(*) FROM elections")
#     if cur.fetchone()[0] == 0:

#         # Create election
#         cur.execute("INSERT INTO elections (name, is_active) VALUES (?, ?)", ("  Council of CR  2025", 1))
#         election_id = cur.lastrowid

#         # Add default candidates WITH PHOTOS
#         cur.executemany(
#             "INSERT INTO candidates (election_id, name, photo) VALUES (?, ?, ?)",
#             [
#                 (election_id, "Aman", "aman.jpg"),
#                 (election_id, "Ankit", "ankit.jpg"),
#                 (election_id, "Aayush", "aayush.jpg")
#             ]
#         )

#         # Add 64 auto-generated students
#         students = []
#         for i in range(1, 65):
#             roll = f"0905CS241{str(i).zfill(3)}"
#             password = f"{roll}#"
#             students.append((roll, hash_password(password)))

#         cur.executemany(
#             "INSERT INTO students (college_id, password_hash) VALUES (?, ?)",
#             students
#         )

#         # commit initial inserts
#         conn.commit()

#     conn.close()

# # Home
# @app.route('/')
# def home():
#     if 'student' in session:
#         return redirect(url_for('vote'))
#     return redirect(url_for('login'))

# # Register
# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     if request.method == 'POST':
#         college_id = request.form['college_id'].strip()
#         password = request.form['password']
#         confirm = request.form['confirm']

#         if password != confirm:
#             flash("Passwords do not match!", "danger")
#             return redirect(url_for('register'))

#         conn = get_conn()
#         cur = conn.cursor()

#         cur.execute("SELECT * FROM students WHERE college_id=?", (college_id,))
#         if cur.fetchone():
#             flash("College ID already registered!", "danger")
#             conn.close()
#             return redirect(url_for('register'))

#         cur.execute("INSERT INTO students (college_id, password_hash) VALUES (?, ?)",
#                     (college_id, hash_password(password)))

#         conn.commit()
#         conn.close()

#         flash("Registration successful!", "success")
#         return redirect(url_for('login'))

#     return render_template('register.html')

# # Login
# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         cid = request.form['college_id'].strip()
#         password = request.form['password']

#         conn = get_conn()
#         cur = conn.cursor()

#         cur.execute("SELECT * FROM students WHERE college_id=?", (cid,))
#         user = cur.fetchone()
#         conn.close()

#         if user and verify_password(user['password_hash'], password):
#             session['student'] = {'id': user['id'], 'college_id': cid}
#             return redirect(url_for('vote'))

#         flash("Invalid credentials!", "danger")
#         return redirect(url_for('login'))

#     return render_template('login.html')

# # Vote
# @app.route('/vote', methods=['GET', 'POST'])
# def vote():
#     if 'student' not in session:
#         return redirect(url_for('login'))

#     sid = session['student']['id']

#     conn = get_conn()
#     cur = conn.cursor()

#     # Get active election
#     cur.execute("SELECT * FROM elections WHERE is_active=1")
#     election = cur.fetchone()

#     if not election:
#         conn.close()
#         return "No active election", 404

#     # Check if student has already voted
#     cur.execute("SELECT has_voted FROM students WHERE id=?", (sid,))
#     row = cur.fetchone()
#     has_voted = bool(row['has_voted']) if row else False

#     # Handle vote submit
#     if request.method == 'POST':
#         if has_voted:
#             conn.close()
#             return redirect(url_for('thanks'))

#         candidate_id_raw = request.form.get('candidate')
#         if not candidate_id_raw:
#             flash("Please select a candidate.", "danger")
#             conn.close()
#             return redirect(url_for('vote'))

#         try:
#             candidate_id = int(candidate_id_raw)
#         except ValueError:
#             flash("Invalid candidate selection.", "danger")
#             conn.close()
#             return redirect(url_for('vote'))

#         # Validate candidate belongs to active election
#         cur.execute(
#             "SELECT id FROM candidates WHERE id=? AND election_id=?",
#             (candidate_id, election['id'])
#         )
#         candidate_ok = cur.fetchone()
#         if not candidate_ok:
#             flash("Invalid candidate!", "danger")
#             conn.close()
#             return redirect(url_for('vote'))

#         try:
#             # Save vote
#             cur.execute(
#                 "INSERT INTO votes (election_id, candidate_id) VALUES (?, ?)",
#                 (election['id'], candidate_id)
#             )
#             cur.execute("UPDATE students SET has_voted=1 WHERE id=?", (sid,))
#             conn.commit()
#         except Exception as e:
#             conn.rollback()
#             flash("Error saving vote. Try again.", "danger")
#             conn.close()
#             return redirect(url_for('vote'))

#         conn.close()
#         return redirect(url_for('thanks'))

#     # Load all candidates (photo included)
#     cur.execute(
#         "SELECT id, name, photo FROM candidates WHERE election_id=?",
#         (election['id'],)
#     )
#     candidates = cur.fetchall()

#     conn.close()
#     return render_template('vote.html', election=election, candidates=candidates, has_voted=has_voted)


# @app.route('/fixphotos')
# def fixphotos():
#     conn = get_conn()
#     cur = conn.cursor()

#     cur.execute("UPDATE candidates SET photo='aman.jpg' WHERE name='Aman'")
#     cur.execute("UPDATE candidates SET photo='ankit.jpg' WHERE name='Ankit'")
#     cur.execute("UPDATE candidates SET photo='aayush.jpg' WHERE name='Aayush'")

#     conn.commit()
#     conn.close()
#     return "Photos updated!"


# @app.route('/thanks')
# def thanks():
#     return render_template('thanks.html')


# # Admin route
# ADMIN_PASS = "THANOSKHANSHARMA"

# @app.route('/admin', methods=['GET', 'POST'])
# def admin():

#     # ---------- ADMIN LOGIN ----------
#     if request.method == 'POST' and 'admin_login' in request.form:
#         if request.form['password'] == ADMIN_PASS:
#             session['admin'] = True
#             return redirect(url_for('admin'))
#         flash("Wrong admin password", "danger")
#         return redirect(url_for('admin'))

#     # If admin not logged in → show login
#     if 'admin' not in session:
#         return render_template('admin.html', logged_in=False)

#     # ---------- ADMIN LOGGED IN ----------
#     conn = get_conn()
#     cur = conn.cursor()

#     # ---------- CREATE ELECTION ----------
#     if request.method == 'POST' and 'create_election' in request.form:
#         name = request.form.get('election_name', '').strip()

#         if name == "":
#             flash("Election name cannot be empty!", "danger")
#         else:
#             try:
#                 cur.execute(
#                     "INSERT INTO elections (name, is_active) VALUES (?, 1)",
#                     (name,)
#                 )
#                 conn.commit()
#                 flash("Election created successfully!", "success")
#             except:
#                 conn.rollback()
#                 flash("Error creating election!", "danger")

#     # ---------- ADD CANDIDATE ----------
#     if request.method == 'POST' and 'add_candidate' in request.form:
#         eid = request.form.get('election_id')
#         cname = request.form.get('candidate_name', '').strip()

#         if not eid:
#             flash("Select an election!", "danger")
#         else:
#             try:
#                 eid_int = int(eid)
#             except:
#                 flash("Invalid election!", "danger")
#                 eid_int = None

#             if eid_int and cname != "":
#                 # check duplicate
#                 cur.execute(
#                     "SELECT id FROM candidates WHERE election_id=? AND name=?",
#                     (eid_int, cname)
#                 )
#                 if cur.fetchone():
#                     flash("Candidate already exists!", "danger")
#                 else:
#                     cur.execute(
#                         "INSERT INTO candidates (election_id, name, photo) VALUES (?, ?, ?)",
#                         (eid_int, cname, "default.png")
#                     )
#                     conn.commit()
#                     flash("Candidate added!", "success")

#     # ---------- LOAD ELECTIONS ----------
#     cur.execute("SELECT * FROM elections ORDER BY id DESC")
#     elections = cur.fetchall()

#     # ---------- LOAD RESULTS ----------
#     results = {}
#     for e in elections:
#         cur.execute("""
#             SELECT c.id, c.name, c.photo, COUNT(v.id) AS votes
#             FROM candidates c
#             LEFT JOIN votes v ON c.id = v.candidate_id
#             WHERE c.election_id=?
#             GROUP BY c.id
#             ORDER BY votes DESC
#         """, (e['id'],))
#         results[e['name']] = cur.fetchall()

#     # ---------- STUDENTS ----------
#     cur.execute("SELECT college_id, has_voted FROM students")
#     students = cur.fetchall()

#     conn.close()

#     return render_template(
#         'admin.html',
#         logged_in=True,
#         elections=elections,
#         results=results,
#         students=students
#     )


# # ---------------- DELETE CANDIDATE ROUTE ----------------
# @app.route('/delete_candidate/<int:cid>', methods=['POST'])
# def delete_candidate(cid):
#     if 'admin' not in session:
#         return redirect(url_for('admin'))

#     conn = get_conn()
#     cur = conn.cursor()

#     # delete votes first
#     cur.execute("DELETE FROM votes WHERE candidate_id=?", (cid,))

#     # delete candidate
#     cur.execute("DELETE FROM candidates WHERE id=?", (cid,))

#     conn.commit()
#     conn.close()

#     flash("Candidate deleted successfully!", "success")
#     return redirect(url_for('admin'))
# # Run app

# if __name__ == '__main__':
#     # ensure DB exists
#     init_db()
#     app.run(debug=True)



















# from flask import Flask, render_template, request, redirect, url_for, session, flash
# from utils.db import get_conn
# from utils.security import hash_password, verify_password
# from datetime import datetime, timedelta
# import os

# app = Flask(__name__)
# app.secret_key = os.urandom(24)

# # Disable Browser Back Button Cache
# @app.after_request
# def after_request(response):
#     response.headers["Cache-Control"] = "no-store"
#     return response


# @app.route('/logout')
# def logout():
#     session.clear()
#     return redirect(url_for('login'))


# # ---------------- INITIALIZE DATABASE ----------------
# def init_db():
#     conn = get_conn()
#     cur = conn.cursor()

#     # TABLES
#     cur.executescript("""
#     CREATE TABLE IF NOT EXISTS students (
#         id INTEGER PRIMARY KEY,
#         college_id TEXT UNIQUE,
#         password_hash TEXT,
#         has_voted INTEGER DEFAULT 0
#     );

#     CREATE TABLE IF NOT EXISTS elections (
#         id INTEGER PRIMARY KEY,
#         name TEXT,
#         is_active INTEGER DEFAULT 1,
#         start_time TEXT,
#         end_time TEXT
#     );

#     CREATE TABLE IF NOT EXISTS candidates (
#         id INTEGER PRIMARY KEY,
#         election_id INTEGER,
#         name TEXT,
#         photo TEXT,
#         FOREIGN KEY (election_id) REFERENCES elections(id)
#     );

#     CREATE TABLE IF NOT EXISTS votes (
#         id INTEGER PRIMARY KEY,
#         election_id INTEGER,
#         candidate_id INTEGER,
#         timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
#         FOREIGN KEY (election_id) REFERENCES elections(id),
#         FOREIGN KEY (candidate_id) REFERENCES candidates(id)
#     );
#     """)

#     # ---- SEED DATA (CRITICAL FIX) ----
#     cur.execute("SELECT COUNT(*) FROM elections")
#     if cur.fetchone()[0] == 0:

#         duration = int(request.form.get('duration'))
# start = datetime.now()
# end = start + timedelta(minutes=duration)


#         # Create default election
#         cur.execute(
#             "INSERT INTO elections (name, is_active, start_time, end_time) VALUES (?,1,?,?)",
#             ("Council of CR 2025", start.isoformat(), end.isoformat())
#         )
#         election_id = cur.lastrowid

#         # Default candidates
#         cur.executemany(
#             "INSERT INTO candidates (election_id, name, photo) VALUES (?, ?, ?)",
#             [
#                 (election_id, "Aman", "aman.jpg"),
#                 (election_id, "Ankit", "ankit.jpg"),
#                 (election_id, "Aayush", "aayush.jpg")
#             ]
#         )

#         # 64 students
#         students = []
#         for i in range(1, 65):
#             roll = f"0905CS241{str(i).zfill(3)}"
#             students.append((roll, hash_password(f"{roll}#")))

#         cur.executemany(
#             "INSERT INTO students (college_id, password_hash) VALUES (?, ?)",
#             students
#         )

#         conn.commit()

#     conn.close()


# # ---------------- HOME ----------------
# @app.route('/')
# def home():
#     if 'student' in session:
#         return redirect(url_for('vote'))
#     return redirect(url_for('login'))


# # ---------------- REGISTER ----------------
# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     if request.method == 'POST':
#         cid = request.form['college_id'].strip()
#         pwd = request.form['password']
#         confirm = request.form['confirm']

#         if pwd != confirm:
#             flash("Passwords do not match!", "danger")
#             return redirect(url_for('register'))

#         conn = get_conn()
#         cur = conn.cursor()

#         cur.execute("SELECT id FROM students WHERE college_id=?", (cid,))
#         if cur.fetchone():
#             flash("College ID already registered!", "danger")
#             conn.close()
#             return redirect(url_for('register'))

#         cur.execute(
#             "INSERT INTO students (college_id, password_hash) VALUES (?, ?)",
#             (cid, hash_password(pwd))
#         )

#         conn.commit()
#         conn.close()
#         flash("Registration successful!", "success")
#         return redirect(url_for('login'))

#     return render_template('register.html')


# # ---------------- LOGIN ----------------
# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         cid = request.form['college_id'].strip()
#         pwd = request.form['password']

#         conn = get_conn()
#         cur = conn.cursor()
#         cur.execute("SELECT * FROM students WHERE college_id=?", (cid,))
#         user = cur.fetchone()
#         conn.close()

#         if user and verify_password(user['password_hash'], pwd):
#             session['student'] = {'id': user['id'], 'college_id': cid}
#             return redirect(url_for('vote'))

#         flash("Invalid credentials!", "danger")

#     return render_template('login.html')


# # ---------------- VOTE ----------------
# @app.route('/vote', methods=['GET', 'POST'])
# def vote():
#     if 'student' not in session:
#         return redirect(url_for('login'))

#     sid = session['student']['id']

#     conn = get_conn()
#     cur = conn.cursor()

#     cur.execute("SELECT * FROM elections WHERE is_active=1")
#     election = cur.fetchone()

#     if not election:
#         conn.close()
#         return "No active election", 404

#     # Voting window
#     now = datetime.now()
#     start = datetime.fromisoformat(election['start_time'])
#     end = datetime.fromisoformat(election['end_time'])
#     voting_open = start <= now <= end

#     cur.execute("SELECT has_voted FROM students WHERE id=?", (sid,))
#     has_voted = bool(cur.fetchone()['has_voted'])

#     if request.method == 'POST':

#         if not voting_open:
#             flash("Voting is closed!", "danger")
#             conn.close()
#             return redirect(url_for('vote'))

#         if has_voted:
#             conn.close()
#             return redirect(url_for('thanks'))

#         candidate_id = int(request.form.get('candidate'))

#         cur.execute(
#             "INSERT INTO votes (election_id, candidate_id) VALUES (?, ?)",
#             (election['id'], candidate_id)
#         )
#         cur.execute("UPDATE students SET has_voted=1 WHERE id=?", (sid,))
#         conn.commit()
#         conn.close()

#         return redirect(url_for('thanks'))

#     cur.execute(
#         "SELECT id, name, photo FROM candidates WHERE election_id=?",
#         (election['id'],)
#     )
#     candidates = cur.fetchall()
#     conn.close()

#     return render_template(
#         'vote.html',
#         election=election,
#         candidates=candidates,
#         has_voted=has_voted,
#         voting_open=voting_open
#     )


# @app.route('/thanks')
# def thanks():
#     return render_template('thanks.html')


# # ---------------- ADMIN ----------------
# ADMIN_PASS = "THANOSKHANSHARMA"

# @app.route('/admin', methods=['GET', 'POST'])
# def admin():

#     if request.method == 'POST' and 'admin_login' in request.form:
#         if request.form['password'] == ADMIN_PASS:
#             session['admin'] = True
#             return redirect(url_for('admin'))
#         flash("Wrong admin password", "danger")

#     if 'admin' not in session:
#         return render_template('admin.html', logged_in=False)

#     conn = get_conn()
#     cur = conn.cursor()

#     # Create election manually
#     if request.method == 'POST' and 'create_election' in request.form:
#         name = request.form.get('election_name', '').strip()
#         start = datetime.now()
#         end = start + timedelta(minutes=30)

#         cur.execute(
#             "INSERT INTO elections (name, is_active, start_time, end_time) VALUES (?,1,?,?)",
#             (name, start.isoformat(), end.isoformat())
#         )
#         conn.commit()
#         flash("Election created (30 minutes)", "success")

#     cur.execute("SELECT * FROM elections ORDER BY id DESC")
#     elections = cur.fetchall()

#     results = {}
#     for e in elections:
#         cur.execute("""
#             SELECT c.id, c.name, c.photo, COUNT(v.id) AS votes
#             FROM candidates c
#             LEFT JOIN votes v ON c.id = v.candidate_id
#             WHERE c.election_id=?
#             GROUP BY c.id
#             ORDER BY votes DESC
#         """, (e['id'],))
#         results[e['name']] = cur.fetchall()

#     cur.execute("SELECT college_id, has_voted FROM students")
#     students = cur.fetchall()

#     conn.close()

#     return render_template(
#         'admin.html',
#         logged_in=True,
#         elections=elections,
#         results=results,
#         students=students
#     )

# @app.route('/results/<int:election_id>')
# def results_page(election_id):

#     conn = get_conn()
#     cur = conn.cursor()

#     cur.execute("SELECT * FROM elections WHERE id=?", (election_id,))
#     election = cur.fetchone()

#     if not election:
#         conn.close()
#         return "Election not found", 404

#     # ⛔ block results if voting still active
#     now = datetime.now()
#     end = datetime.fromisoformat(election['end_time'])

#     if now < end:
#         conn.close()
#         return "Results will be published after voting ends."

#     # fetch votes
#     cur.execute("""
#         SELECT c.id, c.name, c.photo, COUNT(v.id) AS votes
#         FROM candidates c
#         LEFT JOIN votes v ON c.id = v.candidate_id
#         WHERE c.election_id=?
#         GROUP BY c.id
#         ORDER BY votes DESC
#     """, (election_id,))

#     candidates = cur.fetchall()
#     winner = candidates[0] if candidates and candidates[0]['votes'] > 0 else None

#     conn.close()

#     return render_template(
#         "results.html",
#         election=election,
#         candidates=candidates,
#         winner=winner
#     )





# @app.route('/delete_candidate/<int:cid>', methods=['POST'])
# def delete_candidate(cid):
#     if 'admin' not in session:
#         return redirect(url_for('admin'))

#     conn = get_conn()
#     cur = conn.cursor()

#     cur.execute("DELETE FROM votes WHERE candidate_id=?", (cid,))
#     cur.execute("DELETE FROM candidates WHERE id=?", (cid,))
#     conn.commit()
#     conn.close()

#     flash("Candidate deleted successfully!", "success")
#     return redirect(url_for('admin'))


# # ---------------- RUN ----------------
# if __name__ == '__main__':
#     init_db()
#     app.run(debug=True)























































# from flask import Flask, render_template, request, redirect, url_for, session, flash
# from utils.db import get_conn
# from utils.security import hash_password, verify_password
# from datetime import datetime, timedelta
# import os

# app = Flask(__name__)
# app.secret_key = os.urandom(24)

# # Disable browser back button cache
# @app.after_request
# def after_request(response):
#     response.headers["Cache-Control"] = "no-store"
#     return response


# @app.route('/logout')
# def logout():
#     session.clear()
#     return redirect(url_for('login'))


# # ---------------- INITIALIZE DATABASE ----------------
# def init_db():
#     conn = get_conn()
#     cur = conn.cursor()

#     cur.executescript("""
#     CREATE TABLE IF NOT EXISTS students (
#         id INTEGER PRIMARY KEY,
#         college_id TEXT UNIQUE,
#         password_hash TEXT,
#         has_voted INTEGER DEFAULT 0
#     );

#     CREATE TABLE IF NOT EXISTS elections (
#         id INTEGER PRIMARY KEY,
#         name TEXT,
#         is_active INTEGER DEFAULT 1,
#         start_time TEXT,
#         end_time TEXT
#     );

#     CREATE TABLE IF NOT EXISTS candidates (
#         id INTEGER PRIMARY KEY,
#         election_id INTEGER,
#         name TEXT,
#         photo TEXT,
#         FOREIGN KEY (election_id) REFERENCES elections(id)
#     );

#     CREATE TABLE IF NOT EXISTS votes (
#         id INTEGER PRIMARY KEY,
#         election_id INTEGER,
#         candidate_id INTEGER,
#         timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
#         FOREIGN KEY (election_id) REFERENCES elections(id),
#         FOREIGN KEY (candidate_id) REFERENCES candidates(id)
#     );
#     """)

#     # Seed default election if none exist
#     cur.execute("SELECT COUNT(*) FROM elections")
#     if cur.fetchone()[0] == 0:
#         start = datetime.now()
#         end = start + timedelta(minutes=30)

#         cur.execute(
#             "INSERT INTO elections (name, is_active, start_time, end_time) VALUES (?,1,?,?)",
#             ("Council of CR 2025", start.isoformat(), end.isoformat())
#         )
#         election_id = cur.lastrowid

#         cur.executemany(
#             "INSERT INTO candidates (election_id, name, photo) VALUES (?, ?, ?)",
#             [
#                 (election_id, "Aman", "aman.jpg"),
#                 (election_id, "Ankit", "ankit.jpg"),
#                 (election_id, "Aayush", "aayush.jpg")
#             ]
#         )

#         students = []
#         for i in range(1, 65):
#             roll = f"0905CS241{str(i).zfill(3)}"
#             students.append((roll, hash_password(f"{roll}#")))

#         cur.executemany(
#             "INSERT INTO students (college_id, password_hash) VALUES (?, ?)",
#             students
#         )

#         conn.commit()

#     conn.close()


# # ---------------- AUTO-EXPIRE ELECTIONS ----------------
# def expire_elections():
#     conn = get_conn()
#     cur = conn.cursor()

#     now = datetime.now().isoformat()

#     cur.execute("""
#         UPDATE elections
#         SET is_active = 0
#         WHERE is_active = 1 AND end_time < ?
#     """, (now,))

#     conn.commit()
#     conn.close()


# # ---------------- HOME ----------------
# @app.route('/')
# def home():
#     if 'student' in session:
#         return redirect(url_for('vote'))
#     return redirect(url_for('login'))


# # ---------------- REGISTER ----------------
# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     if request.method == 'POST':
#         cid = request.form['college_id'].strip()
#         pwd = request.form['password']
#         confirm = request.form['confirm']

#         if pwd != confirm:
#             flash("Passwords do not match!", "danger")
#             return redirect(url_for('register'))

#         conn = get_conn()
#         cur = conn.cursor()

#         cur.execute("SELECT id FROM students WHERE college_id=?", (cid,))
#         if cur.fetchone():
#             flash("College ID already registered!", "danger")
#             conn.close()
#             return redirect(url_for('register'))

#         cur.execute(
#             "INSERT INTO students (college_id, password_hash) VALUES (?, ?)",
#             (cid, hash_password(pwd))
#         )

#         conn.commit()
#         conn.close()
#         flash("Registration successful!", "success")
#         return redirect(url_for('login'))

#     return render_template('register.html')


# # ---------------- LOGIN ----------------
# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         cid = request.form['college_id'].strip()
#         pwd = request.form['password']

#         conn = get_conn()
#         cur = conn.cursor()
#         cur.execute("SELECT * FROM students WHERE college_id=?", (cid,))
#         user = cur.fetchone()
#         conn.close()

#         if user and verify_password(user['password_hash'], pwd):
#             session['student'] = {'id': user['id'], 'college_id': cid}
#             return redirect(url_for('vote'))

#         flash("Invalid credentials!", "danger")

#     return render_template('login.html')


# # ---------------- VOTE ----------------
# @app.route('/vote', methods=['GET', 'POST'])
# def vote():
#     if 'student' not in session:
#         return redirect(url_for('login'))

#     # 🔄 auto-expire old elections
#     expire_elections()

#     sid = session['student']['id']
#     conn = get_conn()
#     cur = conn.cursor()

#     cur.execute("SELECT * FROM elections WHERE is_active=1")
#     election = cur.fetchone()

#     if not election:
#         conn.close()
#         return "No active election", 404

#     now = datetime.now()
#     start = datetime.fromisoformat(election['start_time'])
#     end = datetime.fromisoformat(election['end_time'])
#     voting_open = start <= now <= end

#     cur.execute("SELECT has_voted FROM students WHERE id=?", (sid,))
#     has_voted = bool(cur.fetchone()['has_voted'])

#     if request.method == 'POST':

#         if not voting_open:
#             flash("Voting is closed!", "danger")
#             conn.close()
#             return redirect(url_for('vote'))

#         if has_voted:
#             conn.close()
#             return redirect(url_for('thanks'))

#         candidate_id = int(request.form.get('candidate'))

#         cur.execute(
#             "INSERT INTO votes (election_id, candidate_id) VALUES (?, ?)",
#             (election['id'], candidate_id)
#         )
#         cur.execute("UPDATE students SET has_voted=1 WHERE id=?", (sid,))
#         conn.commit()
#         conn.close()

#         return redirect(url_for('thanks'))

#     cur.execute(
#         "SELECT id, name, photo FROM candidates WHERE election_id=?",
#         (election['id'],)
#     )
#     candidates = cur.fetchall()
#     conn.close()

#     return render_template(
#         'vote.html',
#         election=election,
#         candidates=candidates,
#         has_voted=has_voted,
#         voting_open=voting_open
#     )


# @app.route('/thanks')
# def thanks():
#     return render_template('thanks.html')


# # ---------------- ADMIN ----------------
# ADMIN_PASS = "THANOSKHANSHARMA"

# @app.route('/admin', methods=['GET', 'POST'])
# def admin():

#     if request.method == 'POST' and 'admin_login' in request.form:
#         if request.form['password'] == ADMIN_PASS:
#             session['admin'] = True
#             return redirect(url_for('admin'))
#         flash("Wrong admin password", "danger")

#     if 'admin' not in session:
#         return render_template('admin.html', logged_in=False)

#     # 🔄 auto-expire old elections
#     expire_elections()

#     conn = get_conn()
#     cur = conn.cursor()

#     if request.method == 'POST' and 'create_election' in request.form:
#         name = request.form.get('election_name').strip()
#         duration = int(request.form.get('duration'))

#         start = datetime.now()
#         end = start + timedelta(minutes=duration)

#         cur.execute(
#             "INSERT INTO elections (name, is_active, start_time, end_time) VALUES (?,1,?,?)",
#             (name, start.isoformat(), end.isoformat())
#         )
#         conn.commit()
#         flash(f"Election created ({duration} minutes)", "success")

#     cur.execute("SELECT * FROM elections ORDER BY id DESC")
#     elections = cur.fetchall()

#     results = {}
#     for e in elections:
#         cur.execute("""
#             SELECT c.id, c.name, c.photo, COUNT(v.id) AS votes
#             FROM candidates c
#             LEFT JOIN votes v ON c.id = v.candidate_id
#             WHERE c.election_id=?
#             GROUP BY c.id
#             ORDER BY votes DESC
#         """, (e['id'],))
#         results[e['name']] = cur.fetchall()

#     cur.execute("SELECT college_id, has_voted FROM students")
#     students = cur.fetchall()

#     conn.close()

#     return render_template(
#         'admin.html',
#         logged_in=True,
#         elections=elections,
#         results=results,
#         students=students
#     )


# # ---------------- RESULTS ----------------
# @app.route('/results/<int:election_id>')
# def results_page(election_id):

#     conn = get_conn()
#     cur = conn.cursor()

#     cur.execute("SELECT * FROM elections WHERE id=?", (election_id,))
#     election = cur.fetchone()

#     if not election:
#         conn.close()
#         return "Election not found", 404

#     now = datetime.now()
#     end = datetime.fromisoformat(election['end_time'])

#     if now < end:
#         conn.close()
#         return "Results will be published after voting ends."

#     cur.execute("""
#         SELECT c.id, c.name, c.photo, COUNT(v.id) AS votes
#         FROM candidates c
#         LEFT JOIN votes v ON c.id = v.candidate_id
#         WHERE c.election_id=?
#         GROUP BY c.id
#         ORDER BY votes DESC
#     """, (election_id,))

#     candidates = cur.fetchall()
#     winner = candidates[0] if candidates and candidates[0]['votes'] > 0 else None

#     conn.close()

#     return render_template(
#         "results.html",
#         election=election,
#         candidates=candidates,
#         winner=winner
#     )


# @app.route('/delete_candidate/<int:cid>', methods=['POST'])
# def delete_candidate(cid):
#     if 'admin' not in session:
#         return redirect(url_for('admin'))

#     conn = get_conn()
#     cur = conn.cursor()

#     cur.execute("DELETE FROM votes WHERE candidate_id=?", (cid,))
#     cur.execute("DELETE FROM candidates WHERE id=?", (cid,))
#     conn.commit()
#     conn.close()

#     flash("Candidate deleted successfully!", "success")
#     return redirect(url_for('admin'))


# # ---------------- RUN ----------------
# if __name__ == '__main__':
#     init_db()
#     app.run(debug=True)









































# from flask import Flask, render_template, request, redirect, url_for, session, flash
# from utils.db import get_conn
# from utils.security import hash_password, verify_password
# from datetime import datetime, timedelta
# import os

# app = Flask(__name__)
# app.secret_key = os.urandom(24)

# # Disable browser back button cache
# @app.after_request
# def after_request(response):
#     response.headers["Cache-Control"] = "no-store"
#     return response


# @app.route('/logout')
# def logout():
#     session.clear()
#     return redirect(url_for('login'))


# # ---------------- INITIALIZE DATABASE ----------------
# def init_db():
#     conn = get_conn()
#     cur = conn.cursor()

#     cur.executescript("""
#     CREATE TABLE IF NOT EXISTS students (
#         id INTEGER PRIMARY KEY,
#         college_id TEXT UNIQUE,
#         password_hash TEXT,
#         has_voted INTEGER DEFAULT 0
#     );

#     CREATE TABLE IF NOT EXISTS elections (
#         id INTEGER PRIMARY KEY,
#         name TEXT,
#         is_active INTEGER DEFAULT 1,
#         start_time TEXT,
#         end_time TEXT
#     );

#     CREATE TABLE IF NOT EXISTS candidates (
#         id INTEGER PRIMARY KEY,
#         election_id INTEGER,
#         name TEXT,
#         photo TEXT,
#         FOREIGN KEY (election_id) REFERENCES elections(id)
#     );

#     CREATE TABLE IF NOT EXISTS votes (
#         id INTEGER PRIMARY KEY,
#         election_id INTEGER,
#         candidate_id INTEGER,
#         timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
#         FOREIGN KEY (election_id) REFERENCES elections(id),
#         FOREIGN KEY (candidate_id) REFERENCES candidates(id)
#     );
#     """)

#     cur.execute("SELECT COUNT(*) FROM elections")
#     if cur.fetchone()[0] == 0:
#         start = datetime.now()
#         end = start + timedelta(minutes=30)

#         cur.execute(
#             "INSERT INTO elections (name, is_active, start_time, end_time) VALUES (?,1,?,?)",
#             ("Council of CR 2025", start.isoformat(), end.isoformat())
#         )
#         election_id = cur.lastrowid

#         cur.executemany(
#             "INSERT INTO candidates (election_id, name, photo) VALUES (?, ?, ?)",
#             [
#                 (election_id, "Aman", "aman.jpg"),
#                 (election_id, "Ankit", "ankit.jpg"),
#                 (election_id, "Aayush", "aayush.jpg")
#             ]
#         )

#         students = []
#         for i in range(1, 65):
#             roll = f"0905CS241{str(i).zfill(3)}"
#             students.append((roll, hash_password(f"{roll}#")))

#         cur.executemany(
#             "INSERT INTO students (college_id, password_hash) VALUES (?, ?)",
#             students
#         )

#         conn.commit()

#     conn.close()


# # ---------------- HOME ----------------
# @app.route('/')
# def home():
#     if 'student' in session:
#         return redirect(url_for('vote'))
#     return redirect(url_for('login'))


# # ---------------- REGISTER ----------------
# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     if request.method == 'POST':
#         cid = request.form['college_id'].strip()
#         pwd = request.form['password']
#         confirm = request.form['confirm']

#         if pwd != confirm:
#             flash("Passwords do not match!", "danger")
#             return redirect(url_for('register'))

#         conn = get_conn()
#         cur = conn.cursor()

#         cur.execute("SELECT id FROM students WHERE college_id=?", (cid,))
#         if cur.fetchone():
#             flash("College ID already registered!", "danger")
#             conn.close()
#             return redirect(url_for('register'))

#         cur.execute(
#             "INSERT INTO students (college_id, password_hash) VALUES (?, ?)",
#             (cid, hash_password(pwd))
#         )

#         conn.commit()
#         conn.close()
#         flash("Registration successful!", "success")
#         return redirect(url_for('login'))

#     return render_template('register.html')


# # ---------------- LOGIN ----------------
# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         cid = request.form['college_id'].strip()
#         pwd = request.form['password']

#         conn = get_conn()
#         cur = conn.cursor()
#         cur.execute("SELECT * FROM students WHERE college_id=?", (cid,))
#         user = cur.fetchone()
#         conn.close()

#         if user and verify_password(user['password_hash'], pwd):
#             session['student'] = {'id': user['id'], 'college_id': cid}
#             return redirect(url_for('vote'))

#         flash("Invalid credentials!", "danger")

#     return render_template('login.html')


# # ---------------- VOTE ----------------
# @app.route('/vote', methods=['GET', 'POST'])
# def vote():
#     if 'student' not in session:
#         return redirect(url_for('login'))

#     sid = session['student']['id']
#     now = datetime.now().isoformat()

#     conn = get_conn()
#     cur = conn.cursor()

#     # 🔥 CORRECT active election logic
#     cur.execute("""
#         SELECT * FROM elections
#         WHERE is_active = 1
#         AND start_time <= ?
#         AND end_time >= ?
#         ORDER BY id DESC
#         LIMIT 1
#     """, (now, now))

#     election = cur.fetchone()

#     if not election:
#         conn.close()
#         return render_template(
#     "election.html",
#     message="No election is active right now. Please check back later."
# )


#     cur.execute("SELECT has_voted FROM students WHERE id=?", (sid,))
#     has_voted = bool(cur.fetchone()['has_voted'])

#     if request.method == 'POST':
#         if has_voted:
#             conn.close()
#             return redirect(url_for('thanks'))

#         candidate_id = int(request.form.get('candidate'))

#         cur.execute(
#             "INSERT INTO votes (election_id, candidate_id) VALUES (?, ?)",
#             (election['id'], candidate_id)
#         )
#         cur.execute("UPDATE students SET has_voted=1 WHERE id=?", (sid,))
#         conn.commit()
#         conn.close()
#         return redirect(url_for('thanks'))

#     cur.execute(
#         "SELECT id, name, photo FROM candidates WHERE election_id=?",
#         (election['id'],)
#     )
#     candidates = cur.fetchall()

#     conn.close()

#     return render_template(
#         'vote.html',
#         election=election,
#         candidates=candidates,
#         has_voted=has_voted
#     )


# @app.route('/thanks')
# def thanks():
#     return render_template('thanks.html')


# # ---------------- ADMIN ----------------
# ADMIN_PASS = "THANOSKHANSHARMA"

# @app.route('/admin', methods=['GET', 'POST'])
# def admin():
#     if request.method == 'POST' and 'admin_login' in request.form:
#         if request.form['password'] == ADMIN_PASS:
#             session['admin'] = True
#             return redirect(url_for('admin'))
#         flash("Wrong admin password", "danger")

#     if 'admin' not in session:
#         return render_template('admin.html', logged_in=False)

#     conn = get_conn()
#     cur = conn.cursor()

#     if request.method == 'POST' and 'create_election' in request.form:
#         name = request.form['election_name'].strip()
#         duration = int(request.form['duration'])

#         start = datetime.now()
#         end = start + timedelta(minutes=duration)

#         cur.execute(
#             "INSERT INTO elections (name, is_active, start_time, end_time) VALUES (?,1,?,?)",
#             (name, start.isoformat(), end.isoformat())
#         )
#         conn.commit()
#         flash("Election created", "success")

#     cur.execute("SELECT * FROM elections ORDER BY id DESC")
#     elections = cur.fetchall()

#     results = {}
#     for e in elections:
#         cur.execute("""
#             SELECT c.id, c.name, c.photo, COUNT(v.id) AS votes
#             FROM candidates c
#             LEFT JOIN votes v ON c.id = v.candidate_id
#             WHERE c.election_id=?
#             GROUP BY c.id
#         """, (e['id'],))
#         results[e['name']] = cur.fetchall()

#     cur.execute("SELECT college_id, has_voted FROM students")
#     students = cur.fetchall()

#     conn.close()

#     return render_template(
#         'admin.html',
#         logged_in=True,
#         elections=elections,
#         results=results,
#         students=students
#     )


# @app.route('/delete_candidate/<int:cid>', methods=['POST'])
# def delete_candidate(cid):
#     if 'admin' not in session:
#         return redirect(url_for('admin'))

#     conn = get_conn()
#     cur = conn.cursor()

#     cur.execute("DELETE FROM votes WHERE candidate_id=?", (cid,))
#     cur.execute("DELETE FROM candidates WHERE id=?", (cid,))
#     conn.commit()
#     conn.close()

#     flash("Candidate deleted successfully!", "success")
#     return redirect(url_for('admin'))


# if __name__ == '__main__':
#     init_db()
#     app.run(debug=True)






























# from flask import Flask, render_template, request, redirect, url_for, session, flash
# from utils.db import get_conn
# from utils.security import hash_password, verify_password
# from datetime import datetime, timedelta
# import os

# app = Flask(__name__)
# app.secret_key = os.urandom(24)

# # ----------------------------------
# # Disable browser back button cache
# # ----------------------------------
# @app.after_request
# def after_request(response):
#     response.headers["Cache-Control"] = "no-store"
#     return response


# # ----------------------------------
# # Logout
# # ----------------------------------
# @app.route('/logout')
# def logout():
#     session.clear()
#     return redirect(url_for('login'))


# # ----------------------------------
# # Database Init + Seed
# # ----------------------------------
# def init_db():
#     conn = get_conn()
#     cur = conn.cursor()

#     cur.executescript("""
#     CREATE TABLE IF NOT EXISTS students (
#         id INTEGER PRIMARY KEY,
#         college_id TEXT UNIQUE,
#         password_hash TEXT,
#         has_voted INTEGER DEFAULT 0
#     );

#     CREATE TABLE IF NOT EXISTS elections (
#         id INTEGER PRIMARY KEY,
#         name TEXT,
#         is_active INTEGER DEFAULT 1,
#         start_time TEXT,
#         end_time TEXT
#     );

#     CREATE TABLE IF NOT EXISTS candidates (
#         id INTEGER PRIMARY KEY,
#         election_id INTEGER,
#         name TEXT,
#         photo TEXT,
#         FOREIGN KEY (election_id) REFERENCES elections(id)
#     );

#     CREATE TABLE IF NOT EXISTS votes (
#         id INTEGER PRIMARY KEY,
#         election_id INTEGER,
#         candidate_id INTEGER,
#         timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
#         FOREIGN KEY (election_id) REFERENCES elections(id),
#         FOREIGN KEY (candidate_id) REFERENCES candidates(id)
#     );
#     """)

#     # Seed ONLY ONCE
#     cur.execute("SELECT COUNT(*) FROM elections")
#     if cur.fetchone()[0] == 0:
#         start = datetime.now()
#         end = start + timedelta(minutes=30)

#         cur.execute(
#             "INSERT INTO elections (name, start_time, end_time) VALUES (?,?,?)",
#             ("Council of CR 2025", start.isoformat(), end.isoformat())
#         )
#         election_id = cur.lastrowid

#         cur.executemany(
#             "INSERT INTO candidates (election_id, name, photo) VALUES (?,?,?)",
#             [
#                 (election_id, "Aman", "aman.jpg"),
#                 (election_id, "Ankit", "ankit.jpg"),
#                 (election_id, "Aayush", "aayush.jpg")
#             ]
#         )

#         students = []
#         for i in range(1, 65):
#             roll = f"0905CS241{str(i).zfill(3)}"
#             students.append((roll, hash_password(f"{roll}#")))

#         cur.executemany(
#             "INSERT INTO students (college_id, password_hash) VALUES (?,?)",
#             students
#         )

#         conn.commit()

#     conn.close()


# # ----------------------------------
# # Auto-expire elections
# # ----------------------------------
# def expire_elections():
#     conn = get_conn()
#     cur = conn.cursor()
#     now = datetime.now().isoformat()

#     cur.execute("""
#         UPDATE elections
#         SET is_active = 0
#         WHERE is_active = 1 AND end_time < ?
#     """, (now,))

#     conn.commit()
#     conn.close()


# # ----------------------------------
# # Home
# # ----------------------------------
# @app.route('/')
# def home():
#     if 'student' in session:
#         return redirect(url_for('vote'))
#     return redirect(url_for('login'))


# # ----------------------------------
# # Register
# # ----------------------------------
# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     if request.method == 'POST':
#         cid = request.form['college_id'].strip()
#         pwd = request.form['password']
#         confirm = request.form['confirm']

#         if pwd != confirm:
#             flash("Passwords do not match", "danger")
#             return redirect(url_for('register'))

#         conn = get_conn()
#         cur = conn.cursor()

#         cur.execute("SELECT id FROM students WHERE college_id=?", (cid,))
#         if cur.fetchone():
#             flash("College ID already registered", "danger")
#             conn.close()
#             return redirect(url_for('register'))

#         cur.execute(
#             "INSERT INTO students (college_id, password_hash) VALUES (?,?)",
#             (cid, hash_password(pwd))
#         )

#         conn.commit()
#         conn.close()
#         flash("Registration successful", "success")
#         return redirect(url_for('login'))

#     return render_template('register.html')


# # ----------------------------------
# # Login
# # ----------------------------------
# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         cid = request.form['college_id'].strip()
#         pwd = request.form['password']

#         conn = get_conn()
#         cur = conn.cursor()
#         cur.execute("SELECT * FROM students WHERE college_id=?", (cid,))
#         user = cur.fetchone()
#         conn.close()

#         if user and verify_password(user['password_hash'], pwd):
#             session['student'] = {'id': user['id'], 'college_id': cid}
#             return redirect(url_for('vote'))

#         flash("Invalid credentials", "danger")

#     return render_template('login.html')


# # ----------------------------------
# # Vote Page (STUDENT)
# # ----------------------------------
# @app.route('/vote', methods=['GET', 'POST'])
# def vote():
#     if 'student' not in session:
#         return redirect(url_for('login'))

#     expire_elections()

#     conn = get_conn()
#     cur = conn.cursor()
#     now = datetime.now().isoformat()

#     cur.execute("""
#         SELECT * FROM elections
#         WHERE is_active = 1
#         AND start_time <= ?
#         AND end_time >= ?
#         ORDER BY id DESC
#         LIMIT 1
#     """, (now, now))

#     election = cur.fetchone()

#     if not election:
#         conn.close()
#         return render_template("election.html")

#     sid = session['student']['id']

#     cur.execute("SELECT has_voted FROM students WHERE id=?", (sid,))
#     has_voted = bool(cur.fetchone()['has_voted'])

#     if request.method == 'POST':
#         if has_voted:
#             conn.close()
#             return redirect(url_for('thanks'))

#         candidate_id = int(request.form.get('candidate'))

#         cur.execute(
#             "INSERT INTO votes (election_id, candidate_id) VALUES (?,?)",
#             (election['id'], candidate_id)
#         )
#         cur.execute("UPDATE students SET has_voted=1 WHERE id=?", (sid,))
#         conn.commit()
#         conn.close()
#         return redirect(url_for('thanks'))

#     cur.execute(
#         "SELECT id, name, photo FROM candidates WHERE election_id=?",
#         (election['id'],)
#     )
#     candidates = cur.fetchall()

#     conn.close()
#     return render_template(
#         'vote.html',
#         election=election,
#         candidates=candidates,
#         has_voted=has_voted
#     )


# # ----------------------------------
# # Thanks
# # ----------------------------------
# @app.route('/thanks')
# def thanks():
#     return render_template('thanks.html')


# # ----------------------------------
# # Admin
# # ----------------------------------
# ADMIN_PASS = "THANOSKHANSHARMA"

# @app.route('/admin', methods=['GET', 'POST'])
# def admin():
#     if request.method == 'POST' and 'admin_login' in request.form:
#         if request.form['password'] == ADMIN_PASS:
#             session['admin'] = True
#             return redirect(url_for('admin'))
#         flash("Wrong admin password", "danger")

#     if 'admin' not in session:
#         return render_template('admin.html', logged_in=False)

#     expire_elections()

#     conn = get_conn()
#     cur = conn.cursor()

#     if request.method == 'POST' and 'create_election' in request.form:
#         name = request.form['election_name'].strip()
#         duration = int(request.form['duration'])

#         start = datetime.now()
#         end = start + timedelta(minutes=duration)

#         cur.execute(
#             "INSERT INTO elections (name, start_time, end_time) VALUES (?,?,?)",
#             (name, start.isoformat(), end.isoformat())
#         )
#         conn.commit()
#         flash("Election created", "success")

#     cur.execute("""
#         SELECT *,
#         CASE WHEN is_active=1 THEN 'ACTIVE' ELSE 'COMPLETED' END AS status
#         FROM elections
#         ORDER BY id DESC
#     """)
#     elections = cur.fetchall()

#     results = {}
#     for e in elections:
#         cur.execute("""
#             SELECT c.id, c.name, c.photo, COUNT(v.id) AS votes
#             FROM candidates c
#             LEFT JOIN votes v ON c.id = v.candidate_id
#             WHERE c.election_id=?
#             GROUP BY c.id
#         """, (e['id'],))
#         results[e['name']] = cur.fetchall()

#     cur.execute("SELECT college_id, has_voted FROM students")
#     students = cur.fetchall()

#     conn.close()
#     return render_template(
#         'admin.html',
#         logged_in=True,
#         elections=elections,
#         results=results,
#         students=students
#     )


# # ----------------------------------
# # Delete Candidate
# # ----------------------------------
# @app.route('/delete_candidate/<int:cid>', methods=['POST'])
# def delete_candidate(cid):
#     if 'admin' not in session:
#         return redirect(url_for('admin'))

#     conn = get_conn()
#     cur = conn.cursor()
#     cur.execute("DELETE FROM votes WHERE candidate_id=?", (cid,))
#     cur.execute("DELETE FROM candidates WHERE id=?", (cid,))
#     conn.commit()
#     conn.close()

#     flash("Candidate deleted", "success")
#     return redirect(url_for('admin'))


# # ----------------------------------
# # Run
# # ----------------------------------
# if __name__ == '__main__':
#     init_db()
#     app.run(debug=True)


















































































# from flask import Flask, render_template, request, redirect, url_for, session, flash
# from utils.db import get_conn
# from utils.security import hash_password, verify_password
# from datetime import datetime, timedelta
# import os

# app = Flask(__name__)
# app.secret_key = os.urandom(24)

# # ----------------------------------
# # Disable browser cache
# # ----------------------------------
# @app.after_request
# def after_request(response):
#     response.headers["Cache-Control"] = "no-store"
#     return response


# # ----------------------------------
# # Logout
# # ----------------------------------
# @app.route('/logout')
# def logout():
#     session.clear()
#     return redirect(url_for('login'))


# # ----------------------------------
# # Database Init
# # ----------------------------------
# def init_db():
#     conn = get_conn()
#     cur = conn.cursor()

#     cur.executescript("""
#     CREATE TABLE IF NOT EXISTS students (
#         id INTEGER PRIMARY KEY,
#         college_id TEXT UNIQUE,
#         password_hash TEXT,
#         has_voted INTEGER DEFAULT 0
#     );

#     CREATE TABLE IF NOT EXISTS elections (
#         id INTEGER PRIMARY KEY,
#         name TEXT,
#         is_active INTEGER DEFAULT 1,
#         start_time TEXT,
#         end_time TEXT
#     );

#     CREATE TABLE IF NOT EXISTS candidates (
#         id INTEGER PRIMARY KEY,
#         election_id INTEGER,
#         name TEXT,
#         photo TEXT
#     );

#     CREATE TABLE IF NOT EXISTS votes (
#         id INTEGER PRIMARY KEY,
#         election_id INTEGER,
#         candidate_id INTEGER,
#         timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
#     );
#     """)

#     conn.commit()
#     conn.close()


# # ----------------------------------
# # Auto-expire elections
# # ----------------------------------
# def expire_elections():
#     conn = get_conn()
#     cur = conn.cursor()
#     now = datetime.now().isoformat()

#     cur.execute("""
#         UPDATE elections
#         SET is_active = 0
#         WHERE is_active = 1 AND end_time < ?
#     """, (now,))

#     conn.commit()
#     conn.close()


# # ----------------------------------
# # Home
# # ----------------------------------
# @app.route('/')
# def home():
#     if 'student' in session:
#         return redirect(url_for('vote'))
#     return redirect(url_for('login'))


# # ----------------------------------
# # Register
# # ----------------------------------
# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     if request.method == 'POST':
#         cid = request.form['college_id'].strip()
#         pwd = request.form['password']
#         confirm = request.form['confirm']

#         if pwd != confirm:
#             flash("Passwords do not match", "danger")
#             return redirect(url_for('register'))

#         conn = get_conn()
#         cur = conn.cursor()

#         cur.execute("SELECT id FROM students WHERE college_id=?", (cid,))
#         if cur.fetchone():
#             flash("College ID already exists", "danger")
#             conn.close()
#             return redirect(url_for('register'))

#         cur.execute(
#             "INSERT INTO students (college_id, password_hash) VALUES (?,?)",
#             (cid, hash_password(pwd))
#         )

#         conn.commit()
#         conn.close()
#         flash("Registration successful", "success")
#         return redirect(url_for('login'))

#     return render_template('register.html')


# # ----------------------------------
# # Login
# # ----------------------------------
# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         cid = request.form['college_id']
#         pwd = request.form['password']

#         conn = get_conn()
#         cur = conn.cursor()
#         cur.execute("SELECT * FROM students WHERE college_id=?", (cid,))
#         user = cur.fetchone()
#         conn.close()

#         if user and verify_password(user['password_hash'], pwd):
#             session['student'] = {'id': user['id']}
#             return redirect(url_for('vote'))

#         flash("Invalid credentials", "danger")

#     return render_template('login.html')


# # ----------------------------------
# # Vote Page
# # ----------------------------------
# @app.route('/vote', methods=['GET', 'POST'])
# def vote():
#     if 'student' not in session:
#         return redirect(url_for('login'))

#     expire_elections()

#     conn = get_conn()
#     cur = conn.cursor()
#     now = datetime.now().isoformat()

#     cur.execute("""
#         SELECT * FROM elections
#         WHERE is_active = 1 AND start_time <= ? AND end_time >= ?
#         LIMIT 1
#     """, (now, now))

#     election = cur.fetchone()

#     if not election:
#         conn.close()
#         return render_template("election.html")

#     sid = session['student']['id']

#     cur.execute("SELECT has_voted FROM students WHERE id=?", (sid,))
#     has_voted = cur.fetchone()['has_voted']

#     if request.method == 'POST':
#         if has_voted:
#             conn.close()
#             return redirect(url_for('thanks'))

#         candidate_id = request.form.get('candidate')

#         if not candidate_id:
#             flash("Please select a candidate", "danger")
#             conn.close()
#             return redirect(url_for('vote'))

#         candidate_id = int(candidate_id)

#         cur.execute(
#             "INSERT INTO votes (election_id, candidate_id) VALUES (?,?)",
#             (election['id'], candidate_id)
#         )
#         cur.execute("UPDATE students SET has_voted=1 WHERE id=?", (sid,))
#         conn.commit()
#         conn.close()
#         return redirect(url_for('thanks'))

#     cur.execute(
#         "SELECT * FROM candidates WHERE election_id=?",
#         (election['id'],)
#     )
#     candidates = cur.fetchall()

#     conn.close()
#     return render_template(
#         'vote.html',
#         election=election,
#         candidates=candidates,
#         has_voted=has_voted
#     )


# # ----------------------------------
# # Thanks
# # ----------------------------------
# @app.route('/thanks')
# def thanks():
#     return render_template('thanks.html')


# # ----------------------------------
# # Admin
# # ----------------------------------
# ADMIN_PASS = "THANOSKHANSHARMA"

# @app.route('/admin', methods=['GET', 'POST'])
# def admin():
#     if request.method == 'POST' and 'admin_login' in request.form:
#         if request.form['password'] == ADMIN_PASS:
#             session['admin'] = True
#             return redirect(url_for('admin'))
#         flash("Wrong admin password", "danger")

#     if 'admin' not in session:
#         return render_template('admin.html', logged_in=False)

#     expire_elections()

#     conn = get_conn()
#     cur = conn.cursor()

#     # Create Election
#     if request.method == 'POST' and 'create_election' in request.form:
#         name = request.form['election_name']
#         duration = int(request.form['duration'])

#         start = datetime.now()
#         end = start + timedelta(minutes=duration)

#         cur.execute("UPDATE elections SET is_active = 0")
#         cur.execute("""
#             INSERT INTO elections (name, is_active, start_time, end_time)
#             VALUES (?,?,?,?)
#         """, (name, 1, start.isoformat(), end.isoformat()))

#         conn.commit()
#         flash("Election created", "success")

#     # Add Candidate
#     if request.method == 'POST' and 'add_candidate' in request.form:
#         cname = request.form['candidate_name']
#         photo = request.form['photo']

#         cur.execute("SELECT id FROM elections WHERE is_active=1")
#         election = cur.fetchone()

#         if election:
#             cur.execute("""
#                 INSERT INTO candidates (election_id, name, photo)
#                 VALUES (?,?,?)
#             """, (election['id'], cname, photo))
#             conn.commit()
#             flash("Candidate added", "success")

#     cur.execute("SELECT * FROM elections ORDER BY id DESC")
#     elections = cur.fetchall()

#     results = {}
#     for e in elections:
#         cur.execute("""
#             SELECT c.name, c.photo, COUNT(v.id) AS votes
#             FROM candidates c
#             LEFT JOIN votes v ON c.id = v.candidate_id
#             WHERE c.election_id=?
#             GROUP BY c.id
#         """, (e['id'],))
#         results[e['name']] = cur.fetchall()

#     cur.execute("SELECT college_id, has_voted FROM students")
#     students = cur.fetchall()

#     conn.close()
#     return render_template(
#         'admin.html',
#         logged_in=True,
#         elections=elections,
#         results=results,
#         students=students
#     )


# # ----------------------------------
# # Run
# # ----------------------------------
# if __name__ == '__main__':
#     init_db()
#     app.run(debug=True)














from flask import Flask, render_template, request, redirect, url_for, session, flash
from utils.db import get_conn
from utils.security import hash_password, verify_password
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import sqlite3, os

app = Flask(__name__)
app.secret_key = "super-secret-key"

# ---------------- CONFIG ----------------
UPLOAD_FOLDER = "static/photos"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# ---------------- HELPERS ----------------
def row_to_dict(row):
    return dict(row) if row else None

def rows_to_dicts(rows):
    return [dict(r) for r in rows]


# ---------------- NO CACHE ----------------
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-store"
    return response


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------- DB INIT ----------------
def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY,
        college_id TEXT UNIQUE,
        password_hash TEXT
    );

    CREATE TABLE IF NOT EXISTS elections (
        id INTEGER PRIMARY KEY,
        name TEXT,
        is_active INTEGER DEFAULT 1,
        start_time TEXT,
        end_time TEXT
    );

    CREATE TABLE IF NOT EXISTS candidates (
        id INTEGER PRIMARY KEY,
        election_id INTEGER,
        name TEXT,
        photo TEXT
    );

    CREATE TABLE IF NOT EXISTS votes (
        id INTEGER PRIMARY KEY,
        election_id INTEGER,
        student_id INTEGER,
        candidate_id INTEGER,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(election_id, student_id)
    );
    """)
    conn.commit()
    conn.close()


def seed_students():
    conn = get_conn()
    cur = conn.cursor()
    for i in range(1, 65):
        cid = f"0905CS241{str(i).zfill(3)}"
        cur.execute(
            "INSERT OR IGNORE INTO students (college_id,password_hash) VALUES (?,?)",
            (cid, hash_password(f"{cid}#"))
        )
    conn.commit()
    conn.close()


# ---------------- HOME ----------------
@app.route("/")
@app.route("/home")
def home():
    return render_template("home.html")


# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        cid = request.form["college_id"]
        pwd = request.form["password"]

        conn = get_conn()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM students WHERE college_id=?", (cid,))
        student = row_to_dict(cur.fetchone())
        conn.close()

        if not student or not verify_password(student["password_hash"], pwd):
            flash("Invalid credentials", "danger")
            return redirect(url_for("login"))

        session.clear()
        session["student"] = {"id": student["id"], "college_id": cid}
        return redirect(url_for("vote"))

    return render_template("login.html")


# ---------------- VOTE ----------------
@app.route("/vote", methods=["GET", "POST"])
def vote():
    if "student" not in session:
        return redirect(url_for("login"))

    sid = session["student"]["id"]
    now = datetime.now().isoformat()

    conn = get_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM elections
        WHERE is_active=1 AND start_time<=? AND end_time>=?
        LIMIT 1
    """, (now, now))
    election = row_to_dict(cur.fetchone())

    if not election:
        conn.close()
        return render_template("election.html")

    cur.execute("SELECT 1 FROM votes WHERE election_id=? AND student_id=?", (election["id"], sid))
    has_voted = cur.fetchone() is not None

    if request.method == "POST" and not has_voted:
        candidate_id = request.form.get("candidate")
        cur.execute(
            "INSERT INTO votes (election_id,student_id,candidate_id) VALUES (?,?,?)",
            (election["id"], sid, candidate_id)
        )
        conn.commit()
        conn.close()
        return redirect(url_for("thanks"))

    cur.execute("SELECT * FROM candidates WHERE election_id=?", (election["id"],))
    candidates = rows_to_dicts(cur.fetchall())
    conn.close()

    return render_template("vote.html", election=election, candidates=candidates, has_voted=has_voted)


# ---------------- THANKS ----------------
@app.route("/thanks")
def thanks():
    return render_template("thanks.html")


# ---------------- ADMIN ----------------
ADMIN_PASS = "ADMIN0905"

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST" and "admin_login" in request.form:
        if request.form["password"] == ADMIN_PASS:
            session.clear()
            session["admin"] = True
            return redirect(url_for("admin"))
        flash("Wrong admin password", "danger")

    if "admin" not in session:
        return render_template("admin.html", logged_in=False)

    conn = get_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    if request.method == "POST" and "end_election" in request.form:
        cur.execute("UPDATE elections SET is_active=0")
        conn.commit()

    if request.method == "POST" and "create_election" in request.form:
        start = datetime.now()
        end = start + timedelta(minutes=int(request.form["duration"]))

        cur.execute("UPDATE elections SET is_active=0")
        cur.execute("DELETE FROM votes")
        cur.execute("DELETE FROM candidates")

        cur.execute(
            "INSERT INTO elections (name,is_active,start_time,end_time) VALUES (?,?,?,?)",
            (request.form["election_name"], 1, start.isoformat(), end.isoformat())
        )
        conn.commit()

    if request.method == "POST" and "add_candidate" in request.form:
        cur.execute("SELECT id FROM elections WHERE is_active=1 LIMIT 1")
        active = cur.fetchone()
        if active:
            photo = request.files["photo"]
            filename = secure_filename(photo.filename)
            photo.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            cur.execute(
                "INSERT INTO candidates (election_id,name,photo) VALUES (?,?,?)",
                (active["id"], request.form["candidate_name"], filename)
            )
            conn.commit()

    cur.execute("SELECT * FROM elections WHERE is_active=1 LIMIT 1")
    election = row_to_dict(cur.fetchone())

    cur.execute("SELECT COUNT(*) FROM students")
    total_students = cur.fetchone()[0]

    cur.execute("""
        SELECT s.college_id,
               CASE WHEN v.id IS NOT NULL THEN 1 ELSE 0 END AS has_voted
        FROM students s
        LEFT JOIN votes v ON s.id=v.student_id
        ORDER BY s.college_id
    """)
    students = rows_to_dicts(cur.fetchall())

    votes_cast = 0
    candidates = []

    if election:
        cur.execute("SELECT COUNT(*) FROM votes WHERE election_id=?", (election["id"],))
        votes_cast = cur.fetchone()[0]

        cur.execute("""
            SELECT c.id,c.name,c.photo,COUNT(v.id) AS votes
            FROM candidates c
            LEFT JOIN votes v ON c.id=v.candidate_id
            WHERE c.election_id=?
            GROUP BY c.id
            ORDER BY votes DESC
        """, (election["id"],))
        candidates = rows_to_dicts(cur.fetchall())

    conn.close()

    return render_template(
        "admin.html",
        logged_in=True,
        election=election,
        candidates=candidates,
        students=students,
        total_students=total_students,
        votes_cast=votes_cast,
        votes_remaining=total_students - votes_cast,
        leader=candidates[0] if candidates else None
    )


# ---------------- DELETE CANDIDATE ----------------
@app.route("/delete_candidate/<int:cid>", methods=["POST"])
def delete_candidate(cid):
    if "admin" not in session:
        return redirect(url_for("admin"))

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM votes WHERE candidate_id=?", (cid,))
    cur.execute("DELETE FROM candidates WHERE id=?", (cid,))
    conn.commit()
    conn.close()

    flash("Candidate deleted", "success")
    return redirect(url_for("admin"))


# ---------------- DELETE STUDENT ----------------
@app.route("/delete_student/<college_id>", methods=["POST"])
def delete_student(college_id):
    if "admin" not in session:
        return redirect(url_for("admin"))

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT id FROM students WHERE college_id=?", (college_id,))
    row = cur.fetchone()

    if row:
        cur.execute("DELETE FROM votes WHERE student_id=?", (row[0],))
        cur.execute("DELETE FROM students WHERE id=?", (row[0],))
        conn.commit()
        flash(f"Student {college_id} deleted", "success")

    conn.close()
    return redirect(url_for("admin"))


# ---------------- RUN ----------------
if __name__ == "__main__":
    init_db()
    seed_students()
    app.run(debug=True)

































