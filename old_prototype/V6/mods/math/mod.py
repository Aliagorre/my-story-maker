# mods/math_conditions/mod.py
#
# Ajoute des opérateurs au ConditionEngine pour écrire des conditions
# et des expressions arithmétiques dans les fichiers JSON de graphe.
#
# ── SYNTAXE GÉNÉRALE ────────────────────────────────────────────────
#
#   Chaque opérateur est un dict à une seule clé :
#   { "nom_op": <args> }
#
#   Les arguments peuvent être :
#     - une valeur littérale  : 10, "texte", true, null
#     - un nom de variable    : "player_gold"  (résolu depuis ctx.state)
#     - une expression imbriquée : { "add": ["player_gold", 5] }
#
# ── OPÉRATEURS DISPONIBLES ──────────────────────────────────────────
#
#   COMPARAISON (→ bool)
#   { "eq":  [a, b] }          a == b
#   { "neq": [a, b] }          a != b
#   { "gt":  [a, b] }          a >  b
#   { "gte": [a, b] }          a >= b
#   { "lt":  [a, b] }          a <  b
#   { "lte": [a, b] }          a <= b
#   { "between": [x, min, max] }   min <= x <= max
#
#   LOGIQUE (→ bool)
#   { "and": [expr, expr, ...] }   tous vrais
#   { "or":  [expr, expr, ...] }   au moins un vrai
#   { "not": expr }                négation
#
#   ARITHMÉTIQUE (→ nombre)      utilisable dans eval_or_resolve,
#                                 ou comme argument d'une comparaison
#   { "add": [a, b] }          a + b
#   { "sub": [a, b] }          a - b
#   { "mul": [a, b] }          a * b
#   { "div": [a, b] }          a / b  (lève si b == 0)
#   { "mod": [a, b] }          a % b
#   { "abs": x }               |x|
#   { "clamp": [x, min, max] } min <= x <= max, retourne x borné
#
# ── EXEMPLES JSON ───────────────────────────────────────────────────
#
#   Condition simple :
#   "conditions": { "gte": ["player_gold", 10] }
#
#   Condition composée :
#   "conditions": { "and": [
#       { "gte": ["player_hp", 1] },
#       { "neq": ["quest_state", "done"] }
#   ]}
#
#   Arithmétique dans une comparaison :
#   "conditions": { "gt": [ { "add": ["base_atk", "bonus_atk"] }, 20 ] }
#
#   Action set avec calcul :
#   { "set": ["player_gold", { "sub": ["player_gold", 5] }] }


def register(ctx):
    ce = ctx.condition_engine   # raccourci

    # ----------------------------------------------------------------
    # Résolution récursive d'une valeur ou expression
    # ----------------------------------------------------------------

    def _res(val):
        """Résout val : variable, littéral ou expression { op: args }."""
        return ce.eval_or_resolve(val)

    # ----------------------------------------------------------------
    # Opérateurs de comparaison
    # ----------------------------------------------------------------

    def op_eq(args):
        a, b = _res(args[0]), _res(args[1])
        return a == b

    def op_neq(args):
        a, b = _res(args[0]), _res(args[1])
        return a != b

    def op_gt(args):
        a, b = _res(args[0]), _res(args[1])
        return a > b

    def op_gte(args):
        a, b = _res(args[0]), _res(args[1])
        return a >= b

    def op_lt(args):
        a, b = _res(args[0]), _res(args[1])
        return a < b

    def op_lte(args):
        a, b = _res(args[0]), _res(args[1])
        return a <= b

    def op_between(args):
        # { "between": [x, min, max] }
        x, lo, hi = _res(args[0]), _res(args[1]), _res(args[2])
        return lo <= x <= hi

    # ----------------------------------------------------------------
    # Opérateurs logiques
    # ----------------------------------------------------------------

    def op_and(args):
        # court-circuit : s'arrête au premier False
        return all(ce.evaluate(expr) for expr in args)

    def op_or(args):
        # court-circuit : s'arrête au premier True
        return any(ce.evaluate(expr) for expr in args)

    def op_not(arg):
        return not ce.evaluate(arg)

    # ----------------------------------------------------------------
    # Opérateurs arithmétiques
    # ----------------------------------------------------------------

    def op_add(args):
        return _res(args[0]) + _res(args[1])

    def op_sub(args):
        return _res(args[0]) - _res(args[1])

    def op_mul(args):
        return _res(args[0]) * _res(args[1])

    def op_div(args):
        a, b = _res(args[0]), _res(args[1])
        if b == 0:
            ctx.events.emit_error("math_conditions: division par zéro")
        return a / b

    def op_mod(args):
        a, b = _res(args[0]), _res(args[1])
        if b == 0:
            ctx.events.emit_error("math_conditions: modulo par zéro")
        return a % b

    def op_abs(arg):
        return abs(_res(arg))

    def op_clamp(args):
        x, lo, hi = _res(args[0]), _res(args[1]), _res(args[2])
        return max(lo, min(hi, x))

    # ----------------------------------------------------------------
    # Enregistrement
    # ----------------------------------------------------------------

    operators = {
        # comparaison
        "eq":      op_eq,
        "neq":     op_neq,
        "gt":      op_gt,
        "gte":     op_gte,
        "lt":      op_lt,
        "lte":     op_lte,
        "between": op_between,
        # logique
        "and":     op_and,
        "or":      op_or,
        "not":     op_not,
        # arithmétique
        "add":     op_add,
        "sub":     op_sub,
        "mul":     op_mul,
        "div":     op_div,
        "mod":     op_mod,
        "abs":     op_abs,
        "clamp":   op_clamp,
    }

    for name, fn in operators.items():
        ce.register(name, fn)