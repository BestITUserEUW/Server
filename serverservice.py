import os
import sys
from psutil import process_iter
from playsound import playsound
from threading import Event,Thread
from time import sleep
import paho.mqtt.client as mqtt
import MQTT as mq
import _sql
import updater 
import playblink as pb



class serverservice():
    def __init__(self):
        self.process_pfad = "F:/ServerService/processes"
        self.log_pfad = "F:/ServerService/logs"
        self.update_pfad = "F:/ServerService/update"
        self.archive_pfad = "F:/ServerService/update/archive"
        self.audio_pfad = "F:/ServerService/audios_wav/"
        self.debug = False
        self._console = True
        self.mqtt_handler = None
        self.keep_alive = True
        self._running_processes = []
        self._running_threads = []
        self.eUpdate = Event()
        self.eKeep_alive = Event()
        self.eWait_for_sound = Event()
        self.eWait_for_sound.set()
        
    
    def mqtt_connect(self):
        client = mqtt.Client()
        client.connect("192.168.178.36",1883,60)
        return client
    
    def publish_mqtt(self,topic,msg):
        client = self.mqtt_connect()
        client.loop_start()
        client.publish(topic,msg)
        client.loop_stop()

    def start(self):
        self.start_t_arg("Sound-Thread",self.ps,"female_system_start.wav")
        self.mqtt_handler = mq.Mqtt()
        self.mqtt_handler.connect_mqtt()
        self.initialize_processes()
        self.start_t("Alive-Service-1",self.keep_alive_service)
        self.start_t_arg("Sound-Thread",self.ps,"female_system_startet.wav")
        if self._console:
            self.console()
    
    def console(self):
        root = False
        while True:
            if root:
                eingabe = input("(root) {}>".format(os.getcwd()))
                split = eingabe.split()
                if eingabe == "newp":
                    self.new_process()
                
                elif eingabe == "update":
                    self.update_process()
                elif "start" in eingabe:
                    os.system("start C:/ServerService/{}".format(split[1]))

                elif "debug" in eingabe:
                    arg = split[1]
                    if arg == "main":
                        if self.debug:
                            self.debug = False
                        else:
                            self.debug = True
                        if arg == "mqtt":
                            if self.mqtt_handler.debug:
                                self.mqtt_handler.debug = False
                            else:
                                self.mqtt_handler.debug = True
                elif eingabe == "keepalive":
                    if self.keep_alive == True:
                        self.keep_alive == False
                    else:
                        self.keep_alive = True
                
                elif "kill" in eingabe:
                    arg = split[1]
                    self.kill_process(arg)
            
                elif "open" in eingabe:
                    arg = split[1]
                    self.open_process(arg)

                elif "ls" in eingabe:
                    if "esp" in eingabe:
                        self.list_esp()
                    elif "ps" in eingabe:
                        self.list_processes()
                    else:
                        self.list_dir()

                elif "chdir" in eingabe:
                    try:
                        arg = split[1]
                        os.chdir(arg)
                    except Exception as e:
                        self.debug_msg("System", "{}".format(e))
                
                elif "sicherheit" in eingabe:
                    arg = split[1]
                    if arg == "an":
                        self.mqtt_handler.sicherheit = True
                    if arg == "aus":
                        self.mqtt_handler.sicherheit = False
                
                elif "ping" in eingabe:
                    if len(split)==2:
                        self.ping_esp(split[1])
                    elif len(split)==3:
                        self.ping_esp(split[1],timeout=int(split[2]))
                    elif len(split)==4:
                        self.ping_esp(split[1],timeout=int(split[2]),intervall=float(split[3]))

                elif "root" in eingabe:
                        root = False

                elif eingabe == "help":
                    print("""Liste verfügbar CMDS:
                       
                      - update                                          
                      - newp                                                   
                      - keepalive [{}]
                      - sicherheit 'an/aus' [{}]     
                      - debug 'main/mqtt' MQTT [?] MAIN [{}]
                      - kill 'process' 
                      - open 'process' 
                      - ls 'dir'/esp/ps
                      - chdir 'dir'                        
                      - ping 'name' 'timeout' 'intervall'
                      - mqtt 
                     
                      
                                     
                       >Copyrights(c) 2020 Best IT Man Somalia<
                      """.format(self.eUpdate._flag,self.mqtt_handler.sicherheit,self.debug))
                else:
                    print("CMD: '{}' ist nicht im System...".format(eingabe))
            else:
                eingabe = input("{}>".format(os.getcwd()))
                split = eingabe.split()
                if "root" in eingabe:
                    if split[1] == "pornhub":
                        root = True
                    else:
                        print("Falsches passwort...")
                else:
                    print("Verpiss dich von meinem PC...")
            
    # Threads
    def start_t(self, _name,_target):
        thread = Thread(name=_name, target=_target)
        self._running_threads.append(thread)
        thread.start()          
        
        
    def start_t_arg(self, _name,_target,arg):
        thread = Thread(name=_name, target=_target,args=(arg,))
        self._running_threads.append(thread)
        thread.start()
    

    def ps(self, audio):
        if not self.debug:
            self.eWait_for_sound.wait()
            self.eWait_for_sound.clear()
            audio_pfad = self.audio_pfad+audio
            client = self.mqtt_connect()
            play = pb.playblink(audio_pfad,client)
            play.run()
            self.eWait_for_sound.set()

    def debug_msg(self, name, msg,ol=False):
        if self.debug:
            if ol:
                Cmsg = "[{}] : {}".format(name.upper(), msg)
                print(Cmsg,end="")
                print("\b" *len(Cmsg),end="", flush=True)
            else:
                print("[{}] : {}".format(name.upper(), msg))
    
    def check_esp(self):
        self.debug_msg("PING","initializing...")
        esp_sql = _sql.Esp_Status()
        esp_list = esp_sql.status_abrufen()
        for esp in esp_list:
            self.ping_esp(esp[1])

    
    def ping_esp(self,name,timeout=5,intervall=1):
        pingback = False
        self.publish_mqtt("ping_snd/{}".format(name),1)
        self.debug_msg("PING","Pinged Esp: {} with Timeout: {}sec".format(name,timeout))
        for i in range(timeout):
            if self.mqtt_handler.pingback!=None:
                pingback = True
                while self.mqtt_handler.pingback!=None:
                    self.mqtt_handler.pingback = None
                break
            self.debug_msg("PING","no pingback after {}sec".format(i),ol=True)
            sleep(intervall)
        if pingback:
            self.debug_msg("PING","received ping from {} after {}sec...".format(name,i))
            esp_status_db = _sql.Esp_Status(name)
            esp_status_db.status_aktualisieren(1)
        else:
            self.debug_msg("PING","did not receive ping from {} after {}sec...".format(name,timeout))
            esp_status_db = _sql.Esp_Status(name)
            esp_status_db.status_aktualisieren(0)
       
    # List Zeug #
   
    def list_processes(self):
        for process in self._running_processes:
            print(process)

    def list_esp(self):
        esp_sql = _sql.Esp_Status()
        esp_list = esp_sql.status_abrufen()
        for esp in esp_list:
            print("Name: {} Status: {}".format(esp[1],esp[0]))

   
    def list_dir(self):
        cwd_list = os.listdir()
        for _file in cwd_list:
            print("~ "+_file)
    
    # Prozesse Zeug

    def new_process(self):
        process = input("[UPDATER]: Process:")
        self.debug_msg("UPDATER","Waiting for keepalive to stop...")
        self.eKeep_alive.wait()
        self.eUpdate.clear()
        self.debug_msg("UPDATER","Integrating new Process...")
        ud = updater.update()
        ud.new_py_process(process)
        self.eUpdate.set()
        self.debug_msg("UPDATER","Update Done...")


    def update_process(self):
        process = input("Process:")
        self.debug_msg("UPDATER","Waiting for keepalive to stop...")
        self.eKeep_alive.wait()
        self.eUpdate.clear()
        self.debug_msg("UPDATER","Updating Process...")
        ud = updater.update()
        ud.update_py_process(process)
        self.eUpdate.set()
        self.debug_msg("UPDATER","Update Done...")

    def kill_process(self, process):
        self.debug_msg("SYSTEM","Prozess {} wird Gestoppt...".format(process))
        try:
            pid = self.look_for_process(process,pid=True)
            os.system("taskkill /F /pid {}".format(pid))
            self.debug_msg("System","{} gestoppt...".format(process))
            self._running_processes.remove(process)
            print(self. _running_processes)       
        except Exception as e:
            self.debug_msg("SYSTEM","Prozess {} konnte nicht gestartet werden Exception: {}...".format(process,e))

    def open_process(self, process):
        os.chdir(self.process_pfad)
        self.debug_msg("SYSTEM","Prozess {} wird gestartet...".format(process))
        try:
            os.system("start {}".format(process))
            self._running_processes.append(process)
        except Exception as e:
            self.debug_msg("SYSTEM","Prozess {} konnte nicht gestartet werden Exception: {}...".format(process,e))
    

    def initialize_processes(self):
        os.chdir(self.process_pfad)
        if not os.listdir(self.process_pfad):
            self.debug_msg("SYSTEM","Prozesse Ordner ist leer")
        else:    
            self.debug_msg("SYSTEM","starte Prozesse...")
            processes = os.listdir()
            for process in processes:
                if "exe" in process:
                    if not self.look_for_process(process):
                        self.open_process(process)
        self.eUpdate.set()
    


    def look_for_process(self,prozess,pid=False):
        for process in process_iter():
            if process.name() in prozess:
                if pid:
                    return process.pid
                else:
                    return True
        return False   
    
    # Keepalive Service 

    def keep_alive_service(self):
        while True:
            while self.eUpdate.is_set() and self.keep_alive:
                self.eKeep_alive.clear()
                self.mqtt_handler.server_service_data[0] = self.keep_alive
                self.mqtt_handler.server_service_data[1] = self._running_processes
                self.check_esp()
                running_processes = os.listdir(self.process_pfad)
                for process in running_processes:
                    if "exe" in process and running_processes.count != 0:
                            for process2 in self._running_processes:
                                if process2 == process:   
                                    if not self.look_for_process(process):
                                        self.open_process(process)

                self.eKeep_alive.set()
                sleep(1)
                

            

if __name__ == "__main__":
    print("Server Service v0.0.1")
    ss = serverservice()
    ss.start()
   
