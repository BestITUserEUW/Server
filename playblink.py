import sys
import wave
import numpy as np
import pyaudio
import os
import subprocess
import contextlib
import paho.mqtt.client as mqtt
import threading

class playblink():
    def __init__(self,Filename,Client,Mask=False,Gui=False):
        self.kill = False
        self.chunk = 2048
        self.np_data = None
        self.client = Client
        self.waiter = threading.Event()
        self.mask = Mask
        self.gui = Gui
        self.filename = Filename
      
    
    def run(self,):
        t = threading.Thread(target=self.light_io)
        t.start()
        self.open_stream()
           
    def publish(self,topic,msg):
        self.client.loop_start()
        self.client.publish(topic,msg)
        self.client.loop_stop()  
            
    
    def light_io(self):
        while self.kill==False:
            self.waiter.wait()
            try:
                m = np.mean(np.absolute(self.np_data))
            except Exception as e:
                print(e)
            a = float(m/30)
            if self.mask:
                a += 100
                if a>255:
                    a = 255
                if a<110:
                    a=0
                self.publish("maske/val",a)
            elif self.gui:
                self.publish("gui/boomer/speak",m)
            else:
                if a>255:
                    a = 255
                if a<40:
                    a = 0
                self.publish("SEled/val",a)
                

    @contextlib.contextmanager
    def audio_stream(self,wf):
        p = pyaudio.PyAudio()

        stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True)

        yield stream

        stream.stop_stream()
        stream.close()
        p.terminate()

    def open_stream(self):
        try:
            wf = wave.open(self.filename, 'rb')
            width = np.int16
   
            with self.audio_stream(wf) as stream:
                data = wf.readframes(self.chunk)
                while data != b'':
                    stream.write(data)
                    self.np_data = np.frombuffer(data,dtype=width)
                    self.waiter.set()
                    self.waiter.clear()
                    data = wf.readframes(self.chunk)
        except Exception as e:
            print(e)
        self.kill = True
        self.np_data = None
        if self.mask:
            self.publish("maske/val",0)
        elif self.gui:
            self.publish("gui/boomer/speak","0")
        else:
            self.publish("SEled/val",0)

