# mods/conditions/mod.py
from core.errors import ModError

def register(ctx):
    ce = ctx.condition_engine

    def op_var(name) -> bool:
        value = ce.get_variable(name)
        if value is None:
            raise ModError(f"Unknown variable '{name}'")
        return bool(value)

    def op_not(expr) -> bool:
        return not ce.eval_or_resolve(expr)

    def op_and(exprs) -> bool:
        return all(ce.eval_or_resolve(e) for e in exprs)

    def op_or(exprs) -> bool:
        return any(ce.eval_or_resolve(e) for e in exprs)

    def op_eq(args) -> bool:
        if not isinstance(args, list) or len(args) != 2:
            raise ModError(f"'eq' expects a list of 2 elements, got: {args!r}")
        return ce.eval_or_resolve(args[0]) == ce.eval_or_resolve(args[1])

    def op_gt(args) -> bool:
        if not isinstance(args, list) or len(args) != 2:
            raise ModError(f"'gt' expects a list of 2 elements, got: {args!r}")
        left, right = ce.eval_or_resolve(args[0]), ce.eval_or_resolve(args[1])
        try:
            return left > right
        except TypeError:
            raise ModError(f"Cannot compare {left!r} and {right!r} with 'gt'")

    def op_lt(args) -> bool:
        if not isinstance(args, list) or len(args) != 2:
            raise ModError(f"'lt' expects a list of 2 elements, got: {args!r}")
        left, right = ce.eval_or_resolve(args[0]), ce.eval_or_resolve(args[1])
        try:
            return left < right
        except TypeError:
            raise ModError(f"Cannot compare {left!r} and {right!r} with 'lt'")

    def op_literal(value):
        return value
    
    ce.register("var", op_var)
    ce.register("not", op_not)
    ce.register("and", op_and)
    ce.register("or",  op_or)
    ce.register("eq",  op_eq)
    ce.register("gt",  op_gt)
    ce.register("lt",  op_lt)
    ce.register("literal",  op_literal)