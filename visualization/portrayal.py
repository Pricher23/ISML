from typing import Dict, Any, Optional


def agent_portrayal(agent) -> Optional[Dict[str, Any]]:
    from agents.head_chef import HeadChef
    from agents.line_cook import LineCook
    
    if agent is None:
        return None
    
    portrayal = {
        "Shape": "circle",
        "Filled": "true",
        "Layer": 2,
        "r": 0.8
    }
    
    if isinstance(agent, HeadChef):
        portrayal["Color"] = "#9B59B6"
        portrayal["text"] = "HC"
        portrayal["text_color"] = "white"
        portrayal["r"] = 0.7
    
    elif isinstance(agent, LineCook):
        state = agent.state
        if state == "idle":
            portrayal["Color"] = "#3498DB"
        elif state == "moving":
            portrayal["Color"] = "#2ECC71"
        elif state == "working":
            portrayal["Color"] = "#E74C3C"
        elif state in ["waiting_resource", "waiting_path"]:
            portrayal["Color"] = "#F39C12"
        else:
            portrayal["Color"] = "#3498DB"
        
        portrayal["text"] = str(agent.cook_id)
        portrayal["text_color"] = "white"
    
    return portrayal


def get_grid_portrayal(model) -> callable:
    def portrayal_func(agent):
        return agent_portrayal(agent)
    
    return portrayal_func


RESOURCE_COLORS = {
    'storage': '#D4A574',
    'stove': '#E74C3C',
    'oven': '#C0392B',
    'cutting_board': '#27AE60',
    'counter': '#F1C40F',
    'sink': '#3498DB'
}

RESOURCE_LABELS = {
    'storage': 'STR',
    'stove': 'STV',
    'oven': 'OVN',
    'cutting_board': 'CUT',
    'counter': 'CTR',
    'sink': 'SNK'
}


def get_resource_portrayal(resource) -> Dict[str, Any]:
    color = RESOURCE_COLORS.get(resource.type, '#808080')
    label = RESOURCE_LABELS.get(resource.type, '?')
    
    portrayal = {
        "Shape": "rect",
        "Filled": "true",
        "Layer": 0,
        "w": 1,
        "h": 1,
        "Color": color,
        "text": label,
        "text_color": "white"
    }
    
    if resource.occupied:
        portrayal["stroke_color"] = "#FF0000"
        portrayal["stroke_width"] = 3
    
    return portrayal
