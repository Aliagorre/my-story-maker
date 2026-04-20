# mods/inventory/mod.py

def register(ctx):
    items_api = ctx.mod_states.get("items_api")
    if items_api is None:
        ctx.events.emit_error("mod_inventory requires mod_items")
        return

    # Inventaire stocké dans ctx.state["inventory"]
    ctx.state.setdefault("inventory", [])

    # API
    def add_item(type_id):
        item = items_api["create_item"](type_id)
        if item is None:
            return
        ctx.state["inventory"].append(item)
        ctx.events.emit("on_item_added", ctx, item)

    def remove_item(type_id):
        inv = ctx.state["inventory"]
        for i, item in enumerate(inv):
            if item["type"] == type_id:
                removed = inv.pop(i)
                ctx.events.emit("on_item_removed", ctx, removed)
                return
        ctx.events.emit_warning(f"Item '{type_id}' not found in inventory")

    def list_inventory():
        return ctx.state["inventory"]

    def has_item(type_id):
        return any(item["type"] == type_id for item in ctx.state["inventory"])

    # Actions
    ctx.mod_states["actions"]["add_item"] = lambda ctx2, args: add_item(args[0])
    ctx.mod_states["actions"]["remove_item"] = lambda ctx2, args: remove_item(args[0])

    # API publique
    ctx.mod_states["inventory_api"] = {
        "add_item": add_item,
        "remove_item": remove_item,
        "list_inventory": list_inventory,
        "has_item": has_item,
    }

    # Events
    ctx.events.register_event("on_item_added")
    ctx.events.register_event("on_item_removed")
