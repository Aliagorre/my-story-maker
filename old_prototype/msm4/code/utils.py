from typing import Protocol, Any
import os

class BoolFunc(Protocol):
    def __call__(self, *args, **kwargs) -> bool: ...
    
class NoneFunc(Protocol):
    def __call__(self, *args, **kwargs) -> None: ...

def none() -> None :
    return None

def true() -> bool :
    return True

def false() -> bool :
    return False

def while_input(values:list[str],message_1:str,message_2:str) -> tuple[int,str] :
    '''
Tant que l'utilisateur ne renvoie pas une passibilité de values, on lui demande de recommencer.
On renvois la réponse de l'utilisateur et son index dans values.
'''
    v = lower_list(values.copy())
    choice = input(f"{message_1}").lower().replace(' ','')
    while not choice in values and not(choice.isdecimal() and 0 <= int(choice) < len(v)):
        choice = input(f"{message_2}").lower().replace(' ','')
    if choice.isdecimal() :
        index = int(choice)
        return (index,values[index])
    index = v.index(choice)
    return (index,values[index])

def double_confirmation(confirmation_1:str,confirmation_2:str,error_message:str) -> str:
    a = input(f"{confirmation_1}")
    b = input(f"{confirmation_2}")
    while a != b:
        print(error_message)
        a = input(f"{confirmation_1}")
        b = input(f"{confirmation_2}")
    return a
        

def open_file(path:str,default_value:str='None') -> Any :
    try :
        file = open(path, "r",encoding="utf8")
    except :
        file = open(path, "w",encoding="utf8")
        file.write(default_value)
        file = open(self.nom, "r",encoding="utf8")
    try :
        return ast.literal_eval(file.read())
    except :
        return file.read() 

def clear_screen() -> None:
    os.system('cls' if os.name == 'nt' else 'clear')
    
def write_file(path:str,entry:str) -> None :
    file = open(path, "w",encoding="utf8")
    file.write(entry)
    
def count_digit(n:int,base:int=10) -> int:
    if base < 1 :
        raise ValueError("count_digit : invalid base")
    if n < 0 :
        return 1 + count_digit(n)
    elif n < base :
        return 1
    return 1 + count_digit(n//base)

def sep(n:int=2,heigh:int=100,space:int=1,s_heigh:str="=",s_space:str="\n",bord:str="0") -> None:
    print(f"{s_space * space}")
    print(f"{bord} {s_heigh * heigh} {bord} \n" * n)
    print(f"{s_space * (space-1)}")
    
def lower_list(liste:list[str]) -> list[str]:
    return [i.lower().replace(' ','') for i in liste]

YES = ["oui","ou","oi","ui","o","u","i","true","yes","ye","es","ys","y","e","s"]
NO = ["non","no","on","nn","n","false"]

MENU_DEBUG_MAIN = [
    "Edit active noeud",
    "Go other noeud",
    "Continue",
    "Edit saves",
    "Main menu",
    ]
MENU_DEBUG_EDIT_MAIN = [
    "Edit description",
    "Edit links",
    "Edit events"
    ]
MENU_DEBUG_EDIT_DESC = [
    "Edit key parameter",
    "Edit label parameter",
    "Edit story parameter"
    ]
MENU_DEBUG_EDIT_KEY = [
    ""
    ]

