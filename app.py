from flask import Flask, render_template, request, redirect, url_for
import paho.mqtt.client as mqtt_client
from sqlalchemy import create_engine,text
from datetime import datetime
import pytz

import pandas as pd
import json

app = Flask(__name__)

# MQTT Configuration
#mqtt_host = "broker.hivemq.com"
mqtt_host = "test.mosquitto.org"
mqtt_port = 1883
mqtt_topic = "FWH/ISE589FinalProj/SystemCommand"

# SQLAlchemy Configuration
#db_uri = "postgresql://sm_grp1_db_user:w7WVszIjZUoq4KY09rfKQNzTIVq5WBrQ@dpg-csps6clumphs73dtgoq0-a.ohio-postgres.render.com/sm_grp1_db"
db_uri = "postgresql://sorting_line_project_ise_user:RVDVnL6nRPM8ym5OnP2HMbUE9h2pcALL@dpg-ct347f5umphs73do9d60-a.oregon-postgres.render.com/sorting_line_project_ise"
engine = create_engine(db_uri)

# Fetch Latest Counters
def fetch_latest_counters():
    query = text('SELECT redcountervalue, whitecountervalue, unknowncountervalue, systemenable, sr_no FROM public.sensor_data ORDER BY sr_no DESC LIMIT 1;')
    try:
        with engine.connect() as connection:
            result = connection.execute(query).fetchone()

            # Set the specific timezone
            timezone = pytz.timezone("America/New_York")  # Change this to your desired timezone
            localized_time = datetime.now(pytz.utc).astimezone(timezone)

            if result:
                status = result[3].strip().lower() == "true"
                return {
                    "red": result[0] if result[0] is not None else 0,
                    "white": result[1] if result[1] is not None else 0,
                    "unknown": result[2] if result[2] is not None else 0,
                    "status": status,
                    "last_checked_time": localized_time.strftime('%I:%M:%S %p on %B %d, %Y')  # 12-hour time with AM/PM
                }
    except Exception as e:
        print(f"Error fetching counters: {e}")

        # Set default time with specific timezone
        timezone = pytz.timezone("America/New_York")
        localized_time = datetime.now(pytz.utc).astimezone(timezone)
        return {
            "red": 0,
            "white": 0,
            "unknown": 0,
            "status": False,
            "last_checked_time": localized_time.strftime('%I:%M:%S %p on %B %d, %Y')
        }


# Query Database
def query_database():
    query = text('SELECT * FROM public."sensor_data" LIMIT 100')
    try:
        return pd.read_sql_query(query, engine)
    except Exception as e:
        print(f"Database error: {e}")
        return pd.DataFrame()

# Root Route
@app.route('/')
def root():
    # Redirect to /control
    return redirect(url_for('index'))

# Control Route
@app.route('/control', methods=['GET', 'POST'])
def index():
    current_counters = fetch_latest_counters()

    # Always ensure `last_checked_time` is passed
    last_checked_time = current_counters.get("last_checked_time", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    if request.method == 'GET':
        return render_template(
            'widget_mqtt_postgres_new.html',
            counters=current_counters,
            last_checked_time=last_checked_time
        )
    
    if request.method == 'POST':
        action = request.form.get("action")

        if action == "Query DB":
            df = query_database()
            table_data = {
                "columns": df.columns.values.tolist(),
                "data": df.values.tolist()
            }
            return render_template(
                'widget_mqtt_postgres_new.html',
                tables=[table_data],
                titles=["Sensor Data"],
                counters=current_counters,
                last_checked_time=last_checked_time
            )

        elif action == "Activate System":
            publish_message(True)
        elif action == "Deactivate System":
            publish_message(False)

        # Render the page again with updated counters and timestamp
        current_counters = fetch_latest_counters()
        last_checked_time = current_counters.get("last_checked_time", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        return render_template(
            'widget_mqtt_postgres_new.html',
            counters=current_counters,
            last_checked_time=last_checked_time
        )

    return render_template('widget_mqtt_postgres_new.html', counters=current_counters, last_checked_time=last_checked_time)





# Publish MQTT Message
def publish_message(enable):
    client = mqtt_client.Client()
    try:
        client.connect(mqtt_host, mqtt_port)
        data = {"enable system": enable}
        client.publish(mqtt_topic, json.dumps(data))
    except Exception as e:
        print(f"Error publishing MQTT message: {e}")

# Run the App
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
