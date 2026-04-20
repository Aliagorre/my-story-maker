from code.util import *

class Noeud:
    def __init__(self,iden:str,texte:str,option:str,condition='True'):
        self.identifiant = iden
        self.texte       = texte.replace('\\n','\n')  #reponce à l'option
        self.option      = option.replace('\\n','\n') #nom de l'option
        self.condition   = condition

    def liste(self):
        return [self.texte,self.option,self.condition]
        
    def choix(self):
        pass
    
    def est_disponible(self):
        return eval(self.condition)