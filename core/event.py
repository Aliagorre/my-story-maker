CRITICAL = "CRITICAL"
WARNING = "WARNING"
DEBUG = "DEBUG"
ERROR = "ERROR"
INFO = "INFO"
LOG = "LOG"

ENGINE_BOOT = "ENGINE_BOOT"
ENGINE_INIT = "ENGINE_INIT"
ENGINE_READY= "ENGINE_READY"
ENGINE_TICK = "ENGINE_TICK"
ENGINE_SHUTDOWN= "ENGINE_SHUTDOWN"
ENGINE_ERROR= "ENGINE_ERROR"
ENGINE_FATAL_ERROR = "ENGINE_FATAL_ERROR"
MOD_DISCOVERED= "MOD_DISCOVERED"
MOD_LOADED = "MOD_LOADED"
MOD_INITIALIZED = "MOD_INITIALIZED"
MOD_ERROR = "MOD_ERROR"
MOD_MANIFEST_ERROR = "MOD_MANIFEST_ERROR"
MOD_DEPENDENCY_ERROR = "MOD_DEPENDENCY_ERROR"
MOD_CONFLICT = "MOD_CONFLICT"
'''
{
  "name": "ENGINE_READY",
  "source": "core",
  "payload": {},
  "timestamp": 1234567890
}
'''
def event_scheme(name : str, source : str, payload : dict, timestamp: int) -> dict:
    return {
  "name": name,
  "source": source,
  "payload": payload,
  "timestamp": timestamp
}

def is_event_structure(event : dict) -> bool :
    if "name" not in event :
        return False
    elif not is_upper_case(event["name"]) :
        return False
    elif "source" not in event :
        return False
    elif not isinstance(event["source"], str) :
        return False
    elif "payload" not in event :
        return False
    elif not isinstance(event["payload"], dict) :
        return False
    elif "timestamp" not in event :
        return False
    elif not isinstance(event["timestamp"], int) :
        return False
    else :
        return True
    
def is_snake_case(string:str) -> bool :
    if not string :
        return False
    else :
        return all("a" <= x <= "z" or "0" <= x <= "9" or x == "_"  for x in string)
    
def is_upper_case(string : str) -> bool :
    if not string :
        return False
    else :
        return all("A" <= x <= "Z" or "0" <= x <= "9" or x == "_"  for x in string)