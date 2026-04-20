# mods/player/mod.py

def register(ctx):
    """
    Mod 'player' :
    - Initialise les stats du joueur au démarrage de la partie
    - Fournit une API pour manipuler les stats
    - (optionnel) expose une petite commande interne pour debug
    """

    # ---------- LOGIQUE MÉTIER ----------

    def init_player(ctx):
        ctx.state["player"] = {
            "name": "Héros",
            "strength": 5,
            "dexterity": 5,
            "intelligence": 5,
            "hp": 20,
            "max_hp": 20,
            "gold": 0,
            "level": 1,
            "xp": 0,
        }

    def get_player():
        return ctx.state.get("player")

    def add_stat(stat, value):
        player = get_player()
        if not player:
            return
        player[stat] = player.get(stat, 0) + value

    def set_stat(stat, value):
        player = get_player()
        if not player:
            return
        player[stat] = value

    def heal(amount):
        player = get_player()
        if not player:
            return
        player["hp"] = min(player["hp"] + amount, player["max_hp"])

    def damage(amount):
        player = get_player()
        if not player:
            return
        player["hp"] = max(player["hp"] - amount, 0)

    # ---------- API EXPOSEE AUX AUTRES MODS ----------

    ctx.mod_states["player_api"] = {
        "get_player": get_player,
        "add_stat": add_stat,
        "set_stat": set_stat,
        "heal": heal,
        "damage": damage,
    }

    # ---------- EVENEMENTS ----------

    # Initialisation du joueur au démarrage de la partie
    ctx.events.on("on_game_start", init_player)

    # ---------- (OPTIONNEL) AFFICHAGE POUR DEBUG ----------

    #def on_game_start_log(ctx):
    #    print("[player] Joueur initialisé :", ctx.state.get("player"))

    #ctx.events.on("on_game_start", on_game_start_log)
