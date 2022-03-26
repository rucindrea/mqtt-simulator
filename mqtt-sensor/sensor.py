import json
from sensor_topic import TopicAutoPublish, TopicSensorInfo

class Sensor:
    def __init__(self, settings_file):
        self.broker_url = None
        self.broker_port = None
        self.auto_publish_topics = []
        self.subscribe_topics = []
        self.load_settings(settings_file)

    def load_settings(self, settings_file):
        with open(settings_file) as json_file:
            config = json.load(json_file)
            self.broker_url = config['BROKER_URL']
            self.broker_port = config['BROKER_PORT']
            self.info_topic = config['SENSOR_INFO_TOPIC']
            self.sensor_name = config['SENSOR_NAME']
            self.sensor_type = config['SENSOR_TYPE']
            self.sensor_serial = config['SENSOR_SERIAL']
            self.sensor_info_topic = config['SENSOR_INFO_TOPIC']
            self.info_data = {
                "name": self.sensor_name,
                "sw_version": config['SENSOR_SW_VERSION'],
                "hw_version": config['SENSOR_HW_VERSION'],
                "type": config['SENSOR_TYPE'],
                "serial": config['SENSOR_SERIAL'],
                
            }
            for topic in config['SENSOR_VALUES']:
                topic_data = topic['DATA']
                topic_time_interval = topic['TIME_INTERVAL']
                topic_retain_probability = topic['RETAIN_PROBABILITY']
                self.auto_publish_topics.append(TopicAutoPublish(self.broker_url, self.broker_port, self.sensor_serial, topic['NAME'], topic_data, topic_retain_probability, topic_time_interval))
            self.info_topic_object = TopicSensorInfo(self.broker_url, self.broker_port, self.sensor_serial, self.info_topic, self.info_data)

    def run(self):
        for topic in self.auto_publish_topics:
            print(f'Starting: {topic.topic_url} ...')
            topic.start()
        self.info_topic_object.start()
        
        

    def stop(self):
        for topic in self.auto_publish_topics:
            print(f'Stopping: {topic.topic_url} ...')
            topic.stop() 
