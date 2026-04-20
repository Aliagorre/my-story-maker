import os
import importlib
import pkgutil
from core.utils import clear_screen, enumerate_list
from core.metadata import MODULE_DIR, ALL_VARS

clear_screen()

modules = [
    m for m in os.listdir(MODULE_DIR)
    if not m.endswith(".py") and not m.startswith("__")
]

ACTIVE_MODULES = []
ALL_MOD_VARS = {}

def module_vars(mod):

    # Récupération de toutes les variables globales du module
    vars_in_module = {}
    for name, value in vars(mod).items():
        # On ignore les variables privées et les builtins
        if name.startswith("_"):
            continue
        # On ignore les fonctions, classes, modules
        if callable(value):
            continue
        if isinstance(value, type(importlib)):
            continue

        vars_in_module[name] = value

    return vars_in_module

def serialize_vars() -> None:
    global ALL_VARS, ALL_MOD_VARS
    for module in ALL_MOD_VARS :
        for var in ALL_MOD_VARS[module] :
            if var in ALL_VARS :
                print(f"edit : {var}")
                t2 = type(ALL_VARS[var])
                t1 = type(ALL_MOD_VARS[module][var])
                if not (t1 is list or t2 is dict) :
                    print(f"{module} -> not listable variable")
                    raise TypeError(f"{module} -> not listable variable")
                elif t1 != t2 :
                    print(f"{module} -> not compatible variable")
                    raise TypeError(f"{module} -> not compatible variable")
                elif t2 == dict :
                    tmp = ALL_MOD_VARS[module][var] | ALL_VARS[var]
                    ALL_VARS[var] = tmp
                elif t2 == list :
                    ALL_VARS[var] += ALL_MOD_VARS[module][var]
                else :
                    print(ALL_VARS[var],ALL_MOD_VARS[module][var])
                    print(f"{module} -> not compatible variable")
                    raise TypeError(f"{module} -> variable")
            else :
                print(f"def : {var}")
                ALL_VARS[var] = ALL_MOD_VARS[module][var].copy()


if len(modules) == 0 :
    print("No module found")
else :
    print(f"{len(modules)} Module{"s" if len(modules) > 1 else ""} found")
    enumerate_list(modules)
    for module in modules:
        try:
            mod = importlib.import_module(f"{MODULE_DIR}.{module}")
            ACTIVE_MODULES.append(module)
            ALL_MOD_VARS[module] = module_vars(mod)
            if hasattr(mod, "__path__"):
                for _, sub, _ in pkgutil.iter_modules(mod.__path__):
                    if not sub.startswith("__"):
                        
                        sub_mod = importlib.import_module(f"{MODULE_DIR}.{module}.{sub}")
                        
                        print(f"success load: {module}.{sub}")
                        ACTIVE_MODULES.append(f"{module}.{sub}")

                        ALL_MOD_VARS[f"{module}.{sub}"] = module_vars(sub_mod)
            print(f"success load: {module}")

        except Exception as e:
            print(f"{module} : load fail ->  ({e})")

    serialize_vars()

    print("\nAll modules Load : ")
    enumerate_list(ACTIVE_MODULES)

input()