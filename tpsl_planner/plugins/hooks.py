from typing import List, Protocol, Dict, Any

class PlannerHook(Protocol):
    def on_trade_saved(self, trade: Dict[str, Any]) -> None: ...
    def on_push_clicked(self, context: Dict[str, Any]) -> None: ...

_PLUGINS: List[PlannerHook] = []

def register(plugin: PlannerHook) -> None:
    _PLUGINS.append(plugin)

def run(event: str, payload: Dict[str, Any]) -> None:
    for p in _PLUGINS:
        if hasattr(p, event):
            getattr(p, event)(payload)
