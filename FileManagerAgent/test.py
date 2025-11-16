
import os 
def make_file(folder,file_name,content:str|None=None):
    '''This is a tool to make a file
    Parameters:
    
    file_name
    '''
    if os.path.exists(f"c:/Users/Digi/Desktop/Python/{folder}"):
     file_path = os.path.join(f"c:/Users/Digi/Desktop/Python/{folder}", file_name)
     with open(file_path,"w") as f:
        f.write(content)
        return f"{file_name} added succesfully"


make_file("mahad","main.py","hello world")