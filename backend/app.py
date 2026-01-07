from flask import Flask, jsonify, make_response, request # Importing the Flask library and some helper functions
import sqlite3 # Library for talking to our database
from datetime import datetime # We'll be working with dates 
from werkzeug.security import generate_password_hash

app = Flask(__name__) # Creating a new Flask app. This will help us create API endpoints hiding the complexity of writing network code!

# This function returns a connection to the database which can be used to send SQL commands to the database
def get_db_connection():
  conn = sqlite3.connect('../database/tessera.db')
  conn.row_factory = sqlite3.Row
  return conn

@app.route()

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

    eventLocation = requests.args.get('location')
    if eventLocation:
        query_conditions.append('location = ?')
        params.append(eventLocation)

    cursor.execute(query, params)
    events = cursor.fetchall() 

    if query_conditions:
        query += ' WHERE ' + ' AND '.join(query_conditions) # AND only shows up between two strs 

    events_list = [dict(event) for event in events]
    conn.close() 

    return jsonify(events.list)


@app.route('/user', methods=['POST'])
def create_user(): 
    email = request.json.get('email')
    username = request.json.get('username')
    password = request.json.get('password')

    if not email or not username or not password:
        return jsonify({'error': 'All fields (email, username, and password) are required.'}), 400

    hashed_password = generate_password_hash(password)

    try: 
        conn = get_db_connection()
        cursor = conn.cursor() 

        cursor.execute('INSERT INTO Users (email, username, password_hash) VALUES (?, ?, ?)', (email, username, hashed_password))
        conn.commit()

        cursor.execute('SELECT Users.user_id FROM Users WHERE Users.user_id = ?', (username,))
        new_user_id = cursor.fetchone() 



if __name__ == '__main__':
    app.run(debug=True)
