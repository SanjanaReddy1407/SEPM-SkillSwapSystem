import os
import sqlite3
from flask import Flask, send_from_directory, request, jsonify, session

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder=None)
app.config['SECRET_KEY'] = 'crossskills_secret_key_2026'

# -------------------------------------------------------------
# CSS / JS / DATA UNIVERSAL SERVING (Handles both /css and /app/css)
# -------------------------------------------------------------
@app.route('/css/<path:filename>')
@app.route('/app/css/<path:filename>')
def serve_css(filename):
    return send_from_directory(os.path.join(BASE_DIR, 'css'), filename, mimetype='text/css')

@app.route('/js/<path:filename>')
@app.route('/app/js/<path:filename>')
def serve_js(filename):
    return send_from_directory(os.path.join(BASE_DIR, 'js'), filename, mimetype='application/javascript')

@app.route('/data/<path:filename>')
@app.route('/app/data/<path:filename>')
def serve_data(filename):
    return send_from_directory(os.path.join(BASE_DIR, 'data'), filename, mimetype='application/json')
# -------------------------------------------------------------
# 2. ROOT HTML PAGES ROUTING
# -------------------------------------------------------------
@app.route('/')
@app.route('/index.html')
def serve_index():
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/login')
@app.route('/login.html')
def serve_login():
    return send_from_directory(BASE_DIR, 'login.html')

@app.route('/signup')
@app.route('/signup.html')
def serve_signup():
    return send_from_directory(BASE_DIR, 'signup.html')

@app.route('/profile-setup')
@app.route('/profile-setup.html')
def serve_profile_setup():
    return send_from_directory(BASE_DIR, 'profile-setup.html')

# -------------------------------------------------------------
# 3. APP SUB-FOLDER HTML PAGES ROUTING (app/*.html)
# -------------------------------------------------------------
@app.route('/app/<path:page>')
def serve_app_pages(page):
    if not page.endswith('.html'):
        page += '.html'
    return send_from_directory(os.path.join(BASE_DIR, 'app'), page)

# -------------------------------------------------------------
# 4. BACKEND API ENDPOINTS (CS1.db Integration)
# -------------------------------------------------------------

# Check Email Existence & Login
@app.route('/api/auth/check-email', methods=['POST'])
def check_email():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM user_profile WHERE LOWER(email) = ?", (email,)).fetchone()
    conn.close()

    if user:
        return jsonify({"exists": True, "user_id": user['user_id'], "name": user['name']})
    return jsonify({"exists": False})

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM user_profile WHERE LOWER(email) = ? AND password = ?", (email, password)).fetchone()
    conn.close()

    if user:
        session['user_id'] = user['user_id']
        session['user_name'] = user['name']
        return jsonify({"success": True, "user_id": user['user_id'], "name": user['name']}), 200
    return jsonify({"success": False, "message": "Invalid credentials"}), 401

@app.route('/api/auth/signup', methods=['POST'])
def signup():
    data = request.get_json() or {}
    name = data.get('name')
    email = data.get('email', '').strip().lower()
    password = data.get('password')
    cat_id = data.get('category_id', 1)
    offered_skill = data.get('offered_skill')
    skill_level = data.get('skill_level', 'Intermediate')
    desired_skill = data.get('desired_skill')
    desired_level = data.get('desired_level', 'Beginner')

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO user_profile (name, email, password, feedback_rate)
            VALUES (?, ?, ?, 5.00)
        """, (name, email, password))
        new_uid = cursor.lastrowid

        cursor.execute("""
            INSERT INTO skills (user_id, category_id, skill, skill_level, desired_skill, desired_level)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (new_uid, cat_id, offered_skill, skill_level, desired_skill, desired_level))

        conn.commit()
        session['user_id'] = new_uid
        session['user_name'] = name
        return jsonify({"success": True, "user_id": new_uid, "name": name}), 201
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "Email already registered"}), 409
    finally:
        conn.close()

# Current Active User Info
@app.route('/api/user/current', methods=['GET'])
def get_current_user():
    uid = session.get('user_id', 1)
    conn = get_db_connection()
    user = conn.execute("""
        SELECT u.*, s.skill AS offered_skill, s.skill_level, s.desired_skill, s.desired_level, c.category_name
        FROM user_profile u
        LEFT JOIN skills s ON u.user_id = s.user_id
        LEFT JOIN catgory c ON s.category_id = c.category_id
        WHERE u.user_id = ?
    """, (uid,)).fetchone()
    conn.close()
    return jsonify(dict(user) if user else {})

# Categories List
@app.route('/api/categories', methods=['GET'])
def get_categories():
    conn = get_db_connection()
    categories = conn.execute("SELECT * FROM catgory ORDER BY category_id ASC").fetchall()
    conn.close()
    return jsonify([dict(row) for row in categories])

# Discovery Search Engine
@app.route('/api/search', methods=['GET'])
def search_students():
    q = request.args.get('q', '').strip()
    cat = request.args.get('category', '').strip()
    uid = session.get('user_id', 0)

    sql = """
        SELECT 
            u.user_id, u.name, u.email, u.feedback_rate,
            s.skill AS offered_skill, s.skill_level,
            s.desired_skill, s.desired_level,
            c.category_name
        FROM user_profile u
        JOIN skills s ON u.user_id = s.user_id
        JOIN catgory c ON s.category_id = c.category_id
        WHERE (? = '' OR u.name LIKE ? OR s.skill LIKE ? OR s.desired_skill LIKE ?)
          AND (? = '' OR c.category_name = ?)
          AND u.user_id != ?
    """
    param = f"%{q}%"
    conn = get_db_connection()
    results = conn.execute(sql, (q, param, param, param, cat, cat, uid)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in results])

# Recommendations Engine
@app.route('/api/recommendations', methods=['GET'])
def get_recommendations():
    uid = session.get('user_id', 1)
    conn = get_db_connection()
    my_skill = conn.execute("SELECT * FROM skills WHERE user_id = ?", (uid,)).fetchone()
    
    if not my_skill:
        conn.close()
        return jsonify([])

    my_offer = my_skill['skill'].lower()
    my_want = my_skill['desired_skill'].lower()

    peers = conn.execute("""
        SELECT 
            u.user_id, u.name, u.email, u.feedback_rate,
            s.skill AS offered_skill, s.skill_level,
            s.desired_skill, s.desired_level,
            c.category_name
        FROM user_profile u
        JOIN skills s ON u.user_id = s.user_id
        JOIN catgory c ON s.category_id = c.category_id
        WHERE u.user_id != ?
    """, (uid,)).fetchall()
    conn.close()

    recs = []
    for p in peers:
        score = 50
        p_offer = p['offered_skill'].lower()
        p_want = p['desired_skill'].lower()

        if p_offer in my_want: score += 25
        if my_offer in p_want: score += 25
        if p['feedback_rate'] >= 4.5: score += 10

        item = dict(p)
        item['match_score'] = min(score, 99)
        recs.append(item)

    recs.sort(key=lambda x: x['match_score'], reverse=True)
    return jsonify(recs)

# Connections & Requests
@app.route('/api/connections', methods=['GET', 'POST'])
def handle_connections():
    uid = session.get('user_id', 1)
    conn = get_db_connection()

    if request.method == 'POST':
        data = request.get_json() or {}
        target_uid = data.get('target_user_id')
        conn.execute("INSERT INTO connection (User_id, connection_user_id) VALUES (?, ?)", (uid, target_uid))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Connection requested"}), 201

    connections = conn.execute("""
        SELECT 
            c.connection_id,
            CASE WHEN c.User_id = ? THEN u2.user_id ELSE u1.user_id END AS peer_id,
            CASE WHEN c.User_id = ? THEN u2.name ELSE u1.name END AS peer_name,
            CASE WHEN c.User_id = ? THEN u2.feedback_rate ELSE u1.feedback_rate END AS peer_rating,
            s.skill AS peer_offered_skill,
            s.desired_skill AS peer_desired_skill
        FROM connection c
        JOIN user_profile u1 ON c.User_id = u1.user_id
        JOIN user_profile u2 ON c.connection_user_id = u2.user_id
        LEFT JOIN skills s ON (s.user_id = u2.user_id OR s.user_id = u1.user_id)
        WHERE c.User_id = ? OR c.connection_user_id = ?
    """, (uid, uid, uid, uid, uid)).fetchall()
    
    conn.close()
    return jsonify([dict(c) for c in connections])

# Schedules
@app.route('/api/schedules', methods=['GET', 'POST'])
def handle_schedules():
    uid = session.get('user_id', 1)
    conn = get_db_connection()

    if request.method == 'POST':
        data = request.get_json() or {}
        slots = data.get('number_of_slot', 1)
        start = data.get('start')
        end = data.get('end')
        agenda = data.get('agenda')

        conn.execute("""
            INSERT INTO schedule (User_id, number_of_slot, start, "end", agenda)
            VALUES (?, ?, ?, ?, ?)
        """, (uid, slots, start, end, agenda))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Slot scheduled"}), 201

    schedules = conn.execute("SELECT * FROM schedule WHERE User_id = ?", (uid,)).fetchall()
    conn.close()
    return jsonify([dict(s) for s in schedules])

# Feedback
@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    data = request.get_json() or {}
    target_uid = data.get('target_user_id')
    stars = int(data.get('no_of_star', 5))

    conn = get_db_connection()
    conn.execute("INSERT INTO feedback (user_id, no_of_star) VALUES (?, ?)", (target_uid, stars))
    
    avg_row = conn.execute("SELECT AVG(no_of_star) AS avg_rate FROM feedback WHERE user_id = ?", (target_uid,)).fetchone()
    new_rate = round(avg_row['avg_rate'], 2) if avg_row['avg_rate'] else 5.00
    
    conn.execute("UPDATE user_profile SET feedback_rate = ? WHERE user_id = ?", (new_rate, target_uid))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "updated_rating": new_rate})

if __name__ == '__main__':
    app.run(debug=True, port=5000)