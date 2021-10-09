import _sql
from threading import Thread, Event
import datetime
import psutil
import time
from playsound import playsound
import paho.mqtt.client as mqtt
import playblink as pb
import json
from queue import Queue

class Mqtt():
    def __init__(self):
        self.mqtt_IP = "192.168.178.36"
        self.sicherheit = True
        self.client = None
        self.last_msg = ""
        self.pingback = None
        self.debug = False
        # [keepalive,running processes]
        self.server_service_data = [None,None]
        # publish data for Gui
        self.gui_stream = False
        self.wait_stream = Event()
        self.wait_stream.set()
        self.sound_queue = Queue()

    def list_esp(self):
        esp_sql = _sql.Esp_Status()
        return esp_sql.status_abrufen()
    
    def ssData(self):
        return self.server_service_data


    def alarme_heute(self):
        ah = _sql.Alarm_handler()
        l = ah.alarme_heute()
        if len(l)==0:
            return []
        return l

    def mqtt_msg(self,msg):
        if self.debug:
            print("[MQTT] : '{}' | {}".format(msg,datetime.datetime.now()))
    
    def publish(self,topic,msg):
        self.client.publish(topic,msg)

    def connect_mqtt(self): 
        self.client = mqtt.Client()
        self.client.max_inflight_messages_set(30)
        self.client.connect(self.mqtt_IP,1883,60)
        self.client.on_connect = self.connect_to_broker
        self.client.on_message = self.mqtt_on_message
        self.publish("connection/callback","1")
        self.client.loop_start()
        Thread(target=self.send_data).start()
        Thread(target=self.sound).start()

    def sound(self):
        while True:
            if not self.sound_queue.empty():
                client = mqtt.Client()
                client.max_inflight_messages_set(30)
                client.connect(self.mqtt_IP,1883,60)
                client.loop_start()
                play = pb.playblink("F:/ServerService/audios_wav/"+self.sound_queue.get(),client)
                play.run()
                client.loop_stop()
                
            

    def connect_to_broker(self,client,userdata,flags,rc):
        self.client.subscribe("#")
        self.mqtt_msg(" Connected to Topic: '{}' with result Code: {}\n".format("#", rc))
    
    def mqtt_on_message(self,client,userdata,msg):
        msg_str = str(msg.payload.decode("utf-8"))
        topic = msg.topic
        if "ping_rcv" in topic:
            for i in range(len(topic)):
                if topic[i] == "/":
                    name = topic[i+1:len(topic)]
                    self.pingback = name
                    break

        elif "sicherheit/nachricht" == topic:
            if msg_str == "1":
                self.sicherheit = True
                self.mqtt_msg("Sicherheit :[An]")
            elif msg_str == "0":
                self.sicherheit = False
                self.mqtt_msg("Sicherheit :[Aus]")
    
        elif "alarm" in topic:
            for i in range(len(topic)):
                if topic[i] == "/":
                    name = topic[i+1:len(topic)]
                    break
            if self.sicherheit==True:
                self.mqtt_msg("[KRITSCH]: '{}' wurde ausgelöst...".format(name))
                esp_db = _sql.Alarm_handler("Ausgelöst", name ,str(datetime.datetime.now()))
                esp_db.neuer_alarm()
                self.mqtt_msg("[DATENBANK]: '{}' Alarm erfolgreich eingetragen...".format(name))
                self.sound_queue.put("leave_or_gas.wav")
         
        elif topic == "button":
            if msg_str == "power":
                self.publish("power/windows1","1")
            elif msg_str == "reset":
                if self.sicherheit == True:
                    self.sicherheit = False
                    self.sound_queue.put("male_sicherheit_aus.wav")
                else:
                    self.sicherheit = True
                    self.sound_queue.put("male_sicherheit_an.wav")

        elif "task" in topic:
            if msg_str == "1":
                self.sound_queue.put("windows_xp_startup.wav")
        
            elif msg_str == "0":
                self.sound_queue.put("cornholio.wav")
                

        elif "verbindung" in topic:
            for i in range(len(topic)):
                if topic[i] == "/":
                    name = topic[i+1:len(topic)]
                    if _sql.Esp_Status.suchen_esp(name)!=None:
                        self.mqtt_msg("sql Eintrag: name: '{}' status: {}".format(name,msg_str))
                        esp_status_db = _sql.Esp_Status(name)
                        esp_status_db.status_aktualisieren(int(msg_str))
                    else:
                        esp_status_db = _sql.Esp_Status(name)
                        esp_status_db.neuer_esp()
        
        elif "gui/data/" in topic:
            if topic == "gui/data/open":    
                if msg_str == "esp":
                    self.open_stream(self.list_esp,msg_str)
                elif msg_str == "processes":
                    self.open_stream(self.ssData,msg_str)
                
            elif topic == "gui/data/close":
                self.gui_stream = False

            elif topic == "gui/data/once":
                if msg_str == "alarms_today":
                   self.open_stream(self.alarme_heute,msg_str)
                if msg_str == "sicherheit": 
                    self.publish("gui/server/sicherheit",str(self.sicherheit))
        
        elif topic == "gui/connection":
            self.publish("gui/connection/callback","1")
  
    def open_stream(self, task, topic, once=False):
        self.gui_stream = False
        self.wait_stream.wait()
        self.wait_stream.clear()
        self.gui_stream = True
        if once:
            j = {"data":task(),"topic":topic}
            self.publish("gui/server/data",json.dumps(j))
            self.gui_stream = False
            self.wait_stream.set()
        else:
            t = Thread(target=self.server_data,args=(task,topic))
            t.start()
 
    def server_data(self, task, topic):
        while self.gui_stream:
            j = {"data":task(),"topic":topic}
            self.publish("gui/server/data",json.dumps(j))
            time.sleep(0.5)
        self.wait_stream.set()
        

    def server_data_json(self):
        json_data ={
            "cpu": str(psutil.cpu_percent(interval=1)),
            "ram": str(psutil.virtual_memory().percent)
        }
        return json.dumps(json_data)

    def send_data(self):
        while True:
            self.publish("gui/server/usage",self.server_data_json())
            time.sleep(0.5)

