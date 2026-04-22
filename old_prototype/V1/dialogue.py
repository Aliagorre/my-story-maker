import ast

class Noeud:
    def __init__(self,texte:str,reponce:str,liste_fils=None,effet='None') -> None:
        self.texte      = texte
        self.reponce    = reponce
        self.liste_fils = liste_fils if liste_fils is not None else []
        self.effet      = effet
        self.attent     = 0

    def liste(self):
        return (self.texte,self.reponce,[fils.liste() for fils in self.liste_fils],self.effet)
        
    def choix(self):
        eval(self.effet)
        if len(self.liste_fils) == 0:
            texte = input('texte choix : ')
            texte = texte.replace("\\n", "\n")
            reponce = input('texte reponse : ')
            reponce = reponce.replace("\\n", "\n")
            self.liste_fils.append(Noeud(texte,reponce,[],'None'))
        for i,j in enumerate(self.liste_fils):
            print(i+1,'|',j.texte)
        choix_possible = [str(i+1) for i in range(len(self.liste_fils))] 
        choix = input('choix : ')
        while not choix in choix_possible :
            if   choix == 'txt':
                new = input('replique : ')
                new = new.replace("\\n", "\n")
                self.texte = new
                print("-----------------------------------")
                print(self.texte)
                for i,j in enumerate(self.liste_fils):
                    print(i+1,'|',j.texte)
            elif choix == 'rep':
                new = input('replique : ')
                new = new.replace("\\n", "\n")
                self.reponce = new
                print("\n-----------------------------------")
                print(self.texte)
                print("-----------------------------------")
                print(self.reponce)
                for i,j in enumerate(self.liste_fils):
                    print(i+1,'|',j.texte)
            elif choix == 'sup':
                choix_2 = input('supprime choix : ')
                while not choix_2 in [str(i+1) for i in range(len(self.liste_fils))]:
                    choix_2 = input('supprime choix : ')
                self.liste_fils.pop(int(choix_2)-1)
                if len(self.liste_fils) == 0:
                    texte = input('texte choix : ')
                    texte = texte.replace("\\n", "\n")
                    reponce = input('texte reponse : ')
                    reponce = reponce.replace("\\n", "\n")
                    self.liste_fils.append(Noeud(texte,reponce,[],'None'))
                choix_possible = [str(i+1) for i in range(len(self.liste_fils))]
                print("\n-----------------------------------")
                print(self.texte)
                print("-----------------------------------")
                print(self.reponce)
                for i,j in enumerate(self.liste_fils):
                    print(i+1,'|',j.texte)
            elif choix == 'act':
                continue
            elif choix == 'new':
                texte = input('texte choix : ')
                texte = texte.replace("\\n", "\n")
                reponce = input('texte reponse : ')
                reponce = reponce.replace("\\n", "\n")
                self.liste_fils.append(Noeud(texte,reponce,[],'None'))
                choix_possible = [str(i+1) for i in range(len(self.liste_fils))]
                print("-----------------------------------")
                print(self.reponce)
                print("\n-----------------------------------")
                print(self.texte)
                for i,j in enumerate(self.liste_fils):
                    print(i+1,'|',j.texte)
            self.attent += 1
            if self.attent > 5:
                print('txt,rep,sup,act,new')
            choix = input('choix : ')
        print(self.liste_fils[int(choix)-1].texte)
        print("-----------------------------------")
        print(self.liste_fils[int(choix)-1].reponce,'\n')
        return self.liste_fils[int(choix)-1]

class Arbre:
    def __init__(self,nom:str,profondeur=10) -> None:
        self.nom    = 'ressource/dialogue_' + nom + '.txt'
        self.profondeur = profondeur
        self.charger_arbre()

    def sauver_arbre(self):
        '''sauvegarde l'arbre dans un .txt sous le nom'''
        dialogue = open(self.nom, "w",encoding="utf8")
        dialogue.write(str(self.racine.liste()))
        dialogue.close()

    def charger_arbre(self):
        '''renvoie un arbre des dialogues possible'''
        try :
            dialogue = open(self.nom, "r",encoding="utf8")
            racine   = ast.literal_eval(dialogue.read())
        except :
            dialogue = open(self.nom, "w",encoding="utf8")
            dialogue.write(str(Noeud("","",[]).liste()))
            dialogue = open(self.nom, "r",encoding="utf8")
            racine   = ast.literal_eval(dialogue.read())
        dialogue.close()
        self.racine = creer_arbre(racine)
        self.actuel = self.racine
        
    def lancer(self):
        if self.racine.reponce == '':
            self.racine.reponce = input('Phrase de départ : ')
            self.racine.reponce = self.racine.reponce.replace("\\n", "\n")
        print(self.racine.reponce)
        self.actuel = self.actuel.choix()
        for i in range(self.profondeur-1):
            self.actuel = self.actuel.choix()
            self.sauver_arbre()
            
class Jeu:
    def __init__(self):
        self.nom = 'catalogue.txt'
        try :
            catalogue = open(self.nom, "r",encoding="utf8")
            self.catalogue   = ast.literal_eval(catalogue.read())
        except :
            catalogue = open(self.nom, "w",encoding="utf8")
            catalogue.write(str([]))
            catalogue = open(self.nom, "r",encoding="utf8")
            self.catalogue   = ast.literal_eval(catalogue.read())
    
    def ajoute_catalogue(self,nom:str):
        self.catalogue.append(nom)
        catalogue = open(self.nom, "w",encoding="utf8")
        catalogue.write(str(self.catalogue))
        catalogue.close()
        return Arbre(nom)
    
    def liste_catalogue(self):
        print('0 | Nouvelle histoire')
        for i,histoire in enumerate(self.catalogue):
            print(i+1,'|',histoire)
        choix = input('choix : ')
        while not choix in [str(i) for i in range(len(self.catalogue)+1)]:
            choix = input('choix : ')
        if choix == '0':
            nom = input("Nom de l'histoire : ")
            self.ajoute_catalogue(nom).lancer()
        else :
            Arbre(self.catalogue[int(choix)-1]).lancer()
            
def creer_arbre(racine:tuple):
    return Noeud(racine[0],racine[1],[creer_arbre(fils) for fils in racine[2]],racine[3])
    
test = Jeu()
test.liste_catalogue()
