# core/__pipeline.py

import asyncio
import inspect
from typing import Callable

from resources.__handler import Handler


async def _invoke(handler: Handler, event: dict, *args) -> None:
    """Appelle le handler, sync ou async de façon transparente."""
    if inspect.iscoroutinefunction(handler.func):
        await handler.func(event, *args)
    else:
        handler.func(event, *args)


class HandlerPipeline:
    """
    Exécute une liste ordonnée de handlers avec comportement selon leur mode.

    Construire une instance par emit(), puis appeler run() ou run_sync().
    """

    def __init__(
        self,
        handlers: list[Handler],
        on_error: Callable[[Handler, Exception], None],
    ):
        # Tri une seule fois, priorité décroissante
        self.handlers = sorted(handlers, key=lambda h: h.priority, reverse=True)
        self.on_error = on_error

    async def run(self, event: dict) -> None:
        await self._execute(event, 0)

    def run_sync(self, event: dict) -> None:
        """Entrée synchrone (pas de loop en cours)."""
        asyncio.run(self.run(event))

    async def _execute(self, event: dict, start: int) -> None:
        i = start
        while i < len(self.handlers):
            h = self.handlers[i]

            if h.mode == "chain":
                # Le handler contrôle la continuation via next()
                next_i = i + 1

                async def _next(captured=next_i):
                    await self._execute(event, captured)

                try:
                    await _invoke(h, event, _next)
                except Exception as e:
                    self.on_error(h, e)
                return  # chain owns continuation, qu'il appelle next() ou non

            elif h.mode == "shadow":
                try:
                    await _invoke(h, event)
                    return  # succès → stop
                except Exception as e:
                    self.on_error(h, e)
                    i += 1  # exception → fallback sur le suivant

            elif h.mode == "override":
                try:
                    await _invoke(h, event)
                except Exception as e:
                    self.on_error(h, e)
                return  # stop systématique, peu importe le résultat

            else:  # "normal" — et fallback sûr pour tout mode inconnu
                try:
                    await _invoke(h, event)
                except Exception as e:
                    self.on_error(h, e)
                i += 1
