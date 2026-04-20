from core.node import *

class Graph:
    def __init__(self) -> None:
        self.root        :str = ""
        self.active_node :str = ""
        self.links       :dict[str,list[str]] = {}
        self.retro_links :dict[str,list[str]] = {}
        self.nodes       :dict[str,Node]      = {}

    def active_node_obj(self) -> Node :
        return self.nodes[self.active_node]

    def init_nodes(self,node_dict:dict[str,dict[str,Any]]) -> None :
        for node_key in node_dict :
            working_node = Node()
            working_node.init_node(node_dict[node_key])
            self.nodes[node_key] = working_node
    
    def nodes_data(self) -> dict[str,dict[str,Any]] :
        dict_data = {}
        for node_key in self.nodes :
            dict_data[node_key] = self.nodes[node_key].node_dict()
        return dict_data
    
    def option(self,story:NoneFunc=none,other_choice:list[str]=[]) -> str :
        neighbor_nodes_key = self.links[self.active_node]
        neighbor_nodes     = [self.nodes[key] for key in neighbor_nodes_key]
        accessible_nodes   = [node for node in neighbor_nodes if node.active()]
        labels_nodes       = [node.label for node in accessible_nodes]
        choice = while_input(labels_nodes + other_choice + ["Retour au menu"],
                             "> Choissisez votre voie\n> ",
                             "> Choissisez une voie correcte\n> ",
                             "# --- Un embranchement vous fait face --- #",[],story)
        return choice

    def debug(self) -> None :
        clear_screen()
        print("Not implemented")
        input()
