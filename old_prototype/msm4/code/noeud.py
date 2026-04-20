
from event import *
from utils import *
from typing import Any #, Callable, Literal, Union # Callable[[T1,T2,T3,...],type1|type2]

class Noeud:
    def __init__(self,key:str="none",label:str="none",text:str="none") -> None :
        self.na_children:dict[str,"Noeud"] = {} # clefs des noeuds enfants dans le graphe : noeud
        self.na_parents :dict[str,"Noeud"] = {} # clefs des noeuds parentsts dans le graphe : noeud
        self.na_key  :str = key   # identifiant unique de l'objet
        self.na_label:str = label # nom afficher dans les choix
        self.na_text :str = text  # petit texte affiché de base en conséquence du choix
        self.na_active       :BoolFunc = true  # condition à évaluer comme vrai pour rendre le noeuds accessible
        self.na_event        :NoneFunc = none  # l'event se déclenche après na_text
        self.na_active_event :BoolFunc = true  # condition suplémentaire pour activer l'event du noeuds.
        self.na_effect       :NoneFunc = none  # effet invisible ou non qui sera évalué quand le noeuds est parcourus
        self.na_active_effect:BoolFunc = false # condition suplémentaire pour activer l'effect du noeuds.
        self.na_data  :dict[str,Any] = {} # dictionnaire de donnée propre au noeud, utilisé pour les conditions ou autres.
        
        
    def __str__(self) -> str :
        str({"na_children":self.nfo_children_keys(),
             "na_parents" :self.nfo_children_keys(),
             "na_key"  :self.na_key,
             "na_label":self.na_label,
             "na_text" :self.na_text,
             "na_active"      :self.na_active.__name__,
             "na_event"       :self.na_event.__name__,
             "na_active_event":self.na_active_event.__name__,
             "na_effect"      :self.na_effect.__name__,
             "na_active_effect":self.na_active_effect.__name__,
             "na_data":f""}) # trouver le chemin
        
# ========== | Fonctions Observatrices (FO) | ========== #

# -------- | Noeud adjacent | -------- #

#### children ####

    def nfo_children(self) -> dict[str,"Noeud"] :
        return self.na_children
    
    def nfo_children_keys(self) -> list[str]:
        return list(self.na_children.keys())
    
    def nfo_children_values(self) -> list["Noeud"]:
        return list(self.na_children.values())
    
    def nfo_children_items(self) -> list[tuple[str,"Noeud"]] :
        return list(self.na_children.items())
    
    def nfo_children_value(self,key:str) -> "Noeud":
        return self.na_children[key]
    
    def nfo_active_children(self) -> list["Noeud"] :
        return [noeud for noeud in self.nfo_children_values() if noeud.nfo_is_activable()]
    
#### parents ####
    
    def nfo_parents(self) -> dict[str,"Noeud"] :
        return self.na_parents
    
    def nfo_parents_keys(self) -> list[str]:
        return list(self.na_parents.keys())
    
    def nfo_parents_values(self) -> list["Noeud"]:
        return list(self.na_parents.values())
    
    def nfo_parents_items(self) -> list[tuple[str,"Noeud"]] :
        return list(self.na_parents.items())
    
    def nfo_parents_value(self,key:str) -> "Noeud":
        return self.na_parents[key]
    
    def nfo_active_parents(self) -> list["Noeud"] :
        return [noeud for noeud in self.nfo_parents_values() if noeud.nfo_is_activable()]
    
# -------- | Descriptif | -------- #

    def nfo_key(self) -> str :
        return self.na_key
    
    def nfo_label(self) -> str :
        return self.na_label
        
    def nfo_text(self) -> str :
        return self.na_text
    
# -------- | event | -------- #
    
    def nfo_active(self) -> BoolFunc :
        return self.na_active
    
    def nfo_active_name(self) -> str :
        return str(self.na_active)[10:-23]
    
    def nfo_event(self) -> NoneFunc :
        return self.na_event
    
    def nfo_event_name(self) -> str :
        return str(self.na_event)[10:-23]
    
    def nfo_active_event(self) -> BoolFunc :
        return self.na_active_event
    
    def nfo_active_event_name(self) -> str :
        return str(self.na_active_event)[10:-23]
    
    def nfo_effect(self) -> NoneFunc :
        return self.na_effect
    
    def nfo_effect_name(self) -> str :
        return str(self.na_effect)[10:-23]
    
    def nfo_active_effect(self) -> BoolFunc :
        return self.na_active_effect
    
    def nfo_active_effect_name(self) -> str :
        return str(self.na_active_effect)[10:-23]
    
#### events_test ####

    def nfo_is_activable(self) -> bool :
        return self.na_active()
    
    def nfo_is_event_activable(self) -> bool :
        return self.na_active_event()
    
    def nfo_is_effect_activable(self) -> bool :
        return self.na_active_effect()
    
    def nfo_has_event(self) -> bool :
        return self.na_event is not none
    
    def nfo_has_effect(self) -> bool :
        return self.na_effect is not none
    
# -------- | datas | -------- #

    def nfo_data(self) -> dict[str,Any]:
        return self.na_data
    
    def nfo_data_keys(self) -> list[str]:
        return list(self.na_data.keys())
    
    def nfo_data_values(self) -> list[Any]:
        return list(self.na_data.values())
    
    def nfo_data_value(self,key:str) -> Any:
        return self.na_data[key]
    
# -------- | autres | -------- #
    
# ========== | Fonctions Observatrices Avancées (FOA) | ========== #

    def nfoa_take_active_children(self,key:int) -> "Noeud" :
        list_active_children = self.nfo_active_children() # On calcule pas plusieurs fois la même chose
        index = len(list_active_children) # liste["Noeud"]
        if not 0<=key<=index :
            raise ValueError(f"{self.na_key}.nfia_take_active_children() : key out off range")
        return list_active_children[key]
    
    def nfoa_take_children(self,key:int) -> "Noeud" :
        list_children = self.nfo_children_values() # On calcule pas plusieurs fois la même chose
        index = len(list_children) # liste["Noeud"]
        if not 0<=key<=index :
            raise ValueError(f"{self.na_key}.nfia_take_children() : key out off range")
        return list_children[key]
        
    def nfoa_take_active_parents(self,key:int) -> "Noeud" :
        list_active_parents = self.nfo_active_parents() # On calcule pas plusieurs fois la même chose
        index = len(list_active_parents) # liste["Noeud"]
        if not 0<=key<=index :
            raise ValueError(f"{self.na_key}.nfia_take_active_parents() : key out off range")
        return list_active_parents[key]
    
    def nfoa_take_parents(self,key:int) -> "Noeud" :
        list_parents = self.nfo_parents_values() # On calcule pas plusieurs fois la même chose
        index = len(list_parents) # liste["Noeud"]
        if not 0<=key<=index :
            raise ValueError(f"{self.na_key}.nfia_take_parents() : key out off range")
        return list_parents[key]
    
# ========== | Fonctions Observatrices Menu (FOM) | ========== #
    
    def nfom_active_children(self) -> "Noeud":
        list_active_children = self.nfo_active_children()
        index = len(list_active_children)
        for i in range(index):
            print(f"{i+1} | {list_active_children[i]}")
        choice = while_input([str(i) for i in range(index+1)],
                             "Choisissez ce que vous faisez : ",
                             "Choisissez ce que vous faisez : ")
        if choice != "0":
            return list_active_children[int(choice)-1]
        else :
            return self.nfim_main()
        
        
# ========== | Fonctions Internes Simple (FIS) | ========== #

# -------- Reset -------- #

    def nfis_reset_all(self) -> None :
        '''
Remet les valeurs par défaut au noeud
'''
        self.na_children = {} 
        self.na_parents  = {} 
        self.na_key      = "none"  
        self.na_label    = "none"
        self.na_text     = "none"  
        self.na_active   = true  
        self.na_event    = none  
        self.na_active_event = true  
        self.na_effect   = none  
        self.na_active_effect= false
        self.na_data     = {}
        
    def nfis_reset_children(self) -> None :
        self.na_children = {}
    
    def nfis_rest_parents(self) -> None :
        self.na_parents = {}
        
    def nfis_reset_key(self) -> None :
        self.na_key = "none"
        
    def nfis_reset_label(self) -> None :
        self.na_label = "none"
        
    def nfis_reset_text(self) -> None :
        self.na_text = "none"
        
    def nfis_reset_active(self) -> None :
        self.na_active = true
        
    def nfis_reset_event(self) -> None :
        self.na_event = none
        
    def nfis_reset_active_event(self) -> None :
        self.na_active_event = true
    
    def nfis_reset_effect(self) -> None :
        self.na_effect = none
        
    def nfis_reset_active_effect(self) -> None :
        self.na_active_effect = false
        
    def nfis_reset_data(self) -> None :
        self.na_data = {}

# -------- | Noeud adjacent | -------- #
        
    def nfis_children_new(self,new:"Noeud") -> None :
        self.na_children[new.na_key] = new
        
    def nfis_children_del_key(self,key:str) -> None :
        del self.na_children[key]
        
    def nfis_children_pop_key(self,key:str) -> "Noeud" :
        return self.na_children.pop(key,Noeud())
        
    def nfis_children_del_value(self,value:"Noeud") -> None :
        key = next((k for k, v in self.na_children.items() if v == value), None)
        if key is not None:
            del self.na_children[key]
            
    def nfis_children_pop_value(self,value:"Noeud") -> "Noeud" :
        key = next((k for k, v in self.na_children.items() if v == value), None)
        if key is not None:
            return self.na_children.pop(key)
        return Noeud()
    
    def nfis_parents_new(self,new:"Noeud") -> None :
        self.na_parents[new.na_key] = new
        
    def nfis_parents_del_key(self,key:str) -> None :
        del self.na_parents[key]
        
    def nfis_parents_pop_key(self,key:str) -> "Noeud" :
        return self.na_parents.pop(key,Noeud())
        
    def nfis_parents_del_value(self,value:"Noeud") -> None :
        key = next((k for k, v in self.na_parents.items() if v == value), None)
        if key is not None:
            del self.na_parents[key]
            
    def nfis_parents_pop_value(self,value:"Noeud") -> "Noeud" :
        key = next((k for k, v in self.na_parents.items() if v == value), None)
        if key is not None:
            return self.na_parents.pop(key)
        return Noeud()
        
# -------- | Descriptif | -------- #

    def nfis_key_edit(self,new:str) -> None :
        self.na_key = new
    
    def nfis_label_edit(self,new:str) -> None :
        self.na_label = new
        
    def nfis_text_edit(self,new:str) -> None :
        self.na_text = new
    
# -------- | event | -------- #
    
    def nfis_active_edit(self,new:BoolFunc) -> None :
        self.na_active = new
    
    def nfis_event_edit(self,new:NoneFunc) -> None :
        self.na_event = new
    
    def nfis_active_event_edit(self,new:BoolFunc) -> None :
        self.na_active_event = new
    
    def nfis_effect_edit(self,new:NoneFunc) -> None :
        self.na_effect = new
    
    def nfis_active_effect_edit(self,new:BoolFunc) -> None :
        self.na_active_effect = new
        
# ========== | Fonctions Internes Menu (FIM) | ========== #

    def nfim_edit_menu(self) -> None :
        pass
    
    def nfim_main(self) -> "Noeud":
        # 
        return self

# -------- | Noeud adjacent | -------- #

    # def nfia_del_self(self,mod:Literal[])