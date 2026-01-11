from flask import Flask, jsonify, make_response, request 
import sqlite3 
from datetime import datetime 
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__) # Creating a new Flask app

def get_db_connection():
  conn = sqlite3.connect('../database/tessera.db')
  conn.row_factory = sqlite3.Row
  return conn

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
    username = request.json.get('username')
    password = request.json.get('password')

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

    if not (username or password): 
        return jsonify({'error': 'Username/Password needed'}), 400

    cursor.execute('SELECT * FROM Users WHERE username = ?', (username,))
    user = cursor.fetchone()
    if not user: 
        return jsonify({'error': 'Username does not exist'}), 400
   
    _, _, db_password, _ = user 

    correctPass = check_password_hash(db_password, password)

    if not correctPass:
        return jsonify({'error': 'Incorrect password'}), 400
        
    conn.close()
    
    return jsonify(username, password), 200

@app.route('/changeData', methods=['PUT'])
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
    
    print(email, user_id)
    if email: 
        if email != db_email:
            print("performing email change!")
            cursor.execute('UPDATE Users SET email = ? WHERE user_id = ?', (email, user_id))

    return jsonify({'message': 'User updated successfully'}), 200

if __name__ == '__main__':
    app.run(debug=True)
