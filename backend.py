

# last modification: 02/04/24
# Description: Back end code for webapp of tree management

from flask import Flask, request, jsonify, session
import logging
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
import psycopg2
from psycopg2.extras import RealDictCursor
from flask_cors import CORS
from flask_login import current_user
from collections import defaultdict

# logging statements to track the flow of code and execution status
logging.basicConfig(filename='app.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


app = Flask(__name__)
CORS(app)
app.config["SECRET_KEY"] = "groupet104"  # Replace with your actual secret key

bcrypt = Bcrypt(app) # these 2 lines of codes are configuring flask extension to the flask instance "app"
login_manager = LoginManager(app)

# Database connection parameters
DATABASE_URL = "postgresql://postgres:postgresql@localhost/tanviuser"


def get_db_connection():
    return psycopg2.connect(DATABASE_URL) 


class User(UserMixin):
    def __init__(self, id_, username, is_admin):
        self.id = id_
        self.username = username
        self.is_admin = is_admin


@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM tanviuser WHERE id = %s", (user_id,))
    user_record = cur.fetchone()
    cur.close()
    conn.close()
    if user_record:
        return User(
            id_=user_record["id"],
            username=user_record["username"],
            is_admin=user_record["is_admin"],
        )
    return None


@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username")
    password = request.form.get("password")

    if not username or not password:
        return (
            jsonify({"status": "fail", "message": "Missing username or password"}),
            400,
        )

    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO tanviuser (username, password, is_admin) VALUES (%s, %s, FALSE) RETURNING id",
            (username, hashed_password),
        )
        user_id = cur.fetchone()[0]
        conn.commit()
    except psycopg2.IntegrityError:
        conn.rollback()
        return jsonify({"status": "fail", "message": "Username already exists"}), 400
    finally:
        cur.close()
        conn.close()

    return jsonify({"status": "success", "user_id": user_id}), 201


@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM tanviuser WHERE username = %s", (username,))
    user_record = cur.fetchone()
    cur.close()
    conn.close()

    if user_record and bcrypt.check_password_hash(user_record["password"], password):
        user = User(
            id_=user_record["id"],
            username=user_record["username"],
            is_admin=user_record["is_admin"],
        )
        login_user(user)
        session["user_id"] = user.id  # Store user_id in session
        return jsonify({"status": "success", "is_admin": user.is_admin}), 200
    else:
        return (
            jsonify({"status": "fail", "message": "Invalid username or password"}),
            401,
        )


@app.route("/logout", methods=["GET"])
@login_required
def logout():
    logout_user()
    return jsonify({"status": "success", "message": "Logged out"}), 200


@app.route("/get_tree_data")
def get_tree_data():
    # Separate function to connect to the tree data database
    def get_tree_db_connection():
        # You'll need to update these parameters to match your tree database
        TREE_DATABASE_URL = "postgresql://postgres:postgresql@localhost/tanvitree"
        return psycopg2.connect(TREE_DATABASE_URL)

    # Fetch tree data from the database and convert it to GeoJSON format
    conn = get_tree_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM tanvitree")  # Replace with your tree data table name
    tree_data = cur.fetchall()
    cur.close()
    conn.close()

    # Convert the tree data to GeoJSON
    features = []
    for tree in tree_data:
        feature = {
            "type": "Feature",
            "properties": {
                "Type": tree["type"],  # Column names should match your database schema
                "Height": tree["height"],
                "Age": tree["age"],
            },
            "geometry": {
                "type": "Point",
                "coordinates": [tree["longitude"], tree["latitude"]],
            },
        }
        features.append(feature)

    geojson = {"type": "FeatureCollection", "features": features}

    return jsonify(geojson)


@app.route("/get_tree_types", methods=["GET"])
def get_tree_types():
    def get_tree_db_connection():
        # You'll need to update these parameters to match your tree database
        TREE_DATABASE_URL = "postgresql://postgres:postgresql@localhost/tanvitree"
        return psycopg2.connect(TREE_DATABASE_URL)

    conn = (
        get_tree_db_connection()
    )  # make sure to define this function if it's not already defined
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT type FROM tanvitree")
    types = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return jsonify(types)


@app.route("/get_filtered_tree_data", methods=["POST"])
def get_filtered_tree_data():
    filters = request.json
    query = "SELECT * FROM tanvitree WHERE true"
    parameters = []

    if filters.get("treeType"):
        query += " AND type = %s"
        parameters.append(filters["treeType"])
    if filters.get("minAge"):
        query += " AND age >= %s"
        parameters.append(filters["minAge"])
    if filters.get("maxAge"):
        query += " AND age <= %s"
        parameters.append(filters["maxAge"])
    if filters.get("minHeight"):
        query += " AND height >= %s"
        parameters.append(filters["minHeight"])
    if filters.get("maxHeight"):
        query += " AND height <= %s"
        parameters.append(filters["maxHeight"])

    def get_tree_db_connection():
        # You'll need to update these parameters to match your tree database
        TREE_DATABASE_URL = "postgresql://postgres:postgresql@localhost/tanvitree"
        return psycopg2.connect(TREE_DATABASE_URL)

    conn = get_tree_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(query, parameters)
    tree_data = cur.fetchall()
    cur.close()
    conn.close()

    features = []
    for tree in tree_data:
        feature = {
            "type": "Feature",
            "properties": {
                "Type": tree["type"],  # Column names should match your database schema
                "Height": tree["height"],
                "Age": tree["age"],
            },
            "geometry": {
                "type": "Point",
                "coordinates": [tree["longitude"], tree["latitude"]],
            },
        }
        features.append(feature)

    geojson = {"type": "FeatureCollection", "features": features}

    return jsonify(geojson)

from collections import defaultdict

# Dictionary to store vote counts for each tree name
from collections import defaultdict

# Initialize tree_votes as a defaultdict of defaultdicts
from flask import Flask, request, jsonify
import psycopg2
import psycopg2.extras
from collections import defaultdict

app = Flask(__name__)

# Debug logging setup
import logging
logging.basicConfig(level=logging.DEBUG)

# Dictionary to store tree votes
tree_votes = defaultdict(lambda: defaultdict(int))

@app.route("/add_tree", methods=["POST"])
def add_tree():
    # Log the start of the function
    app.logger.debug("add_tree function called")

    data = request.json
    app.logger.debug("Received JSON data: %s", data)

    TREE_DATABASE_URL = "postgresql://postgres:postgresql@localhost/tanvitree"
    conn = psycopg2.connect(TREE_DATABASE_URL)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    try:
        tree_name = data["name"]
        tree_height = float(data["height"])
        tree_age = int(data["age"])
        tree_latitude = float(data["latitude"])
        tree_longitude = float(data["longitude"])
    except (ValueError, TypeError, KeyError) as e:
        # Log the error
        app.logger.error("Invalid input data: %s", str(e))
        return (
            jsonify({"status": "fail", "message": "Invalid input data", "error": str(e)}),
            400,
        )
    
    # Log the validated data
    app.logger.debug("Validated tree data: name=%s, height=%s, age=%s, latitude=%s, longitude=%s",
                     tree_name, tree_height, tree_age, tree_latitude, tree_longitude)

    # Initialize the inner defaultdict for the tree name if it doesn't exist
    if tree_name not in tree_votes:
        tree_votes[tree_name] = defaultdict(int)
    
    # Increment the vote count for the tree type of the tree name
    tree_votes[tree_name]["votes"] += 1

    # Log the current vote count for the tree name
    app.logger.debug("Current vote count for tree %s: %s", tree_name, tree_votes[tree_name]["votes"])
    
    # Check if the tree has received 3 votes
    if tree_votes[tree_name]["votes"] >= 3:
        # Determine the tree type with the maximum votes
        max_tree_type = max(tree_votes[tree_name], key=tree_votes[tree_name].get)
        
        try:
            # Insert the tree request into the database with the tree type that received the maximum votes
            cur.execute(
                "INSERT INTO tree_requests (tree_name, tree_type, height, age, latitude, longitude) VALUES (%s, %s, %s, %s, %s, %s)",
                (tree_name, max_tree_type, tree_height, tree_age, tree_latitude, tree_longitude),
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            # Log the error
            app.logger.error("Failed to add the tree request: %s", str(e))
            return (
                jsonify({"status": "fail", "message": "Failed to add the tree request", "error": str(e)}),
                500,
            )
        finally:
            cur.close()
            conn.close()
        
        # Log the successful addition of the tree request
        app.logger.debug("Tree request added successfully")
        return jsonify({"status": "success", "message": "Tree request added successfully"}), 201
    else:
        # Log the current status of the vote
        app.logger.debug("Vote received for tree %s: %s", tree_name, tree_votes[tree_name]["votes"])
        return jsonify({"status": "success", "message": f"Thank you. Vote no. {tree_votes[tree_name]['votes']} for this tree has been received."}), 200

if __name__ == "__main__":
    app.run(debug=True)


# Route to delete a tree. Only accessible by admin users.
@app.route("/delete_tree", methods=["POST"])
@login_required

def delete_tree():
    tree_id = request.json.get("tree_id")
    
    # Check if tree_id is provided
    if not tree_id:
        error_message = "Tree ID is required"
        logging.error(error_message)
        return jsonify({"status": "fail", "message": "Tree ID is required"}), 400

    TREE_DATABASE_URL = "postgresql://postgres:postgresql@localhost/tanviuser"

    conn = psycopg2.connect(TREE_DATABASE_URL)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
    try:
        # If the user is an admin, delete the tree immediately
        if current_user.is_admin:
            cur.execute("DELETE FROM tanvitree WHERE id = %s", (tree_id,))
            conn.commit()
            message = "Tree deleted successfully"
            logging.info(message)

        # If the user is not an admin, log the deletion request
        else:
            user_id = current_user.id
            cur.execute(
                "INSERT INTO tree_deletion_requests (tree_id, user_id, status) VALUES (%s, %s, %s)",
                (tree_id, user_id, "pending"),
            )
            conn.commit()
            message = "Deletion request submitted successfully"
            logging.info(message)

            

    except Exception as e:
        conn.rollback()
        error_message = f"Error processing your request: {str(e)}"
        logging.error(error_message)
        return (
            jsonify(
                {
                    "status": "fail",
                    "message": "Error processing your request",
                    "error": str(e),
                }
            ),
            500,
        )
    finally:
        cur.close()
        conn.close()

    return jsonify({"status": "success", "message": message}), 200


if __name__ == "__main__":
    app.run(debug=True)