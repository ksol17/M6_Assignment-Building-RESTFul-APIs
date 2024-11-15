from flask import Flask, request, jsonify
from flask_marshmallow import Marshmallow
from marshmallow import Schema, fields, ValidationError
import mysql.connector
from mysql.connector import Error
from datetime import datetime



# Creating Flask application and Marshmallow
app = Flask(__name__)
ma = Marshmallow(app)

# Creating Schema using Marshmallow
class MemberSchema(ma.Schema):
    name = fields.String(required=True)
    age = fields.Int(required=True)

    class Meta:
        fields = ('name', 'age', 'id')

member_schema = MemberSchema()
members_schema = MemberSchema(many=True)
# -------------------------------------------------------------------
class WorkoutSessionSchema(ma.Schema):
    session_id = fields.Int(dump_only=True)
    member_id = fields.Int(required=True)
    session_date = fields.Date(required=True)
    session_time = fields.Time(required=True)
    activity = fields.Str(required=True)

    class Meta:
        fields = ('session_id', 'member_id', 'session_date', 'session_time', 'activity')

workout_session_schema = WorkoutSessionSchema()
workout_sessions_schema = WorkoutSessionSchema(many=True)


# ---------------------------------------------------------------------------

# Database connection details
def get_db_connection():
    """Connect to the MySQL database and return the connection object """
    # Database connection parameters
    db_name = "fitness_center_DB"
    user = "root"
    password = "Preciosa2016!"
    host = "localhost"

    try:
        #Attempting to establish a connection
        conn = mysql.connector.connect(
            database=db_name,
            user=user,
            password=password,
            host=host
        )
        
        # Check if the connection is successful
        print("Connected to MySQL database successfully")
        return conn

    except Error as e:
        # Handling if the connection is successful
        print(f"Error: {e}")
        return None

# -------------------------------------------------------------------   
@app.route('/')
def home():
    return 'Welcome to Temple Fitness Center'

# -------------------------------------------------------------------
# FITNESS CENTER MEMBERS
@app.route('/members', methods=['GET'])
def get_members():
    try: 
        conn = get_db_connection()
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500
        cursor = conn.cursor(dictionary=True)
        
        query = "SELECT * FROM Members"

        cursor.execute(query)

        members = cursor.fetchall()

        return members_schema.jsonify(members)
    
    except Error as e:
        print(f"Error: {e}")
        return jsonify({"error": "Internal Server Error"}), 500
    
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# -------------------------------------------------------------------
@app.route('/members', methods=['POST'])
def add_member():
    # Logic to add a member
    try:
        # Validate and deserialize input
        member_data = member_schema.load(request.json)
    except ValidationError as err:
        print(f"Error: {e}")
        return jsonify(e.messages), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        cursor = conn.cursor()
        query = "INSERT INTO Members (name, age, id) VALUES (%s, %s, %s)"
        cursor.execute(query, (member_data['name'], member_data['age'], member_data['id']))


        
        conn.commit()
        return jsonify({"message": "New member added successfully"}), 201
    
    except Error as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500
    
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()



# ------------------------------------------------------------------------

@app.route('/members/<int:id>', methods=['PUT'])
def update_member(id):
    try:
        # Validate and deserialize input
        member_data = member_schema.load(request.json)
    except ValidationError as err:
        print(f"Error: {e}")
        return jsonify(err.messages), 400
    
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = conn.cursor()

        updated_member = (member_data['name'], member_data['age'], id)

        query = "UPDATE Members SET name = %s, age = %s WHERE id = %s"

        cursor.execute(query, updated_member)
        conn.commit()
        
        return jsonify({"message": "Member updated successfully"}), 200
    
    except Error as e:
        print(f"Error: {e}")
        return jsonify({"error": "Internal Server Error"}), 500
    
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# ----------------------------------------------------------------------------------

@app.route('/members/<int:id>', methods=['DELETE'])
def delete_member(id):
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = conn.cursor()

        member_to_remove = (id,)

        cursor.execute("SELECT * FROM Members WHERE id = %s", member_to_remove)
        member = cursor.fetchone()
        if not member:
            return jsonify({"error": "Member not found"}), 404

        query = "DELETE FROM Members WHERE id = %s"
        cursor.execute(query, member_to_remove)
        conn.commit()
        
        return jsonify({"message": "Member deleted successfully"}), 201
    
    except Error as e:
        print(f"Error: {e}")
        return jsonify({"error": "Interal Server Error"}), 500
    finally: 
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
# ----------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------
# WORKOUT_SESSIONS

# Route to view all workout sessions

@app.route('/workouts', methods=['GET'])
def get_all_workouts():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    
    cursor = conn.cursor(dictionary=True)
    query = """
            SELECT 
                session_id, 
                member_id, 
                DATE_FORMAT(session_date, '%Y-%m-%d') AS session_date, 
                TIME_FORMAT(session_time, '%h:%i %p') AS session_time, 
                activity 
            FROM WorkoutSessions
        """
    cursor.execute(query)
    workouts = cursor.fetchall()
    return jsonify(workouts), 200
            
    cursor.close()
    conn.close()

    return workout_sessions_schema.jsonify(workouts)

# ----------------------------------------------------------------------------------
# Route to schedule a workout session
@app.route('/workouts', methods=['POST'])
def schedule_workout():
    try:
        # Validate and deserialize input
        workout_data = workout_session_schema.load(request.json)
    except ValidationError as err:
        print(f"Validation Error: {err.messages}")
        return jsonify({"error": "Invalid input"}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = conn.cursor()
        query = """
            INSERT INTO WorkoutSessions (member_id, session_date, session_time, activity) 
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (
            workout_data["member_id"],
            workout_data["session_date"],
            workout_data["session_time"],
            workout_data["activity"]
        ))
        conn.commit()

        # Retrieve the newly inserted session_id
        session_id = cursor.lastrowid

        # Return the success message with the new session_id
        return jsonify({
            "message": "Workout session scheduled successfully",
            "session_id": session_id
        }), 201

    except Error as e:
        print(f"Database Error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# ----------------------------------------------------------------------------------
# Route to update a workout by session_id
@app.route('/workouts/<int:session_id>', methods=['PUT'])
def update_workout_session(session_id):
    try:
        # Validate and deserialize input
        workout_data = workout_session_schema.load(request.json)
    except ValidationError as err:
        print(f"Validation Error: {err.messages}")
        return jsonify({"error": "Invalid input"}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = conn.cursor()

        # Check if the session exists
        query_check = "SELECT * FROM WorkoutSessions WHERE session_id = %s"
        cursor.execute(query_check, (session_id,))
        session = cursor.fetchone()

        if not session:
            return jsonify({"error": "Workout session not found"}), 404

        # Prepare the update query
        query_update = """
            UPDATE WorkoutSessions
            SET session_date = %s, session_time = %s, activity = %s
            WHERE session_id = %s
        """
        cursor.execute(query_update, (
            workout_data["session_date"],
            workout_data["session_time"],
            workout_data["activity"],
            session_id
        ))
        conn.commit()

        return jsonify({
            "message": "Workout session updated successfully",
            "session_id": session_id
        }), 200

    except Error as e:
        print(f"Database Error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# ----------------------------------------------------------------------------------
# Route to retrieve all workout sessions for a specific member
@app.route('/workouts/member/<int:member_id>', methods=['GET'])
def get_workouts_for_member(member_id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = conn.cursor()

        # Query to get all workout sessions for the specific member
        query = """
            SELECT session_id, session_date, session_time, activity 
            FROM WorkoutSessions 
            WHERE member_id = %s
        """
        cursor.execute(query, (member_id,))

        # Fetch all workout sessions for the member
        workouts = cursor.fetchall()

        if not workouts:
            return jsonify({"message": "No workouts found for this member"}), 404

        # Format the response for each workout
        workout_list = []
        for workout in workouts:
            session_id, session_date, session_time, activity = workout

            # Format the session_date to a more readable format
            formatted_session_date = session_date.strftime("%Y-%m-%d")  # Format as "YYYY-MM-DD"
            

            workout_list.append({
                "session_id": session_id,
                "session_date": formatted_session_date,
                "session_time": session_time,  # Format the session_time as "HH:MM AM/PM"
                "activity": activity
            })

        return jsonify({"workouts": workout_list}), 200

    except Error as e:
        print(f"Database Error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()



if __name__ == '__main__':
    app.run(debug=True)



