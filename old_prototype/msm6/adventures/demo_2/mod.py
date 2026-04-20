# adventures/demo_2/mod.py

def register(ctx):
    from core import load_graph_from_file, Engine
    graph  = load_graph_from_file("adventures/demo_2/graph.json")
    engine = Engine(graph, ctx, ctx.events)
    ctx.mod_states["engine"] = engine
