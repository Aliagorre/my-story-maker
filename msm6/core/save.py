from core.graph import *
import importlib.util
from pathlib import Path

COMMON = '''
from module import *
from core.utils import none, true, false, YES, NO
'''

def format_dict_as_python(d:Any, name:str, indent:int=4) -> str:
    def fmt(value, level) -> str:
        space = " " * (indent * level)

        if isinstance(value, dict):
            items = []
            for k, v in value.items():
                items.append(f'{space}{indent*" "}"{k}" : {fmt(v, level+1)}')
            return "{\n" + ",\n".join(items) + f"\n{space}}}"
            
        elif isinstance(value, list):
            items = []
            for v in value:
                items.append(f'{space}{indent*" "}{fmt(v, level+1)}')
            return "[\n" + ",\n".join(items) + f"\n{space}]"

        elif callable(value):
            return value.__name__ 
        elif value is str :
            return f"'''{value}'''"

        else:
            return f'"{value}"'

    return f"{name} = " + fmt(d, 0) + "\n"

def load_save(path) :
    path = Path(path)
    spec:Any = importlib.util.spec_from_file_location("save", path)
    save = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(save)
    return save

def create_save(path:str,version:str=":debug",modules:list=[],is_save:bool=True) -> None :
    file = path.split("/")[-1]
    name = file.removesuffix(".py").removesuffix("_save")
    with open(path, "w", encoding="utf-8") as f:
        f.write(COMMON)
        f.write(format_dict_as_python(name     ,"name"))
        f.write(format_dict_as_python(version  ,"version"))
        f.write(format_dict_as_python(modules  ,"module"))
        f.write(format_dict_as_python(path     ,"path"))
        f.write(format_dict_as_python("default","root"))
        f.write(format_dict_as_python("default","active_node"))
        f.write(format_dict_as_python({"default":[]},"link"))
        f.write(format_dict_as_python({"default":[]},"retro_links"))
        f.write(format_dict_as_python({"default":Node().node_dict()},"nodes"))
        f.write(format_dict_as_python({},"data"))
        f.write(format_dict_as_python("","story"))
    
def copy_save(src_path:str,dest_path:str) -> None :
    src = Save(src_path)
    if src_path != dest_path :
        src.path = dest_path
        file = dest_path.split("/")[-1]
        name = file.removesuffix("_save.py")
        src.name = name
        src.write()

def rename_save(path:str,new_path:str) -> None :
    copy_save(path,new_path)
    remove_directory(path)

class Save :
    def __init__(self, path:str) -> None :
        save = load_save(path)
        self.name   :str       = save.name
        self.version:str       = save.version
        self.modules:list[str] = save.module.copy()
        self.path   :str       = path

        self.data      = save.data
        self.story:str = save.story

        self.graph = Graph()
        self.graph.links       = save.link
        self.graph.retro_links = save.retro_links
        self.graph.root        = save.root
        self.graph.active_node = save.active_node
        self.graph.init_nodes(save.nodes)

    def write(self) -> None :
        with open(self.path, "w", encoding="utf-8") as f:
            f.write(COMMON)
            f.write(format_dict_as_python(self.name   ,"name"))
            f.write(format_dict_as_python(self.version,"version"))
            f.write(format_dict_as_python(self.modules,"module"))
            f.write(format_dict_as_python(self.path   ,"path"))
            f.write(format_dict_as_python(self.graph.root,"root"))
            f.write(format_dict_as_python(self.graph.active_node,"active_node"))
            f.write(format_dict_as_python(self.graph.links,"link"))
            f.write(format_dict_as_python(self.graph.retro_links,"retro_links"))
            f.write(format_dict_as_python(self.graph.nodes_data(),"nodes"))
            f.write(format_dict_as_python(self.data   ,"data"))
            f.write(format_dict_as_python(self.story  ,"story"))

    def draw_story(self) -> None :
        clear_screen()
        print(self.story)
        sep()

    def start(self) -> None :
        choice = self.graph.option(self.draw_story)
        if choice == "Retour au menu" :
            pass
        elif choice == ":debug" :
            self.graph.debug()
            self.start()
        else :
            self.graph.active_node = choice
            self.story += "\n" + self.graph.active_node_obj().text
            self.start()
