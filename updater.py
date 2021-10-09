import shutil, os
import ctypes, sys
import psutil


class update():
    def __init__(self):
        self.process_dir = "C:/ServerService/processes"
        self.update_dir = "C:/Scripts"
    
    def __kill_process(self, p_name):
        for process in psutil.process_iter():
            if process.name() in p_name:
                process.terminate()
    
    
    def update_py_process(self,process): 
        os.chdir(self.update_dir)
        name_split = process.split(".")
        exe_dir = self.process_dir+"/"+name_split[0]+".exe"
        p_spec = "{}.spec".format(name_split[0])
        spec_dir = "C:/ServerService/spec"+"/"+p_spec
        if "py" in process:
            self.__kill_process(name_split[0]+".exe")
            os.remove(exe_dir)
            os.remove(spec_dir)
            os.system("pyinstaller --onefile {} --distpath {}".format(process,self.process_dir))
            shutil.move(p_spec,"C:/ServerService/spec")
            shutil.rmtree(self.update_dir+"/build", ignore_errors=True)
           
            
                        
              
    def new_py_process(self,process):
        os.chdir(self.update_dir)
        if "py" in process:
            os.system("pyinstaller --onefile {} --distpath {}".format(process,self.process_dir))
            p_name = process.split(".")
            p_spec = "{}.spec".format(p_name[0])
            shutil.move(p_spec,"C:/ServerService/spec")
            shutil.rmtree(self.update_dir+"/build", ignore_errors=True)
            


