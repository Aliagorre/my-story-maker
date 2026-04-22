from code.noeud import *
    
class Graphe:
    def __init__(self,nom:str) -> None:
        self.nom    =  nom #'ressource/dialogue_' + nom + '.txt'
        nom = "../ressource/"+ self.nom
        if not exists(nom):
            os.makedirs(nom)
        self.graphe = dict()
#        self.savoir = dict()
#        self.livre  = dict()
        self.charger_graphe()
        self.dernier_noeud  = self.charger_noeud_courant()
        self.noeud_courant  = self.charger_noeud_courant()

    def sauver_graphe(self):
        '''sauvegarde l'arbre dans un .txt sous le nom'''
        nom_noeud = '../ressource/' + self.nom + '/noeuds.txt'
        nom_liens = '../ressource/' + self.nom + '/liens.txt'
#        nom_saoir = '../ressource/' + self.nom + '/savoir.txt'
#        nom_livre = '../ressource/' + self.nom + '/livre.txt'
        noeud = open(nom_noeud, "w",encoding="utf8")
        liens = open(nom_liens, "w",encoding="utf8")
        dico_noeuds = {noeud.identifiant:noeud.liste() for noeud in self.graphe}
        dico_liens  = {noeud.identifiant:[lien.identifiant for lien in self.graphe[noeud]] for noeud in self.graphe}
        noeud.write(str(dico_noeuds))
        liens.write(str(dico_liens))
        noeud.close()
        liens.close()
        
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
        nom_noeud = '../ressource/' + self.nom + '/noeuds.txt'
        nom_liens = '../ressource/' + self.nom + '/liens.txt'
        nom_saoir = '../ressource/' + self.nom + '/savoir.txt'
        nom_livre = '../ressource/' + self.nom + '/livre.txt'
        try : # NOEUD
            liste_noeud = open(nom_noeud, "r",encoding="utf8")
            dico_noeuds = ast.literal_eval(liste_noeud.read())
        except :
            liste_noeud = open(nom_noeud, "w",encoding="utf8")
            liste_noeud.write(str({'Noyau':Noeud('Noyau','__Texte__','__Option__').liste()}))
            liste_noeud = open(nom_noeud, "r",encoding="utf8")
            dico_noeuds = ast.literal_eval(liste_noeud.read())
        liste_noeud.close()
        print('\ndico_noeuds extrait du txt : ', dico_noeuds)
        try : # LIENS
            liste_liens = open(nom_liens, "r",encoding="utf8")
            dico_liens  = ast.literal_eval(liste_liens.read())
        except :
            liste_liens = open(nom_liens, "w",encoding="utf8")
            liste_liens.write(str({'Noyau':[]}))
            liste_liens = open(nom_liens, "r",encoding="utf8")
            dico_liens  = ast.literal_eval(liste_liens.read())
        print('\ndico_liens extrait du txt : ', dico_liens)
        liste_liens.close()
        liste_noeuds_2 = {} # iden:Noeud(iden,noeuds[iden][0],noeuds[iden][1]) for iden in noeuds
        for identifiant in dico_noeuds:
            attribut = dico_noeuds[identifiant]
            noeud = Noeud(identifiant,*attribut)
            liste_noeuds_2[identifiant] = noeud
        print('\ndico identifiant : objet : ', liste_noeuds_2)
        for identifiant in liste_noeuds_2:
            cle = liste_noeuds_2[identifiant] # type noeud
            liste_identifient_lien = dico_liens[identifiant]
            liens = [liste_noeuds_2[iden] for iden in liste_identifient_lien]
            self.graphe[cle] = liens
        print('\ndico lien objet : lst[objet] : ', self.graphe)
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
        print('\n',self.noeud_courant.texte)
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
        noeud_courant.texte = reponce_option
        return self.menu_debogage(noeud_courant)
    
    def modifier_option(self,noeud_courant):
        nom_option     = input('nom option     : ')
        noeud_courant.option = nom_option
        return self.menu_debogage(noeud_courant)
    
    def modifier_choix(self,noeud_courant):
        
        return self.menu_debogage(noeud_courant)
    
    def créer_noeud(self,noeud_courant):
        dico_noeuds = {noeud.identifiant:noeud for noeud in self.graphe}
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
        
        condition      = input('condition      : ')
        while not est_solvable(condition):
            condition  = input('incorrecte     : ')
        nom_option     = input('nom option     : ')
        reponce_option = input('reponce option : ')
        if identifiant == 'stop' or condition == 'stop' or nom_option == 'stop' or reponce_option == 'stop':
            return self.menu_debogage(noeud_courant)
        noeud = Noeud(identifiant,reponce_option,nom_option,condition)
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
              