from flask import Flask, jsonify, request, render_template
import paho.mqtt.client as mqtt_client
import json
import psycopg2 as pg

app = Flask(__name__)

block_counts = {
    "white" : 0,
    "red" : 0,
    "blue" : 0
    
    }

class SortingLine:
    def __init__(self, mqtt_host, mqtt_port, keep_alive):
        self.mqtt_host = mqtt_host
        self.mqtt_port = mqtt_port
        self.keep_alive = keep_alive
        self.mqttc = None
        self._init_mqtt()

    def _init_mqtt(self):
        try:
            self.mqttc = mqtt_client.Client()
            self.mqttc.connect(self.mqtt_host, self.mqtt_port, self.keep_alive)
            print("MQTT Client Initialized")
        except Exception as e:
            print("Error in MQTT Client Initialization: ", e)

    # def _init_db_client(self):
    #     try:
    #         self.db_client = pg.connect(self.db_host_address, sslmode="require")
    #         self.db_cursor = self.db_client.cursor()
    #         print("Database Connection Established")
    #     except (Exception, pg.DatabaseError) as error:
    #         print("Error in Database Initialization: ", error)

    def enable_disable_system(self, enable):
        mqtt_topic = "test/topic"
        dataObj = {"enable system": enable}
        jsondata = json.dumps(dataObj)
        self.mqttc.publish(mqtt_topic, jsondata)
        print("Controller Command Sent: ", "Enabled" if enable else "Disabled")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_conveyor():
    control.enable_disable_system(True)
    return jsonify({"message": "Conveyor Started"}), 200

@app.route('/stop', methods=['POST'])
def stop_conveyor():
    control.enable_disable_system(False)
    return jsonify({"message": "Conveyor Stopped"}), 200

if __name__ == '__main__':
    control = SortingLine('broker.hivemq.com', 1883, 60)
    app.run(debug=True, host='0.0.0.0', port=5001)
