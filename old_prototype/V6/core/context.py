# core/context.py
import copy
from typing import Any, Callable, Dict, List

from core.condition_engine import ConditionEngine
from EVENTS import EventBus

HookHandler = Callable[..., None]

CORE_EVENTS = [
    "on_game_start",
    "on_node_enter",
    "on_choice_selected",
    "on_engine_warning",
    "on_engine_error",
    "on_engine_log" ,
    "on_cli_input",
    "on_save",
    "on_load",
    "on_tick",
    "on_exit",
]

class Context:
    def __init__(self):
        self.state = {}
        self.mod_states = {}
        self.save_data = {}
        self.current_node = None

        self.events = EventBus()
        for ev in CORE_EVENTS:
            self.events.register_event(ev)

        # Handlers par défaut pour éviter les crashs avant chargement des mods
        def _default_error_handler(msg):
            raise RuntimeError(msg)
        self.events.on("on_engine_error", _default_error_handler)
        self.events.on("on_engine_warning", lambda msg: None)

        self.condition_engine = ConditionEngine(self)

        def _emit_action(ctx, args):
            if isinstance(args, str):
                ctx.events.emit(args, ctx)
            elif isinstance(args, list) and len(args) >= 1:
                ctx.events.emit(args[0], ctx, *args[1:])
            else:
                ctx.events.emit_warning(f"Invalid emit action args: {args}")

        self.mod_states["actions"] = {
            "set":   lambda ctx, args: ctx.state.__setitem__(args[0], args[1]),
            "unset": lambda ctx, args: ctx.state.pop(args[0] if isinstance(args, list) else args, None),
            "emit":  _emit_action,
        }

    def reset(self):
        self.__init__()  # simple, propre, garanti correct



class RegistrationContext(Context):
    def __init__(self, base: Context):
        self._base = base
        self.state        = copy.deepcopy(base.state)
        self.mod_states   = copy.deepcopy(base.mod_states)
        self.save_data    = copy.deepcopy(base.save_data)
        self.current_node = base.current_node

        # FIX #8 : deepcopy(base.events) copie les objets capturés par les
        # closures des handlers, ce qui crée des références vers des copies
        # fantômes du contexte plutôt que vers le vrai contexte après commit().
        #
        # Correction : on crée un EventBus vierge puis on copie les *listes* de
        # handlers par valeur (shallow copy), sans jamais copier les handlers
        # eux-mêmes.  Les closures continuent de pointer vers les objets d'origine.
        # Les nouveaux handlers ajoutés pendant register() s'accumulent dans les
        # nouvelles listes sans toucher à base.events.
        self.events = EventBus()
        for event_name, handlers in base.events._events.items():
            self.events._events[event_name] = list(handlers)  # FIX #8

        # CE frais lié à reg_ctx, puis on recopie les opérateurs custom
        self.condition_engine = ConditionEngine(self)
        self.condition_engine.operators.update(base.condition_engine.operators)

    def commit(self):
        self._base.state        = self.state
        self._base.mod_states   = self.mod_states
        self._base.save_data    = self.save_data   # FIX #7 : save_data était oublié ;
        self._base.current_node = self.current_node  # toute modification faite pendant
        # register() était silencieusement perdue après commit().

        # On ne crée PAS un nouveau CE — on repointe le contexte de l'existant
        # pour que les closures qui ont capturé ce CE voient le vrai ctx.
        self.condition_engine.context = self._base
        self._base.condition_engine   = self.condition_engine
        self._base.events             = self.events        self._base.events             = self.events