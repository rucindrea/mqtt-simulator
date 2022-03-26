import time
import json
import random
import threading
import paho.mqtt.client as mqtt

class SensorTopic:
    def __init__(self, broker_url, broker_port, sensor_serial, topic_url, topic_data, retain_probability, trigger=False, trigger_value=0):
        self.broker_url = broker_url
        self.broker_port = broker_port
        self.topic_url = topic_url + "/" + sensor_serial
        self.topic_data = topic_data
        self.retain_probability = retain_probability
        self.client = None
        self.trigger = trigger
        self.trigger_value = trigger_value
        self.command_topic = self.topic_url + '/in'
        self.command_data = {}

    def connect(self):
        self.client = mqtt.Client(self.topic_url, clean_session=True, transport='tcp')
        self.client.on_publish = self.on_publish
        self.client.on_message = self.on_message
        self.client.connect(self.broker_url, self.broker_port)
        self.client.subscribe(topic=self.command_topic)
        self.client.loop_start()

    def run(self):
        pass

    def disconnect(self):
        self.client.loop_end()
        self.client.disconnect()

    def on_publish(self, client, userdata, result):
        print(f'[{time.strftime("%H:%M:%S")}] Data published on: {self.topic_url} :: {self.old_payload}')

    def on_message(self, client, userdata, message):
        self.command_data = json.loads(message.payload.decode('utf-8'))
        print(f'[{time.strftime("%H:%M:%S")}] Received message on: {self.topic_url} :: {self.command_data}')

class TopicSensorInfo(SensorTopic, threading.Thread):
    def __init__(self, broker_url, broker_port, sensor_serial, topic_url, topic_data):
        SensorTopic.__init__(self, broker_url, broker_port, sensor_serial, topic_url, topic_data, retain_probability=0)
        threading.Thread.__init__(self, args = (), kwargs = None)
        self.time_interval = 0
        self.old_payload = topic_data

    def run(self):
        self.connect()
        
    def on_message(self, client, userdata, message):
        self.command_data = json.loads(message.payload.decode('utf-8'))
        print(f'[{time.strftime("%H:%M:%S")}] Received message on sensor info topic: {self.topic_url} :: {self.command_data}')
        self.client.publish(topic=self.topic_url, payload=json.dumps(self.old_payload), qos=2, retain= False)
    

class TopicAutoPublish(SensorTopic, threading.Thread):
    def __init__(self, broker_url, broker_port, sensor_serial, topic_url, topic_data, retain_probability, time_interval):
        SensorTopic.__init__(self, broker_url, broker_port, sensor_serial, topic_url, topic_data, retain_probability)
        threading.Thread.__init__(self, args = (), kwargs = None)
        self.time_interval = time_interval
        self.old_payload = None

    def run(self):
        self.connect()
        while True:
            if self.command_data == {}:
                payload = self.generate_data()
                self.old_payload = payload
                self.client.publish(topic=self.topic_url, payload=json.dumps(payload), qos=2, retain= False)
            else:
                self.old_payload = self.command_data
                self.client.publish(topic=self.topic_url, payload=json.dumps(self.command_data), qos=2, retain= False)
            time.sleep(self.time_interval)

    def generate_data(self):
        payload = {}
        
        if self.old_payload == None:
            # generate initial data
            for data in self.topic_data:
                if data['TYPE'] == 'int':
                    payload[data['NAME']] = random.randint(data['MIN_VALUE'], data['MAX_VALUE'])
                elif data['TYPE'] == 'float':
                    payload[data['NAME']] = random.uniform(data['MIN_VALUE'], data['MAX_VALUE'])
                elif data['TYPE'] == 'bool':
                    payload[data['NAME']] = random.choice([True, False])
                elif data['TYPE'] == 'trigger':
                    if payload[data["TRIGGER_NAME"]] < data["TRIGGER_LEVEL"]:
                        payload[data['NAME']] = False
                    else:
                        payload[data['NAME']] = True
        else:
            # generate next data
            payload = self.old_payload
            for data in self.topic_data:
                if random.random() > (1 - self.retain_probability):
                    continue
                if data['TYPE'] == 'bool':
                    payload[data['NAME']] = not payload[data['NAME']]
                elif data['TYPE'] == 'trigger':
                    if payload[data["TRIGGER_NAME"]] < data["TRIGGER_LEVEL"]:
                        payload[data['NAME']] = False
                    else:
                        payload[data['NAME']] = True
                else:
                    step = random.uniform(-data['MAX_STEP'], data['MAX_STEP']) 
                    step = round(step) if data['TYPE'] == 'int' else step
                    payload[data['NAME']] = max(payload[data['NAME']]+step, data['MIN_VALUE']) if step < 0 else min(payload[data['NAME']]+step, data['MAX_VALUE'])

        return payload
