
from flask import Flask
import psycopg2
import json

app = Flask(__name__)


def insert_data():
    # Database connection parameters - replace these with your actual database credentials
    conn = psycopg2.connect(
        dbname="tanvitree", user="postgres", password="postgresql", host="localhost"
    )
    cur = conn.cursor()

    # Load and parse the JSON data
    with open("./ExistingTreesFile.geojson", "r") as file:
        data = json.load(file)

    for feature in data['features']:
        # Check if coordinates array is not empty
        if feature['geometry']['coordinates']:
            # Assuming the first point is representative and exists
            longitude, latitude = feature['geometry']['coordinates'][0]

        # Insert data into the database, using the detailed coordinates
        cur.execute(
            """
            INSERT INTO tanvitree (type, height, age, latitude, longitude)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                feature["properties"]["Type"],
                feature["properties"]["Height"],
                feature["properties"]["Age"],
                latitude,  # Note the order is now latitude then longitude
                longitude,
            ),
        )

    # Commit and close the connection
    conn.commit()
    cur.close()
    conn.close()


@app.route("/add_tree")
def web_insert_data():
    insert_data()
    return "Data inserted successfully"


if __name__ == "__main__":
    app.run(debug=True)