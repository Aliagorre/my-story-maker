# core/__mod_storage.py

from pathlib import Path
from typing import Any


class ModStorage :
    def __init__(self) -> None:
        self.manifests : dict[str, dict] = {}
        self.states    : dict[str, str ] = {} # "enable" "disable" "discovered"
        self.instances : dict[str, Any]  = {} 
        self.paths     : dict[str, Path] = {}
        self.errors    : dict[str, list] = {}
        self.dependencies :dict[str, list]={}
        self.conflicts : dict[str, list] = {}
        self.load_order : list = []
