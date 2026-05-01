# resources/__handler.py

from typing import Callable

mode = "normal", "shadow", "override", "chain"


class Handler:
    def __init__(
        self,
        func: Callable,
        priority: int = 0,
        name: str | None = None,
        mode: str = "normal",
        mod_name: str | None = None,
    ):
        self.name: str = func.__name__ if name is None else name
        self.func = func
        self.priority = priority
        self.mode = mode
        self.mod_name = mod_name

    def __call__(self, event):
        return self.func(event)

    def __name__(self):
        return self.func.__name__
