import sqlite3
import time
import datetime

class Alarm_handler():
    def __init__(self,alarmmeldung="",ort="",datum = None ):
        self.alarmmeldung = alarmmeldung
        self.ort = ort
        self.datum = datum 
        self.db = "F:/ServerService/database/Sy_database.db"
    
    def neuer_alarm(self):
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        c.execute("INSERT INTO Alarme VALUES (:alarmmeldung, :Ort, :Datum)", {"alarmmeldung":self.alarmmeldung, "Ort":self.ort, "Datum":self.datum})
        conn.commit()
        conn.close()
        
    def alarme_heute(self):
        alarme_heute = []
        heute = datetime.datetime.now()
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        c.execute("SELECT * FROM Alarme")
        alarme = c.fetchall()
        for i in range(len(alarme)):
            alarm = alarme[i]
            datum = datetime.datetime.strptime(alarm[2],"%Y-%m-%d %H:%M:%S.%f")
            if datum.day == heute.day:
                alarme_heute.append(alarm)
        return alarme_heute
             
        

    def alle_alarme_loeschen(self):
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        c.execute('DELETE FROM Alarme;',)
        print("Es wurden {} Alarme von Alarme gelöscht".format(c.rowcount))
        conn.commit()
        conn.close()
 

    def alarme_alle(self):
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        c.execute("SELECT * FROM Alarme")
        return c.fetchall() 


class Schule():
    def __init__(self,typ,info,datum):
        self.typ = typ
        self.info = info
        self.datum = datum
        self.db = "F:/ServerService/database/Sy_database.db"
    
    def neuer_schuleintrag(self):
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        c.execute("INSERT INTO Schule VALUES (:Typ, :Info, :Datum)", {"Typ":self.typ, "Ort":self.info, "Datum":self.datum})
        conn.commit()
        conn.close()
    
    def schuleintraege_abrufen(self):
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        c.execute("SELECT * FROM Schule")
        return c.fetchall()

class Termin():
    def __init__(self,termin,ort,datum):
        self.termin = termin
        self.ort = ort
        self.datum = datum
        self.db = "F:/ServerService/database/Sy_database.db"
    
    def neuer_termin(self):
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        c.execute("INSERT INTO Termin VALUES (:Termin, :Ort, :Datum)", {"Termin":self.termin, "Ort":self.ort, "Datum":self.datum})
        conn.commit()
        conn.close()
    
    def termine_abrufen(self):
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        c.execute("SELECT * FROM Termine")
        return c.fetchall()
    #In Arbeit
    
    def termin_loeschen(self):
        print("X")

class Esp_Status():
    def __init__(self,name=""):
        self.name = name
        self.db = "F:/ServerService/database/Sy_database.db"

    def status_aktualisieren(self,status):
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        c.execute("UPDATE Esp_Status SET Status = :Status WHERE name = :name", {"Status":status, "name":self.name})
        conn.commit()
        conn.close()

    def status_abrufen(self):
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        c.execute("SELECT * FROM Esp_Status")
        return c.fetchall()
    
    def neuer_esp(self):
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        c.execute("INSERT INTO Esp_Status VALUES (:Status, :Name)", {"Status":1,"Name":self.name})
        conn.commit()
        conn.close()

    @staticmethod
    def suchen_esp(name):
        conn = sqlite3.connect("F:/ServerService/database/Sy_database.db")
        c = conn.cursor()
        c.execute("SELECT * FROM Esp_Status WHERE Name=?",(name,))
        return c.fetchone()

class Wecker():
    def __init__(self):
        pass

