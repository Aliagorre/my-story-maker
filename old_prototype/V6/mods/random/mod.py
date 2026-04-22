# mods/random/mod.py
import random
from core.errors import EngineError, ModError

def register(ctx):

    # ----------------------------------------------------------------
    # Opérateurs de condition aléatoires
    # ----------------------------------------------------------------

    def op_chance(args):
        """
        { "chance": 0.3 }  → True 30% du temps
        """
        if not isinstance(args, (int, float)) or not (0.0 <= args <= 1.0):
            raise ModError(f"'chance' expects a float between 0 and 1, got: {args!r}")
        return random.random() < args

    def op_roll(args):
        """
        { "roll": [2, 6] }  → lance 2d6, retourne la somme (int, pas bool)
        Utile dans un 'gt' : { "gt": [{ "roll": [1, 20] }, 15] }
        """
        if not isinstance(args, list) or len(args) != 2:
            raise ModError(f"'roll' expects [nb_dice, faces], got: {args!r}")
        nb, faces = args
        if not isinstance(nb, int) or not isinstance(faces, int) or nb < 1 or faces < 1:
            raise ModError(f"'roll' expects positive integers, got: {args!r}")
        return sum(random.randint(1, faces) for _ in range(nb))

    def op_one_of(args):
        """
        { "one_of": ["forest", "cave", "village"] }  → retourne un élément au hasard
        Utile pour des destinations ou textes aléatoires.
        """
        if not isinstance(args, list) or not args:
            raise ModError(f"'one_of' expects a non-empty list, got: {args!r}")
        return random.choice(args)

    ctx.condition_engine.register("chance",  op_chance)
    ctx.condition_engine.register("roll",    op_roll)
    ctx.condition_engine.register("one_of",  op_one_of)

    # ----------------------------------------------------------------
    # Actions aléatoires
    # ----------------------------------------------------------------

    def action_random_set(ctx, args):
        """
        { "random_set": ["variable", 1, 10] }  → assigne un entier aléatoire entre 1 et 10
        """
        if not isinstance(args, list) or len(args) != 3:
            raise ModError(f"'random_set' expects [variable, min, max], got: {args!r}")
        key, low, high = args
        if not isinstance(low, int) or not isinstance(high, int) or low > high:
            raise ModError(f"'random_set' expects integers with min <= max, got: {args!r}")
        ctx.state[key] = random.randint(low, high)

    def action_random_goto(ctx, args):
        """
        { "random_goto": ["forest", "cave", "village"] }  → navigue vers un nœud aléatoire
        """
        if not isinstance(args, list) or not args:
            raise ModError(f"'random_goto' expects a non-empty list of node ids, got: {args!r}")
        target = random.choice(args)
        engine = ctx.mod_states.get("engine")
        if engine is None:
            raise ModError("'random_goto' requires an active engine")
        engine.enter_node(target)

    ctx.mod_states["actions"]["random_set"]  = action_random_set
    ctx.mod_states["actions"]["random_goto"] = action_random_goto