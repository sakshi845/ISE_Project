#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/10/22 18:32
# @Author  : Fred Livingston (fjliving@ncsu.edu)

# Cntr + Shift + P -> Python: Select Interpreter -> Python 3.11.9 64-bit ('smartm': conda) -> Enter
from flask import Flask
from flask import render_template
from flask import request, jsonify
import paho.mqtt.client as mqtt_client
import json
from flask_classful import FlaskView
import psycopg as pg
import pandas as pd

# Dependencies
#pip install Flask # for web server
#pip install Flask-Classful # for class-based views
#pip install psycopg2    # for postgresql
#pip install pandas  # for data manipulation
#pip install paho-mqtt # for mqtt


app = Flask(__name__)

class ClientApp(FlaskView):
    def __init__(self, mqtt_host_address, db_host_address):
        # instantiate an object:
        self.mqtt_host =  mqtt_host_address 
        self.mqtt_port = 1883
        self.mqtt_keep_alive = 60
        self.db_host_address = db_host_address

        # Initialize MQTT Client
        self. _init_mqtt()
        print("MQTT Client Initialized")

        # Initialize DB Client
        self._init_db_client()
        print("DB Client Initialized")
   

        @app.route('/control', methods=['GET', 'POST', 'DELETE', 'PATCH'])
        def index():
            # send form to the user
            if request.method == 'GET':
                return render_template('widget_mqtt_postgres.html')
    
            if request.method == 'POST':
                action = request.form.get("action") 
                print(action)
        
            if(action == "Start Controller"):
                self._enabled_disable_system(True)
        
            if(action == "Stop Controller"):
                self._enabled_disable_system(False)

            if(action == "Query DB"):
                df = self._queryDB()
                return render_template('widget_mqtt_postgres.html', tables=[df.to_html(classes='data')], titles=df.columns.values ) 
            
            return render_template('widget_mqtt_postgres.html')
        
    def _init_mqtt(self):
        # Initialize MQTT Client
        try:
            self.mqttc = mqtt_client.Client()
            self.mqttc.connect(self.mqtt_host, self.mqtt_port, self.mqtt_keep_alive)
        except Exception as e:
            print("Error in MQTT Client Initialization: ", e)

    def _init_db_client(self):
        self.db_client = pg.connect(self.db_host_address,sslmode="require")
        try:
            self.db_cursor = self.db_client.cursor()
            print("Connection Established")
        except (Exception, pg.DatabaseError) as error:
            print(error)

    def _enabled_disable_system(self, enable):
        mqtt_topic = "FWH/ISE589finalproj/systemcommand"
        dataObj={}
        dataObj["enable system"] = enable
        jsondata = json.dumps(dataObj)
        self. _init_mqtt()
        self.mqttc.publish(mqtt_topic, jsondata)
        print ("Controller: ", enable)

    def _queryDB(self):
        qCmd = """SELECT t.* FROM public."sensor_data5" t LIMIT 100 """
        df = pd.read_sql_query(qCmd, self.db_client) # read the query into a pandas dataframe
        print(df) # print the dataframe
        # Now that we have the data as a dataframe, we can manipulate it as needed
        # and utilize it in our web application and machine learning models
        return df

# mqtt_host = "10.155.14.88" Can be used for local testing        
#mqtt_host = "test.mosquitto.org"
mqtt_host = "broker.hivemq.com"
db_host = "postgresql://sorting_line_project_ise_user:RVDVnL6nRPM8ym5OnP2HMbUE9h2pcALL@dpg-ct347f5umphs73do9d60-a.oregon-postgres.render.com/sorting_line_project_ise"

app_client = ClientApp(mqtt_host, db_host)
ClientApp.register(app) # Register the class with the app
# app.run(debug=True) # Run the app locally
app.run(debug=True, host='0.0.0.0', port=5001) # Render the app on the network
