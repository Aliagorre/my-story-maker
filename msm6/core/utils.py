from typing import Protocol, Any, Callable
import os
import shutil

YES = {"oui","ou","oi","ui","o","u","i","true","yes","ye","es","ys","y","e","s"}
NO = {"non","no","on","nn","n","false"}

class BoolFunc(Protocol):
    def __call__(self, *args, **kwargs) -> bool: ...
    
class NoneFunc(Protocol):
    def __call__(self, *args, **kwargs) -> None: ...

def none(*args, **kwargs) -> None :
    return None

def true(*args, **kwargs) -> bool :
    return True

def false(*args, **kwargs) -> bool :
    return False

def priority() -> None :
    pass

def enumerate_list(liste:list) -> None :
    print()
    for i,j in enumerate(liste):
        print(f"{i+1}{' '*(len(liste)//10)} | {j}")
    print()

def while_input(values:list[str],message_1:str,message_2:str,titre:str="",
                hidden_value:list[str]=[],apply:NoneFunc=none) -> str :
    clear_screen()
    apply()
    #sep()
    print(f"{titre}")
    enumerate_list(values)
    strict_hidden = lower_list(hidden_value.copy())
    strict_values = lower_list(values.copy())
    strict_choice = input(f"{message_1}").lower().replace(' ','')
    while (not (strict_choice in strict_values) 
           and not (strict_choice in strict_hidden)
           and (strict_choice != ':debug' )
           and not(strict_choice.isdecimal() 
                   and 0 <= int(strict_choice) <= len(strict_values))):
        clear_screen()
        #sep()
        print(f"{titre}")
        enumerate_list(values)
        strict_choice = input(f"{message_2}").lower().replace(' ','')
    if strict_choice.isdecimal() :
        index = int(strict_choice)
        if not(index):
            return ":debug"
        return values[index-1]
    if strict_choice == ":debug" :
        return ":debug"
    if strict_choice in strict_hidden :
        index = strict_hidden.index(strict_choice)
        return hidden_value[index]
    index = strict_values.index(strict_choice)
    return values[index]

def double_confirmation(confirmation_1:str,confirmation_2:str,error_message:str="") -> str:
    a = input(f"{confirmation_1}")
    b = input(f"{confirmation_2}")
    while a != b:
        sep(1,20)
        print(error_message)
        a = input(f"{confirmation_1}")
        b = input(f"{confirmation_2}")
    return a
        
def open_file(path:str,default_value:str='None') -> str :
    if os.path.exists(path) :
        file = open(path, "r",encoding="utf8")
    else :
        file = open(path, "w",encoding="utf8")
        file.write(default_value)
        file = open(path, "r",encoding="utf8")
    to_return =  file.read() 
    file.close()
    return to_return

def make_file(path:str,default_value:str='None') -> None :
    if not os.path.exists(path) :
        file = open(path, "w",encoding="utf8")
        file.write(default_value)
    file.close()
    
def make_directories(path,directory_list:list[str]) -> None :
    for directory in directory_list:
        if not os.path.exists(f"{path}/{directory}") :
            os.mkdir(f"{path}/{directory}",True)

def remove_directory(path:str) -> None :
    if os.path.isdir(path):
        shutil.rmtree(path)
    elif os.path.isfile(path):
        os.remove(path)
    else:
        print(f"Error: '{path}' does not exist")

def clear_screen() -> None:
    os.system('cls' if os.name == 'nt' else 'clear')
    
def write_file(path:str,entry:str) -> None :
    file = open(path, "w",encoding="utf8")
    file.write(entry)
    file.close()
    
def count_digit(n:int,base:int=10) -> int:
    if base < 1 :
        raise ValueError("count_digit : invalid base")
    if n < 0 :
        return 1 + count_digit(n)
    elif n < base :
        return 1
    return 1 + count_digit(n//base)

def sep(n:int=1,heigh:int=100,space:int=1,s_heigh:str="=",bord:str="O") -> None:
    print()
    print(f"{bord} {s_heigh * heigh} {bord} \n" * n,end='')
    print("\n" * space,end='')
    
def lower_list(liste:list[str]) -> list[str]:
    return [i.lower().replace(' ','') for i in liste]

def unsuffix_list(liste:list[str],suffix) -> list[str]:
    return [i.removesuffix(suffix) for i in liste]

def first_debug_option(name) -> list[str]:
    return  [
        f"Supprimer {name}",
        f"Créer {name}",
        f"Renommer {name}"]


