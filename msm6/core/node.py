from core.utils import *

class Node:
    def __init__(self) -> None:
        self.key    :str = "default"   # identifiant unique de l'objet
        self.label  :str = "default"   # nom afficher dans les choix
        self.text   :str = "default"   # texte affiché en conséquence du choix
        self.active      :BoolFunc = true  # condition à évaluer comme vrai pour rendre le noeuds accessible
        self.event       :NoneFunc = none  # l'event se déclenche après text
        self.active_event:BoolFunc = true  # condition suplémentaire pour activer l'event du noeuds.
        self.data :dict[str,Any] = {} # dictionnaire de donnée propre au noeud, utilisé pour les conditions ou autres.

    def init_node(self,data:dict[str,Any]) -> None :
        self.key  = data["key"]   
        self.label= data["label"] 
        self.text = data["text"]  
        self.active      = data["active"]
        self.event       = data["event"]
        self.active_event= data["active_event"]  
        self.data = data["data"]

    def node_dict(self) -> dict[str,str|dict|Callable] :
        return {
            "key"   :self.key   ,
            "label" :self.label ,
            "text"  :self.text  ,
            "active":self.active,
            "event" :self.event ,
            "active_event":self.active_event,
            "data"  :self.data  
            }
    
    def __eq__(self, value: "Node") -> bool :
        return self.key == value.key
    