# core/condition_engine.py
from core.errors import EngineError

class ConditionEngine:
    def __init__(self, context):
        self.context = context
        self.operators = {}

    def register(self, name, func):
        if not callable(func):
            raise EngineError(f"Operator '{name}' must be callable")
        self.operators[name] = func

    def evaluate(self, expr) -> bool:
        if isinstance(expr, dict):
            if len(expr) != 1:
                raise EngineError(f"Invalid condition object: {expr}")
            op, value = next(iter(expr.items()))
            if op not in self.operators:
                raise EngineError(f"Unknown operator '{op}'")
            try:
                return self.operators[op](value)
            except Exception as e:
                raise EngineError(f"Error in operator '{op}': {e}")
        if isinstance(expr, bool):
            return expr
        if isinstance(expr, str):
            return bool(self.resolve(expr))
        if isinstance(expr, (int, float)):
            return bool(expr)
        raise EngineError(f"Invalid condition type: {expr}")

    def resolve(self, value):
        if isinstance(value, str):
            return self.get_variable(value)
        return value

    def get_variable(self, name: str):
        if name in self.context.state:
            return self.context.state[name]
        if name in self.context.mod_states:
            return self.context.mod_states[name]
        if "." in name:
            parts = name.split(".")
            obj = self.context.state.get(parts[0])
            if obj is None and parts[0] in self.context.mod_states:
                obj = self.context.mod_states[parts[0]]
            for key in parts[1:]:
                if isinstance(obj, dict) and key in obj:
                    obj = obj[key]
                else:
                    return None
            return obj
        return None

    def eval_or_resolve(self, value):
        if isinstance(value, dict):
            if len(value) != 1:
                raise EngineError(f"Invalid condition object: {value}")
            op, args = next(iter(value.items()))
            if op not in self.operators:
                raise EngineError(f"Unknown operator '{op}'")
            return self.operators[op](args)
        if isinstance(value, list):
            return [self.eval_or_resolve(v) for v in value]
        return self.resolve(value)
