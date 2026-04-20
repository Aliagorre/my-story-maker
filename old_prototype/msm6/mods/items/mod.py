# mods/items/mod.py
# mods/items/mod.py

def register(ctx):
    # Stockage interne : types d'items
    ctx.mod_states["items"] = {
        "types": {},   # type_id -> dict
    }

    # API
    def register_type(type_id, data):
        """Déclare un nouveau type d'item."""
        types = ctx.mod_states["items"]["types"]
        if type_id in types:
            ctx.events.emit_warning(f"Item type '{type_id}' already registered")
            return
        types[type_id] = data

    def get_type(type_id):
        return ctx.mod_states["items"]["types"].get(type_id)

    def list_types():
        return list(ctx.mod_states["items"]["types"].keys())

    def create_item(type_id):
        """Crée une instance d'item simple."""
        t = get_type(type_id)
        if t is None:
            ctx.events.emit_error(f"Unknown item type '{type_id}'")
            return None

        # Instance minimale
        return {
            "type": type_id,
            "name": t.get("name", type_id),
            "props": t.get("props", {}).copy(),
        }

    # Exposer l'API
    ctx.mod_states["items_api"] = {
        "register_type": register_type,
        "get_type": get_type,
        "list_types": list_types,
        "create_item": create_item,
    }


