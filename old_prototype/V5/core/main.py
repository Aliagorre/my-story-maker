from core.save import *
from core.metadata import *
from module import *

MAIN_MENU = [
    "Reprendre la partie",
    "Créer une sauvergarde",
    "Sauvergarder",
    "Retour à la bibliothèque",
    "Retour au bureau"
    ]

ISO  = ALL_VARS["init_story_option"]
DSO  = ALL_VARS["debug_stories_option"]
DlSO = ALL_VARS["delete_story_option"]
CSO  = ALL_VARS["create_story_option"]
RSO  = ALL_VARS["rename_story_option"]

ISaO  = ALL_VARS["init_save_option"] 
DSaO  = ALL_VARS["debug_saves_option"]
DlSaO = ALL_VARS["delete_save_option"]
CSaO  = ALL_VARS["create_save_option"]
RSaO  = ALL_VARS["rename_save_option"]

SSO = ALL_VARS["save_start_option"]

class Main:
    def __init__(self,default:bool=False) -> None :
        self.stories:list[str] = ["default_story"]
        self.saves  :list[str] = ["default"]
        self.story  :str = "default_story"
        self.save   :str = "default"
        make_directories("saves",self.stories)
        if not default :
            self.init()
        self.save_file:Save = Save(f"saves/{self.story}/{self.save}_save.py")
        
    def init(self) -> None :
        self.init_story()
        self.init_save()

    def init_story(self) -> None :
        clear_screen()
        self.stories = os.listdir(f"saves")
        self.story   = while_input(
            self.stories + list(ISO),
            "> Choisir le livre à ouvrir :\n> ",
            "> Entrer un titre valide :\n> ",
            "O === | STORIES SECETION | === O")
        if self.story == ":debug" :
            self.debug_stories()
            self.init_story()
        elif self.story in ISO :
            if ISO[self.story]() :
                self.init_story()

    def init_save(self) -> None :
        clear_screen()
        self.saves = os.listdir(f"saves/{self.story}")
        if not "__init__.py" in self.saves :
            create_save(f"saves/{self.story}/__init__.py",VERSION,ACTIVE_MODULES,False)
            self.init_save()
        else :
            self.saves = unsuffix_list(self.saves,"_save.py")
            self.saves = [save for save in self.saves if not save.startswith("__")]
            if not self.save :
                copy_save(f"saves/{self.story}/__init__.py", 
                        f"saves/{self.story}/default_save.py")
                self.init_save()
            else :
                #if "default" in self.saves :
                #    self.saves.remove("default")
                self.save  = while_input(
                    self.saves + ["Annuler"] + list(ISaO),
                    "> Choisir la sauvegarde à ouvrir :\n> ",
                    "> Entrer une sauvegarde valide :\n> ",
                    "O === | SAVES SECETION | === O")
                if self.save == ":debug" :
                    self.debug_saves()
                    self.init_save()
                elif self.save == "Annuler" :
                    self.init()
                elif self.save in ISaO :
                    if ISaO[self.save]() :
                        self.init_save()

    def debug_stories(self) -> None :
        debug_option = while_input(
            first_debug_option("livre") + ["Annuler"] + list(DSO),
            "> Choisir une option de débogage :\n> ",
            "> Entrer une option valide :\n> ",
            "O ### | STORIES DEBUG SELECTION | ### O")
        if debug_option == "Supprimer livre":
            self.del_story()
        elif debug_option == "Créer livre":
            self.create_story()
        elif debug_option == "Renommer livre":
            self.rename_story()
        elif debug_option in DSO :
            if DSO[debug_option]() :
                self.debug_saves()

    def debug_saves(self) -> None :
        debug_option = while_input(
            first_debug_option("sauvegarde"),
            "> Choisir une option de débogage :\n> ",
            "> Entrer une option valide :\n> ",
            "O ### | SAVE DEBUG SECETION | ### O")
        if debug_option == "Supprimer sauvegarde":
            self.del_save()
        elif debug_option == "Créer sauvegarde":
            self.create_save()
        elif debug_option == "Renommer sauvegarde":
            self.rename_save()
        elif debug_option in DSaO :
            if DSaO[debug_option]() :
                self.debug_saves()

    def del_save(self) -> None:
        working_element = while_input(
            self.saves + ["Annuler"] + list(DlSaO),
            f"> Choisir sauvegarde à supprimer :\n> ",
            f"> Entrer sauvegarde à supprimer valide :\n> ",
            f"O ### | DELETE SAVE DEBUG SECETION | ### O")
        if working_element not in [":debug","Annuler"] :
            if working_element in DlSaO :
                if DlSaO[working_element]() :
                    self.del_save()
            elif os.path.exists(f"saves/{self.story}/{working_element}_save.py") :
                remove_directory(f"saves/{self.story}/{working_element}_save.py")
            else :
                print("Error : debug_saves -> no file to delete found")
                self.del_save()
    
    def del_story(self) -> None:
        working_element = while_input(
            self.stories + ["Annuler"] + list(DlSO),
            f"> Choisir livre à supprimer :\n> ",
            f"> Entrer livre à supprimer valide :\n> ",
            f"O ### | DELETE STORY DEBUG SELECTION | ### O")
        if working_element not in [":debug","Annuler"] :
            if working_element in DlSO :
                if DlSO[working_element]() :
                    self.del_story()
            elif os.path.exists(f"saves/{working_element}") :
                remove_directory(f"saves/{working_element}")
            else :
                print("Error : debug_stories -> no directory to delete found")
                self.del_story()

    def create_save(self) -> None:
        new_name = double_confirmation(
            f"> Entrer le nom de la nouvelle sauvegarde :\n> ",
            f"> Confirmer le nom de la nouvelle sauvegarde :\n> ",
            "#>- Les deux noms doivent être identiques -<#")
        if new_name not in ["null","",":debug","Annuler"] + list(CSaO):
            if not os.path.exists(f"saves/{self.story}/{new_name}_save.py") :
                copy_save(f"saves/{self.story}/__init__.py",f"saves/{self.story}/{new_name}_save.py")
            else :
                print("Error : debug_saves -> file already exist")
                self.create_save()
        elif new_name in CSaO :
            if CSaO[new_name]() :
                self.create_save()

    def create_story(self) -> None:
        new_name = double_confirmation(
            f"> Entrer le nom du nouveau livre :\n> ",
            f"> Confirmer le nom du nouveau livre :\n> ",
            "#>- Les deux noms doivent être identiques -<#")
        if new_name not in ["null","",":debug","Annuler"] + list(CSO) :
            if not os.path.exists(f"saves/{new_name}") :
                make_directories(f"saves",[new_name])
            else :
                print("Error : debug_saves -> file already exist")
                self.create_story()
        elif new_name in CSO :
            if CSO[new_name]() :
                self.create_story()

    def rename_save(self) -> None :
        working_element = while_input(
            self.saves + ["Annuler"],
            f"> Choisir sauvegarde à renommer :\n> ",
            f"> Entrer sauvegarde à renommer valide :\n> ",
            f"O ### | RENAME SAVE DEBUG SELECTION | ### O")
        if working_element not in [":debug","Annuler"] + list(RSaO):
            new_name = double_confirmation(
                "> Entrer le nouveau nom :\n> ",
                "> Confirmer le nouveau nom :\n> ",
                "#>- Les deux noms doivent être identiques -<#")
            if new_name not in  ["null","Annuler"] + list(RSaO):
                if os.path.exists(f"saves/{self.story}/{working_element}_save.py") :
                    rename_save(f"saves/{self.story}/{working_element}_save.py",
                                f"saves/{self.story}/{new_name}_save.py")
                else :
                    print("Error : debug -> no file to rename found")
                    self.rename_save()
            elif new_name in RSaO :
                if RSaO[new_name]() :
                    self.rename_save()
        elif working_element in RSaO :
            RSaO[working_element]()

    def rename_saves(self,old_name,new_name):
        saves = os.listdir(f"saves/{old_name}")
        for save in saves :
            rename_save(f"saves/{old_name}/{save}",f"saves/{new_name}/{save}")
    
    def rename_story(self) -> None :
        working_element = while_input(
            self.stories + ["Annuler"],
            f"> Choisir livre à renommer :\n> ",
            f"> Entrer livre à renommer valide :\n> ",
            f"O ### | RENAME STORy DEBUG SELECTION | ### O")
        if working_element not in [":debug","Annuler"] + list(RSO):
            new_name = double_confirmation(
                "> Entrer le nouveau nom du livre :\n> ",
                "> Confirmer le nouveau nom du livre:\n> ",
                "#>- Les deux noms doivent être identiques -<#")
            if new_name not in ["null","Annuler"] + list(RSO) :
                if os.path.exists(f"saves/{working_element}") :
                    make_directories("saves",[new_name])
                    self.rename_saves(working_element, new_name)
                    remove_directory(f"saves/{working_element}")
                else :
                    print("Error : debug -> no file to rename found")
                    self.rename_save()
            elif new_name in RSO :
                RSO[new_name]()
        elif working_element in RSO :
            if RSO[working_element]() :
                self.rename_story()

    def start(self) -> None :
        clear_screen()
        choice = while_input(
            MAIN_MENU + list(SSO),
            "> Allez vous retournez au jeu ?\n> ",
            "> J'ai peur de ne vous avoir pas compris.\n> ",
            "O ### | MENU PRINCIPALE | ### O"
            )
        if choice == "Reprendre la partie":
            self.save_file.start()
            self.start()
        elif choice == "Créer une sauvergarde":
            self.create_save()
            self.start()
        elif choice == "Sauvergarder":
            self.save_file.write()
            self.start()
        elif choice == "Retour au bureau":
            clear_screen()
            print("---   Au revoir   ---\n")
            input()
            clear_screen()
        elif choice == "Retour à la bibliothèque":
            self.init()
            self.start()
        elif choice in SSO :
            if SSO[choice]() :
                self.start()
        
