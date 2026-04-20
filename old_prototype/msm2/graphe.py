from genericpath import exists
import ast
import os
import random

NON = ["non","no","nn","n","0","false"]
OUI = ["oui","ou","oi","ui","o","1","true"]

"""
class Joueur:
    def __init__(self):
        self.stat = dict()
        self.init()
    def init(self):
        d6 = [random.randint(1,20) for i in range(7)]
        d6.sort()
        d6.pop(0)
        for stat in ['force','dexterité','constitution','intelligence','sagesse','charisme']:
            print('--|',stat,'|--')
            for i in range(len(d6)):
                print('| valeur',i+1,':',d6[i])
            n = input('Choisir une valeur.\n >>> ')
            while not n in [str(j) for j in d6]:
                n = input('Choisir une valeur.\n >>> ')
            i = 0
            while not d6[i] == int(n):
                i += 1
            self.stat[stat] = d6.pop(i)
        
#Joueur()
"""


    



    
class Noeud:
    def __init__(self,iden:str,texte:str,option:str,condition='True',effet='None'):
        self.identifiant = iden
        self.texte       = texte.replace('\\n','\n')  #reponce à l'option
        self.option      = option.replace('\\n','\n') #nom de l'option
        self.condition   = condition
        self.effet       = effet

    def liste(self):
        self.texte = self.texte.replace('\\n','\n')
        return self.__dict__
        
    def choix(self):
        pass
    
    def est_disponible(self):
        return eval(self.condition)

class Graphe:
    def __init__(self,nom:str) -> None:
        self.nom    =  nom #'ressource/dialogue_' + nom + '.txt'
        nom = "ressource/"+ self.nom
        if not exists(nom):
            os.makedirs(nom)
        self.graphe = dict()
        self.savoir = dict()
#        self.livre  = dict()
        self.charger_graphe()
        self.dernier_noeud  = self.charger_noeud_courant()
        self.noeud_courant  = self.charger_noeud_courant()

    def sauver_graphe(self):
        '''sauvegarde l'arbre dans un .txt sous le nom'''
        nom_noeud = 'ressource/' + self.nom + '/noeuds.txt'
        nom_liens = 'ressource/' + self.nom + '/liens.txt'
        nom_savoir = 'ressource/' + self.nom + '/savoir.txt'
#        nom_livre = 'ressource/' + self.nom + '/livre.txt'
        noeud = open(nom_noeud, "w",encoding="utf8")
        liens = open(nom_liens, "w",encoding="utf8")
        savoir = open(nom_savoir, "w",encoding="utf8")
        dico_noeuds = {noeud.identifiant:noeud.liste() for noeud in self.graphe}
        dico_liens  = {noeud.identifiant:[lien.identifiant for lien in self.graphe[noeud]] for noeud in self.graphe}
        dico_savoir = {know:0 for know in self.savoir}
        noeud.write(str(dico_noeuds))
        liens.write(str(dico_liens))
        savoir.write(str(dico_savoir))
        noeud.close()
        liens.close()
        savoir.close()
        
    def lire_savoir(self,nom,valeur,operation):
        if not nom in self.savoir:
            self.savoir[nom] = 0
        if operation == '=':
            return self.savoir[nom] == valeur
        if operation == '>':
            return self.savoir[nom] > valeur
        if operation == '<':
            return self.savoir[nom] < valeur
        else :
            return False
        
    def est_solvable(self,appelation):
        try :
            if type(eval(appelation)) == bool:
                return True
            else :
                return False
        except :
            return False
        
    def modif_savoir(self,nom,valeur,operation):
        if not nom in self.savoir:
            self.savoir[nom] = 0
        if operation == '=':
            self.savoir[nom] = valeur
        if operation == '+':
            self.savoir[nom] += valeur
        if operation == '-':
            self.savoir[nom] -= valeur
        if operation == '*':
            self.savoir[nom] *= valeur
        return None
        
    def noeuds(self):
        liste_noeud = {}
        for noeud in self.graphe:
            liste_noeud[noeud.identifiant] = noeud.liste()
    def liens(self):
        liste_lien = {}
        for noeud in self.graphe:
            liste_lien[noeud.identifiant] = [n.identifiant for n in self.graphe]
        return liste_lien

    def charger_graphe(self):
        '''renvoie un graphe des dialogues possible'''
        nom_noeud = 'ressource/' + self.nom + '/noeuds.txt'
        nom_liens = 'ressource/' + self.nom + '/liens.txt'
        nom_savoir = 'ressource/' + self.nom + '/savoir.txt'
        nom_livre = 'ressource/' + self.nom + '/livre.txt'
        try : # SAVOIR
            liste_savoir = open(nom_savoir, "r",encoding="utf8")
            self.savoir  = ast.literal_eval(liste_savoir.read())
        except :
            liste_savoir = open(nom_savoir, "w",encoding="utf8")
            liste_savoir.write(str({}))
            liste_savoir = open(nom_savoir, "r",encoding="utf8")
            self.savoir  = ast.literal_eval(liste_savoir.read())
        liste_savoir.close()
        try : # NOEUD
            liste_noeud = open(nom_noeud, "r",encoding="utf8")
            dico_noeuds = ast.literal_eval(liste_noeud.read())
        except :
            liste_noeud = open(nom_noeud, "w",encoding="utf8")
            liste_noeud.write(str({'Noyau':Noeud('Noyau','__Texte__','__Option__').liste()}))
            liste_noeud = open(nom_noeud, "r",encoding="utf8")
            dico_noeuds = ast.literal_eval(liste_noeud.read())
        liste_noeud.close()
        #print('dico_noeuds extrait du txt : ', dico_noeuds)
        try : # LIENS
            liste_liens = open(nom_liens, "r",encoding="utf8")
            dico_liens  = ast.literal_eval(liste_liens.read())
        except :
            liste_liens = open(nom_liens, "w",encoding="utf8")
            liste_liens.write(str({'Noyau':[]}))
            liste_liens = open(nom_liens, "r",encoding="utf8")
            dico_liens  = ast.literal_eval(liste_liens.read())
        #print('dico_liens extrait du txt : ', dico_liens)
        liste_liens.close()
        liste_noeuds_2 = {} # iden:Noeud(iden,noeuds[iden][0],noeuds[iden][1]) for iden in noeuds
        for identifiant in dico_noeuds:
            noeud = Noeud('Noyau','__Texte__','__Option__')
            noeud.__dict__.update(dico_noeuds[identifiant])
            liste_noeuds_2[identifiant] = noeud
        #print('dico identifiant : objet : ', liste_noeuds_2)
        for identifiant in liste_noeuds_2:
            cle = liste_noeuds_2[identifiant] # type noeud
            liste_identifient_lien = dico_liens[identifiant]
            liens = [liste_noeuds_2[iden] for iden in liste_identifient_lien]
            self.graphe[cle] = liens
        #print('dico lien objet : lst[objet] : ', self.graphe)
        #self.graphe = {liste_noeuds_2[iden]:[liste_noeuds_2[iden2] for iden2 in liens[iden]] for iden in liens}
        
    def charger_noeud_courant(self):
        for noeud in self.graphe:
            if noeud.identifiant == 'Noyau':
                return noeud
        assert False, 'Aucun Noyau trouvé'
        
    def menu_debogage(self,noeud_courant,debug_max=False):
        self.sauver_graphe()
        print('\n----- | Menu édition noeud',noeud_courant.identifiant,'| -----\n')
        if self.noeud_courant != self.dernier_noeud:
            print('Dernière choix fait     :',self.noeud_courant.option,'|',self.noeud_courant.identifiant)
        else :
            print('Dernière choix fait     :','-- Aucun choix précédent trouvé --')
        print('Noeud en cours de modif :',noeud_courant.option,'|',noeud_courant.identifiant)
        print('Conditions préalables   :',noeud_courant.condition)
        print('Nombre de choix possible:',len([noeud for noeud in self.graphe[noeud_courant] if eval(noeud.condition)]))
        print('Nombre de choix bloquée :',len([noeud for noeud in self.graphe[noeud_courant] if not eval(noeud.condition)]))
        print('Nombre de choix total   :',len(self.graphe[noeud_courant]))
        print()
        if debug_max :
            print('||||| | Info debug avancée | |||||')
            print('Texte :\n',noeud_courant.texte)
            print('\n---| Choix existant |---\n')
            for i,lien in enumerate(self.graphe[noeud_courant]):
                print(i+1,'|',lien.option,' >>> ',lien.identifiant)
                print(' ','|',lien.condition,'  >>>  ',eval(lien.condition))
            if len(self.graphe[noeud_courant]) == 0:
                print('-- Aucun choix disponible --')
            print()
        possible = [str(i) for i in range(1,9)]
        print("1 | Retour à l'histoire")
        print('2 | La réponce au choix actif doit être changé')
        print("3 | Le nom du d'option choix actif doit être modifié")
        print('4 | Aucun choix ne me satisfait parmis les nouveaux proposés')
        print('5 | Un choix proposé est incorrecte')
        print('6 | Quitter vers le menu de selection de histoire')
        print('7 | "Sauvegarder" et quitter le programme')
        if not debug_max:
            print("8 | Voir plus d'informations sur le noeud")
            possible.append('8')
        if self.noeud_courant != self.dernier_noeud:
            print("9 | J'aurais originelement du avoir un autre choix possible")
            print('10| Revenir au noeud précédent')
            possible.append('9')
            possible.append('10')
        choix = input('\n>>> ')
        while not choix in possible:
            choix = input('>>> ')
            
        if choix == '1':
            return self.parcourir()
        if choix == '2':
            return self.modifier_réponce(noeud_courant)
        if choix == '3':
            return self.modifier_option(noeud_courant)
        if choix == '4':
            return self.créer_noeud(noeud_courant)
        if choix == '5':
            return self.modifier_choix(noeud_courant)
        # modifier condition
        if choix == '6':
            return True
        if choix == '7':
            return False # Faire la sauvegarde
        
        if choix == '8':
            return self.menu_debogage(noeud_courant,True)
        if choix == '9':
            return self.créer_noeud(self.dernier_noeud)
        if choix == '10':
            self.noeud_courant = self.dernier_noeud
            return self.parcourir()
        return False
        
    def parcourir(self):
        assert self.noeud_courant in self.graphe
        eval(self.noeud_courant.effet)
        print('\n',self.noeud_courant.texte)
        print()
        liste_possible = [noeud for noeud in self.graphe[self.noeud_courant] if eval(noeud.condition)]
        for i,noeud in enumerate(liste_possible):
            print(i+1,'|',noeud.option)
        if len(liste_possible) == 0:
            print('0 | Menu créatif (visible si aucune option possible)')
        choix = input('>>> ')
        while not choix in [str(i) for i in range(len(liste_possible)+1)]:
            choix = input('>>> ')
        if choix == '0':
            return self.menu_debogage(self.noeud_courant)
        else :
            self.dernier_noeud = self.noeud_courant
            self.noeud_courant = liste_possible[int(choix)-1]
            return self.parcourir()
    
    def ajouter_lien(self,noeud_courant,noeud_cible):
        assert noeud_courant in self.graphe and noeud_cible in self.graphe
        self.graphe[noeud_courant].append(noeud_cible)
        print('\n---- Lien de',noeud_courant,'vers',noeud_cible,' créé ----\n')
        return self.menu_debogage(noeud_courant,True)
    
    def modifier_réponce(self,noeud_courant):
        reponce_option = input('reponce option : ')
        noeud_courant.texte = reponce_option.replace('\\n','\n')
        return self.menu_debogage(noeud_courant)
    
    def modifier_option(self,noeud_courant):
        nom_option     = input('nom option     : ')
        noeud_courant.option = nom_option.replace('\\n','\n')
        return self.menu_debogage(noeud_courant)
    
    def modifier_choix(self,noeud_courant):
        
        return self.menu_debogage(noeud_courant)
    
    def créer_noeud(self,noeud_courant):
        dico_noeuds = {noeud.identifiant:noeud for noeud in self.graphe}
        for i in self.graphe:
            print('|',i.identifiant,end = ' ')
        print('|')
        identifiant    = input('identifiant    : ').lower()
        if identifiant in dico_noeuds:
            print(identifiant,'existe déjà !\n')
            choix = input('1 | créer un lien\n2 | utiliser un autre identifiant')
            while not choix in ['1','2']:
                choix = input('1 | créer un lien\n2 | utiliser un autre identifiant\n>>> ')
            if choix == '2':
                return self.créer_noeud(noeud_courant)
            else :
                return self.ajouter_lien(noeud_courant,dico_noeuds[identifiant])
        
        for i in self.savoir:
            print(i,':',self.savoir[i])
        condition      = input('condition      : ')
        while not self.est_solvable(condition):
            condition  = input('incorrecte     : ')
        nom_option     = input('nom option     : ')
        reponce_option = input('reponce option : ')
        effet          = input('effet(self.modif_savoir()):')
        if identifiant == 'stop' or condition == 'stop' or nom_option == 'stop' or reponce_option == 'stop':
            return self.menu_debogage(noeud_courant)
        noeud = Noeud(identifiant,reponce_option,nom_option,condition,effet)
        self.graphe[noeud] = []
        self.graphe[noeud_courant].append(noeud)
        
        print('\n---- Noeud',identifiant,'créé dans',noeud_courant.identifiant,'----\n')
        
        sous_noeud = input('Créer un sous-noeud ?\n >>> ')
        while not (sous_noeud in OUI) and not(sous_noeud in NON):
            sous_noeud = input('Créer un sous-noeud ?\n >>> ')
        if sous_noeud in OUI:
            return self.créer_noeud(noeud)
        else :
            return self.menu_debogage(noeud_courant,True)
              
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
            
             
test = Jeu()
test.liste_catalogue()
