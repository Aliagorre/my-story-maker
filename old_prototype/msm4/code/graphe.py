from noeud import *

class Graphe:
    def __init__(self,key:str="None",label:str="None",racine:Noeud=Noeud()) -> None :
        self.ga_key:str      = key     # identifiant de la sauvegarde - plusieur sauvegarde par scénario
        self.ga_label:str    = label   # identifiant du scénario ?
        self.ga_racine:Noeud = racine  # On charge la racine à partir de laquel est construit le graphe
        self.ga_graphe:dict[str,Noeud] = {racine.nfo_key() : racine} # On charge un dico des identifiant des noeuds et le noeud
        self.ga_noeud_courant:Noeud=racine
        
# ========== | Fonctions Observatrices (FO) | ========== #

    def gfo_key(self) -> str :
        return self.ga_key
    
    def gfo_label(self) -> str :
        return self.ga_label
    
    def gfo_racine(self) -> Noeud :
        return self.ga_racine
    
    def gfo_graphe(self) -> dict[str,Noeud] :
        return self.ga_graphe
    
    def gfo_graphe_keys(self) -> list[str] :
        return list(self.ga_graphe.keys())
    
    def gfo_graphe_values(self) -> list[Noeud] :
        return list(self.ga_graphe.values())
    
    def gfo_graphe_value(self,key:str) -> Noeud :
        return self.ga_graphe[key]
    
    def gfo_noeud_courant(self) -> Noeud :
        return self.ga_noeud_courant
    
     
# ========== | Fonctions Internes Simple (FIS) | ========== #

    def gfi_load(self,path:str):
        default_racine = {"key":self.ga_key,"label":self.ga_label,
                          "racine":self.ga_racine.nfo_key(),
                          "graphe":self.gfo_graphe_keys()}
        data:dict =  open_file(f"{path}/{self.ga_key}/graphe.txt",default_value)
        self.ga_key = data["key"]
        self.ga_label = data["label"]
        self.ga_racine = Noeud(data["racine"])
        self.ga_racine.nfi_load()
        self.ga_graphe = {}

# -------- Reset -------- #


# -------- Edit -------- #

    def gfis_key_edit(self,new:str) -> None :
        self.ga_key = new
        
    def gfis_label_edit(self,new:str) -> None :
        self.ga_label = new
        
    def gfis_racine_edit(self,new:Noeud) -> None :
        '''
Ne vérifie pas si la nouvelle racine existe dans le graphe
'''
        self.ga_racine = new
        
    def gfis_noeud_courant_edit(self,new:Noeud) -> None :
        '''
Ne vérifie pas si le nouveau noeud courant existe dans le graphe
'''
        self.ga_noeud_courant = new
        
    def gfis_noeud_courant_racine(self) -> None :
        '''
Met la racine en noeud dourant
'''
        self.ga_noeud_courant = self.ga_racine
        
# ========== | Fonctions Internes Avancées (FIA) | ========== #

# ========== | Fonctions Internes Menu (FIM) | ========== #
    
    def 

    