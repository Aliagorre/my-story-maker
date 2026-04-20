from code.graphe import *

class Jeu:
    def __init__(self):
        self.nom = 'catalogue.txt'
        try :
            catalogue = open(self.nom, "r",encoding="utf8")
            self.catalogue   = ast.literal_eval(catalogue.read())
        except :
            catalogue = open(self.nom, "w",encoding="utf8")
            catalogue.write('[]')
            catalogue = open(self.nom, "r",encoding="utf8")
            self.catalogue   = ast.literal_eval(catalogue.read())
    
    def ajoute_catalogue(self,nom:str):
        self.catalogue.append(nom)
        catalogue = open(self.nom, "w",encoding="utf8")
        catalogue.write(str(self.catalogue))
        catalogue.close()
        return Graphe(nom)
    
    def liste_catalogue(self):
        print('0 | Nouvelle histoire')
        for i,histoire in enumerate(self.catalogue):
            print(i+1,'|',histoire)
        choix = input('choix : ')
        while not choix in [str(i) for i in range(len(self.catalogue)+1)]:
            choix = input('choix : ')
        if choix == '0':
            nom = input("Nom de l'histoire : ")
            graphe = self.ajoute_catalogue(nom)
        else :
            graphe = Graphe(self.catalogue[int(choix)-1])
        boucle = graphe.parcourir()
        if boucle:
            graphe.sauver_graphe()
            return self.liste_catalogue()
        else :
            return False