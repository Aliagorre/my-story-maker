class Mod:
    def on_load(self, core):
        # Le core peut enregistrer des services ici si nécessaire
        pass

    def on_init(self, core):
        # Le core peut initialiser des structures internes
        pass

    def on_ready(self, event):
        # Le core est prêt, rien à faire
        pass

    def on_shutdown(self, core):
        # Nettoyage éventuel
        pass
