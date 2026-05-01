# resources/__handler.py

from typing import Callable, Literal

HandlerMode = Literal["normal", "shadow", "override", "chain"]
_VALID_MODES = {"normal", "shadow", "override", "chain"}


class Handler:
    """
    Wraps a callable with execution metadata.

    Modes:
    - normal:   toujours exécuté; exception catchée; pipeline continue
    - shadow:   succès → pipeline stop; exception → handler suivant (fallback)
    - override: toujours exécuté; pipeline stop quoi qu'il arrive
    - chain:    handler reçoit next() comme 2e arg; contrôle la continuation
    """

    def __init__(
        self,
        func: Callable,
        priority: int = 0,
        name: str | None = None,
        mode: HandlerMode = "normal",
        mod_name: str | None = None,
    ):
        if mode not in _VALID_MODES:
            raise ValueError(f"mode invalide '{mode}'. Valides : {_VALID_MODES}")
        self.func = func
        self.name = func.__name__ if name is None else name
        self.priority = priority
        self.mode: HandlerMode = mode
        self.mod_name = mod_name

    def __call__(self, event):
        return self.func(event)

    def __repr__(self):
        return f"Handler({self.name!r}, priority={self.priority}, mode={self.mode!r})"
