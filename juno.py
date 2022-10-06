from vosk import Model, KaldiRecognizer
import pyttsx3
from playsound import playsound
import paho.mqtt.client as mqtt
import os
from threading import Thread, Event
import time
import pyaudio
import json
import sys
from winsound import Beep
import playblink as pb

class Boomer():
    def __init__(self):
        print("Boomer Version: 0.01")
        self.audio_pfad = "F:/ServerService/audios_wav/"
        self.debug_msg("system","initalizing...")
        self.shutdown = False
        self.mqtt_client = None
        self.sicherung = False
        self.sr_model = None
        self.name = "juno"
        self.s_keywords = ["abmelden","passwort"]
        self.keywords = ["bin zu hause","ich gehe","starte computer eins","starte computer zwei","starte computer drei"]
        self.wait_for_sound = Event()
        self.wait_for_sound.set()
  
        self.converter = pyttsx3.init()
        self.converter.setProperty('voice', "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_DE-DE_HEDDA_11.0")
        self.converter.setProperty('rate', 180)

    def speak(self,text):
        self.converter.say(text)
        self.converter.runAndWait()
        
    def start_t(self, _name,_target):
        thread = Thread(name=_name, target=_target)
        thread.start()          
        
        
    def start_t_arg(self, _name,_target,arg):
        thread = Thread(name=_name, target=_target,args=(arg,))
        thread.start()
    
    def ps(self, audio):
        self.wait_for_sound.wait()
        self.wait_for_sound.clear()
        audio_pfad = self.audio_pfad+audio
        play = pb.playblink(audio_pfad,self.mqtt_client,Gui=True)
        play.run()
        self.wait_for_sound.set()

    def debug_msg(self, name, msg):
        print("[{}] : '{}'".format(name.upper(), msg))
    
    def publish(self,topic,msg):
        client = self.mqtt_client
        client.loop_start()
        client.publish(topic,msg)
        client.loop_stop()

    def mqtt_connect(self):
        self.debug_msg("mqtt","connecting to Mqtt...")
        client = mqtt.Client()
        client.connect("192.168.178.36",1883,60)
        self.mqtt_client = client
        self.debug_msg("mqtt","connected...")
     

    def initialize_model(self):
        self.publish("gui/boomer/task","loading model...")
        if not os.path.exists("F:/ServerService/rec-de"):
            self.debug_msg("system","no model found")
            exit (1) 
        
        self.sr_model = Model("F:/ServerService/rec-de")   
        self.publish("gui/boomer/task","model succesfully loaded...")  

    

    def mic_listen(self):
        text = ""
        open_stream = True
        p = pyaudio.PyAudio()
        while True:
            if open_stream:
                self.publish("gui/boomer/task","opening stream...")
                stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
                stream.start_stream()
                open_stream = False
            
            elif len(text)!=0:
                try:
                    stream.stop_stream()
                except Exception:
                    pass
                return text
            rec = KaldiRecognizer(self.sr_model, 16000)
            start_time = time.time()
            self.publish("gui/boomer/eye","0")
            while True:
                try:
                    data = stream.read(4000)
                    if len(data) == 0:
                        break

                    elif time.time() - start_time>7:
                            break
                    else:
                        rec.AcceptWaveform(data)
                        output = json.loads(rec.PartialResult())
                        output = output["partial"]
                        self.debug_msg("Kaldi_r","Output: "+output)
                        if self.name in output:
                            self.publish("gui/boomer/eye","1")
                            
                        if self.name not in output and len(output)>7:
                            break

                        elif self.name in output and ' '.join(str(output).split()[1:len(output)-1]) in self.keywords:
                            self.debug_msg("Kaldi_R","got keyword")
                            text = output
                            break
                        
                except Exception as e:
                    self.publish("gui/boomer/task",str(e))
                    try:
                        stream.stop_stream()
                    except Exception:
                        pass
                    open_stream = True
                    break

    def menu(self):
        while not self.shutdown:
            audio_str = self.mic_listen()
            self.publish("gui/boomer/task","Execute: {}".format(audio_str))
            if "starte computer" in audio_str:
                if "eins" in audio_str:
                    self.debug_msg("admin","Computer eins wird gestartet...")
                    self.start_t_arg("Sound-Thread",self.ps,"windows_xp_startup.wav")
                    self.publish("power/windows1","1")
                elif "zwei" in audio_str:
                    self.debug_msg("admin","Computer zwei wird gestartet...")
                    self.start_t_arg("Sound-Thread",self.ps,"windows_xp_startup.wav")
                    self.publish("power/ubuntu1","1")
                elif "drei" in audio_str:
                    self.debug_msg("admin","Computer drei wird gestartet...")
                    self.start_t_arg("Sound-Thread",self.ps,"windows_xp_startup.wav")
                    self.publish("power/windows2","1")
                
            elif "bin zuhause" in audio_str:
                self.start_t_arg("Sound-Thread",self.ps,"cornholio_bier.wav")
                self.publish("sicherheit/nachricht","0")
                self.debug_msg("admin","[Sicherheit]: Aus")
                self.start_t_arg("Sound-Thread",self.ps,"male_sicherheit_aus.wav")

            elif "ich gehe" in audio_str:
                self.start_t_arg("Sound-Thread",self.ps,"cornholio_drohung.wav")
                self.publish("sicherheit/nachricht","1")
                self.debug_msg("admin","[Sicherheit]: An")
                self.start_t_arg("Sound-Thread",self.ps,"male_sicherheit_an.wav")
            
            elif "sicherheit an" in audio_str:
                self.publish("sicherheit/nachricht","1")
                self.debug_msg("admin","[Sicherheit]: An")
                self.start_t_arg("Sound-Thread",self.ps,"male_sicherheit_an.wav")
                
                
            elif "sicherheit aus" in audio_str:
                self.publish("sicherheit/nachricht","0")
                self.debug_msg("admin","[Sicherheit]: Aus")
                self.start_t_arg("Sound-Thread",self.ps,"male_sicherheit_aus.wav")
                
            else:
                self.speak("Das konnte ich leider nicht verstehen")
                
    def start(self):
        self.mqtt_connect()
        while self.mqtt_client == None:
            pass
        self.initialize_model()
        self.menu()
          


if __name__=="__main__":
    print("Juno v0.1")
    bm = Boomer()
    bm.start()
    
    
