import sqlite3 
import os
from flask import Flask, jsonify, make_response, request 
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS 
from pathlib import Path 
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, JWTManager

# Initializing and configuring extensions Flask will use 
app = Flask(__name__) # Creating a new Flask app
app.config["JWT_SECRET_KEY"] = "super-secret" # need to change to smth else 
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
jwt = JWTManager(app)
CORS(app)

def init_db():
    # skipping db initalization if it already exists
    if os.path.exists("../database/tessera.db"):
        return 

    conn = sqlite3.connect("../database/tessera.db")
    cursor = conn.cursor()

    with open("schema.sql", "r") as f:
        schema = f.read()
    
    cursor.executescript(schema)

    with open("data.sql", "r") as f:
        data = f.read()
    
    cursor.executescript(data)

    conn.commit()
    conn.close()

def get_db_connection():
  conn = sqlite3.connect("../database/tessera.db")
  conn.row_factory = sqlite3.Row
  return conn

@app.route('/emails', methods=["GET"])
@jwt_required()
def getEmails():
    conn.get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT email FROM Users")

    emails = cursor.fetchall()

    emails_list = [dict(email) for email in emails]
    conn.close()

    return jsonify(emails)

@app.route('/events', methods=['GET'])
def get_events():
    conn = get_db_connection() 
    cursor = conn.cursor()

    query = 'SELECT * FROM Events' 
    params = []
    query_conditions = []

    # We want to see if afterDate param is provided 
    after_date = request.args.get('afterDate') # fetching the afterDate param
    if after_date: 
        query_conditions.append('date > ?') # fetching dates AFTER after_date, ? is a placeholder
        params.append(after_date)

    eventLocation = request.args.get('location')
    if eventLocation:
        query_conditions.append('location = ?')
        params.append(eventLocation)

    if query_conditions:
        query += ' WHERE ' + ' AND '.join(query_conditions) # AND only shows up between two strs 

    cursor.execute(query, params)
    events = cursor.fetchall() 

    events_list = [dict(event) for event in events]
    conn.close() 

    return jsonify(events_list)

# need to check if there are username duplicates 
@app.route('/user/create', methods=['POST'])
def create_user():
    # Extract email, username, and password from the JSON payload
    email = request.json.get('email')
    username = request.json.get('username', None)
    password = request.json.get('password', None)

    # Basic validation to ensure all fields are provided
    if not email or not username or not password:
        return jsonify({'error': 'All fields (email, username, and password) are required.'}), 400

    # Hash the password
    hashed_password = generate_password_hash(password)

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Attempt to insert the new user into the Users table
        cursor.execute('INSERT INTO Users (email, username, password_hash) VALUES (?, ?, ?)',
                       (email, username, hashed_password))
        conn.commit()  # Commit the changes to the database

        # Retrieve the user_id of the newly created user to confirm creation
        cursor.execute('SELECT user_id FROM Users WHERE username = ?', (username,))
        new_user_id = cursor.fetchone()

        conn.close()

        return jsonify({'message': 'User created successfully', 'user_id': new_user_id['user_id']}), 201

    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username or email already exists.'}), 409
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/login', methods=['POST'])
def login():
    conn = get_db_connection() 
    cursor = conn.cursor()

    username = request.json.get('username')
    password = request.json.get('password')

    if not (username and password): 
        return jsonify({'error': 'Username/Password needed'}), 400

    cursor.execute('SELECT * FROM Users WHERE username = ?', (username,))
    user = cursor.fetchone()
    if not user: 
        return jsonify({'error': 'Username does not exist'}), 400
   
    db_user_id, _, db_password, _, db_account_type = user 
    access_token = create_access_token(identity=db_user_id, role=db_account_type)

    correctPass = check_password_hash(db_password, password)

    if not correctPass:
        return jsonify({'error': 'Incorrect password'}), 400
        
    conn.close()
    
    return jsonify(username=username, access_token=access_token), 200

@app.route('/changeData', methods=['PUT'])
@jwt_required()
def changeUserData():
    conn = get_db_connection()
    cursor = conn.cursor()

    user_id = request.json.get('user_id')
    username = request.json.get('new_username')
    email = request.json.get('new_email')

    if not (username and email):
        return jsonify({'error': 'At least Username or Email is needed to update user data.'}), 400
    
    cursor.execute('SELECT * FROM Users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    if not user: 
        return jsonify({'error': 'Username does not exist'}), 400

    user_id, db_username, _, db_email = user

    if username != db_username: 
        cursor.execute('UPDATE Users SET username = ? WHERE user_id = ?', (username, user_id))
    
    if email: 
        if email != db_email:
            print("performing email change!")
            cursor.execute('UPDATE Users SET email = ? WHERE user_id = ?', (email, user_id))

    conn.close()
    return jsonify({'message': 'User updated successfully'}), 200

@app.route('/deleteUser', methods=["DELETE"])
@jwt_required()
def deleteUser():
    conn = get_db_connection()
    cursor = conn.cursor()

    user_id = request.json.get('user_id')

    if not user_id:
        return jsonify({'error': 'User_id is needed to delete User'})
    
    cursor.execute('DELETE FROM Users WHERE user_id = ?', (user_id,))

    if cursor.rowcount == 0:
        return jsonify({'error': 'User does not exist'}), 400

    conn.commit()
    conn.close()
    return jsonify({'message': 'User successfully deleted'}), 200

@app.route('/events/create', methods=["POST"])
@jwt_required()
def create_event():
    conn = get_db_connection()
    cursor = conn.cursor()

    identity, role = get_jwt_identity()
    # if there is no JWT token (aka person is not logged in) OR person is NOT admin, do smth idk
    if curr_identity is None or role is None or role != 1:
        return None # idk what to return here, its if there is no authority with the user

    # getting everything needed for an Event row 
    name = request.json.get('event_name')
    description = request.json.get('event_description')
    date = request.json.get('event_date')
    time = request.json.get('event_time')
    location = request.json.get('event_location')

    cursor.execute('SELECT event_id FROM Events WHERE name = ?', (name,))
    existing_event = cursor.fetchone()

    if existing_event:
        return jsonify({'error': 'event already exists'})

    cursor.execute('INSERT INTO Events (name, description, date, time, location) VALUES (?, ?, ?, ?, ?)', (name, description, date, time, location))

    conn.commit()
    conn.close()
    return jsonify(curr_identity)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
