from graphe import *
from utils import *
import os

class Main:
    def __init__(self,respectory:str="default") -> None :
        self.ma_key:str = respectory
        self.ma_respectory:list[tuple[str,str]] = open_file(f"../respectories/{self.ma_key}.txt")
        os.mkdir(f"../ressources/{self.ma_key}",True)
        self.init_directories()
        
    def init_directories(self) -> None :
        for directory in self.mfo_respectory_key():
            os.mkdir(f"../ressource/{self.ma_key}/{directory}",True)
            
    def mfp_main_loop(self) -> None :
        story = self.mfim_respectory()
        if story[1] == 'Quitter la bibliotèque': # cas d'arret
            return self.mfim_end()
        story = Graphe(self.ma_respectory[story[0]-1],story[1])
        story.gfi_load(f"../ressource/{self.ma_key}")
        story.gfp_main_loop()
        return self.mfp_main_loop() # cas récursif
        
        
        
            
# ========== | Fonctions Observatrices (FO) | ========== #
            
    def mfo_respectory_key(self) -> list[str] :
        return [key[0] for key in self.ma_respectory]
    
    def mfo_respectory_label(self) -> list[str] :
        return [label[1] for label in self.ma_respectory]
    
    def mfo_exist_respectory(self,name:str) -> bool :
        return name in self.ma_respectory_label() or name in self.ma_respectory_key()
    
# ========== | Fonctions Internes Simple (FIS) | ========== #
            
    def mfis_respectory_add(self, new:str) -> None :
        self.ma_respectory.append(new)
        os.mkdir(f"../ressources/{self.ma_key}/{new}",True)
        write_file(f"../respectories/{self.ma_key}.txt",self.ma_respectory)
        
    def mfis_respectory_edit(self,old:str,new:str) -> None :
        self.ma_respectory[self.ma_respectory.index(old)] = new
        write_file(f"../respectories/{self.ma_key}.txt",self.ma_respectory)
        os.rename(f"../ressources/{self.ma_key}/{old}",f"../ressources/{self.ma_key}/{new}")
        
    def mfis_respectory_del(self,name:str,only_path:bool=True) -> None :
        self.ma_respectory.pop(self.ma_respectory.index(name))
        write_file(f"../respectories/{self.ma_key}.txt",self.ma_respectory)
        if not only_path :
            files = os.listdir(f"../ressources/{self.ma_key}/{name}")
            for file in files:
                os.remove(f"../ressources/{self.ma_key}/{name}/{file}")
            os.rmdir(f"../ressources/{self.ma_key}/{name}")
                  
# ========== | Fonctions Internes Menu (FIM) | ========== #

# -------- | Debug | -------- #

    def mfim_respectory_add(self) -> str :
        sep(1,47)
        print(" O ========== |    ADDING NEW BOOK    | ========== O ")
        sep(1,47)
        name = double_confirmation("Choose new book's name : ","Confirme book's name :","\nError : Tow entry must be the same\n")
        self.mfis_respectory_add(name)
        return self.mfim_respectory_debug()
        
    def mfim_respectory_edit(self) -> str :
        sep(1,47)
        print(" O ========== |    EDIT BOOK'S NAME   | ========== O ")
        sep(1,47)
        for book in self.mfo_respectory_label() :
            print(book)
        old = while_input(self.ma_respectory,"Choose book's name to edit : ","Book not found.\nChoose book's name to edit : ")
        new = double_confirmation("Choose new name for book : ","Confirme new name for book :","\nError : Tow entry must be the same\n")
        self.mfis_respectory_edit(old,new)
        return self.mfim_respectory_debug()
        
    def mfim_respectory_del(self) -> str :
        sep(1,47)
        print(" O ========== |       DELET BOOK      | ========== O ")
        sep(1,47)
        for book in self.mfo_respectory_label() :
            print(book)
        name = while_input(self.ma_respectory,"Choose book to delet : ","Book not found.\nChoose book to delet : ")[1]
        definitive = while_input(YES+NO,"Definitive deletion (y/n) : ","Error.\nDefinitive deletion (y/n) : ")[1]
        if definitive in NO:
            definitive = False
        else :
            definitive = True
        self.mfis_respectory_del(name,definitive)
        return self.mfim_respectory_debug()
    
    def mfim_respectory_debug(self) -> tuple[int|str]:
        clear_screen()
        sep(1,47)
        print(" O ========== | MENU DEBUG RESPECTORY | ========== O ")
        sep(1,47)
        option = ["Add book","Del book","Edit book","Return to library"]
        for i,j in enumerate(option):
            print(f"{i} | {j}")
        choice = while_input(option,"Choose option : ","Error\nChoose option : ")[0]
        if choice == 3:
            return self.mfim_respectory() # cas d'arret
        if choice == 2:
            return self.mfim_respectory_edit() # appelle récursif
        if choice == 1:
            return self.mfim_respectory_del()
        return self.mfim_respectory_add()
            
# -------- | Main | -------- #         
        
    def mfim_respectory(self) -> tuple[int|str] :
        clear_screen()
        sep(1)
        print("Choisissez votre livre.")
        r = self.mfo_respectory_label()
        t = len(r)
        for i in range(t):
            print(f"{' ' * count_digit(t+1)-1}{i+1} | {r[i]}")
        print(f"{' ' * count_digit(t+1)-1}{t+1} | Quitter la bibliotèque")
        choice = while_input(
            ["MENU_DEBUG_RESPECTORY"]+r+["Quitter la bibliotèque"],
            "\nJ'ai fais mon choix : ",
            "\nVotre livre ne semble pas exister.\n Nous vous invitons à faire un nouveau choix : ")
        if choice[1] == "MENU_DEBUG_RESPECTORY":
            return self.mfim_respectory_debug() # finit toujours par rappeler mfim_respectory
        return choice # attention, les index sont décalés de 1 par rapport au repertoire
    
    def mfim_end(self) -> None:
        clear_screen()
        sep(1)
        print(" O =========== | Au Revoir | =========== O")
        sep(1)
        
    
        
            
    
        