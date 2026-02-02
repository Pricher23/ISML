import mesa
from mesa.visualization.modules import CanvasGrid, ChartModule, TextElement
from mesa.visualization.ModularVisualization import ModularServer

from model.kitchen_model import KitchenModel
from visualization.portrayal import RESOURCE_COLORS, RESOURCE_LABELS
from utils.constants import GRID_WIDTH, GRID_HEIGHT, WIN_THRESHOLD, LOSE_THRESHOLD, TOTAL_PLATES


class OrderBoardElement(TextElement):
    def render(self, model):
        html = "<h3>Active Orders</h3>"
        html += "<div style='font-family: monospace; font-size: 12px;'>"
        
        if not model.order_manager.active_orders:
            html += "<p><i>No active orders</i></p>"
        else:
            for order in model.order_manager.active_orders:
                if order.time_remaining < order.time_limit * 0.25:
                    color = "#E74C3C"
                elif order.time_remaining < order.time_limit * 0.5:
                    color = "#F39C12"
                else:
                    color = "#27AE60"
                
                progress = order.get_completion_percentage()
                status = order.status.upper()
                
                html += f"<div style='margin: 5px 0; padding: 5px; background: #f5f5f5; border-left: 3px solid {color};'>"
                html += f"<b>Order #{order.order_id}:</b> {order.recipe.name}<br>"
                html += f"Time: <span style='color: {color};'>{order.time_remaining}/{order.time_limit}</span> | "
                html += f"Progress: {progress:.0f}%<br>"
                html += f"Status: {status}"
                html += "</div>"
        
        next_in = model.next_order_time - model.time_steps
        if next_in > 0:
            html += f"<p>Next order in: {next_in} steps</p>"
        
        html += "</div>"
        return html


class ScorePanelElement(TextElement):
    def render(self, model):
        completed = model.order_manager.get_completed_count()
        failed = model.order_manager.get_failed_count()
        clean_plates = model.get_clean_plate_count()
        dirty_plates = model.get_dirty_plate_count()
        
        html = "<h3>Kitchen Status</h3>"
        html += "<div style='font-family: monospace;'>"
        
        progress = (completed / WIN_THRESHOLD) * 100
        html += f"<b>Completed Orders:</b> {completed}/{WIN_THRESHOLD}<br>"
        html += f"<div style='background: #ddd; border-radius: 5px; margin: 5px 0;'>"
        html += f"<div style='background: #27AE60; width: {progress}%; height: 20px; border-radius: 5px;'></div>"
        html += "</div>"
        
        fail_progress = (failed / LOSE_THRESHOLD) * 100
        html += f"<b>Failed Orders:</b> <span style='color: #E74C3C;'>{failed}/{LOSE_THRESHOLD}</span><br>"
        html += f"<div style='background: #ddd; border-radius: 5px; margin: 5px 0;'>"
        html += f"<div style='background: #E74C3C; width: {fail_progress}%; height: 20px; border-radius: 5px;'></div>"
        html += "</div>"
        
        html += f"<br><b>Plates:</b><br>"
        html += f"Clean: {clean_plates} | Dirty: {dirty_plates} | In Use: {TOTAL_PLATES - clean_plates - dirty_plates}"
        
        html += f"<br><br><b>Time Step:</b> {model.time_steps}"
        
        if model.game_over:
            if model.game_result == 'win':
                html += "<br><br><div style='background: #27AE60; color: white; padding: 10px; text-align: center;'>"
                html += "<b>YOU WIN!</b></div>"
            else:
                html += "<br><br><div style='background: #E74C3C; color: white; padding: 10px; text-align: center;'>"
                html += "<b>GAME OVER</b></div>"
        
        html += "</div>"
        return html


class AgentStatusElement(TextElement):
    def render(self, model):
        html = "<h3>Agents</h3>"
        html += "<div style='font-family: monospace; font-size: 11px;'>"
        
        hc_status = model.head_chef.get_status_string() if model.head_chef else "N/A"
        html += f"<div style='background: #9B59B6; color: white; padding: 5px; margin: 2px 0;'>"
        html += f"<b>Head Chef:</b> {hc_status}"
        html += "</div>"
        
        state_colors = {
            'idle': '#3498DB',
            'moving': '#2ECC71',
            'working': '#E74C3C',
            'waiting_resource': '#F39C12',
            'waiting_path': '#F39C12'
        }
        
        for cook in model.cooks:
            color = state_colors.get(cook.state, '#808080')
            status = cook.get_status_string()
            
            html += f"<div style='background: {color}; color: white; padding: 5px; margin: 2px 0;'>"
            html += f"<b>Cook {cook.cook_id}:</b> {status}"
            
            if cook.current_task:
                html += f"<br>Task: {cook.current_task.task_type} (Order #{cook.current_task.order_id})"
            
            html += "</div>"
        
        html += "</div>"
        return html


class LegendElement(TextElement):
    def render(self, model):
        html = "<h3>Legend</h3>"
        html += "<div style='font-family: monospace; font-size: 11px;'>"
        
        for resource_type, color in RESOURCE_COLORS.items():
            label = RESOURCE_LABELS.get(resource_type, '?')
            name = resource_type.replace('_', ' ').title()
            html += f"<div style='display: inline-block; margin: 2px;'>"
            html += f"<span style='background: {color}; color: white; padding: 2px 5px;'>{label}</span> {name}"
            html += "</div><br>"
        
        html += "<br><b>Agents:</b><br>"
        html += "<span style='background: #9B59B6; color: white; padding: 2px 5px; border-radius: 50%;'>HC</span> Head Chef<br>"
        html += "<span style='background: #3498DB; color: white; padding: 2px 5px; border-radius: 50%;'>1-4</span> Line Cooks<br>"
        
        html += "<br><b>Cook States:</b><br>"
        html += "<span style='background: #3498DB; color: white; padding: 2px 5px;'>Blue</span> Idle<br>"
        html += "<span style='background: #2ECC71; color: white; padding: 2px 5px;'>Green</span> Moving<br>"
        html += "<span style='background: #E74C3C; color: white; padding: 2px 5px;'>Red</span> Working<br>"
        html += "<span style='background: #F39C12; color: white; padding: 2px 5px;'>Orange</span> Waiting<br>"
        
        html += "</div>"
        return html


def canvas_portrayal(agent):
    from model.resources import ResourceAgent
    from agents.head_chef import HeadChef
    from agents.line_cook import LineCook
    
    if agent is None:
        return None
    
    if isinstance(agent, ResourceAgent):
        color = RESOURCE_COLORS.get(agent.resource_type, '#808080')
        label = RESOURCE_LABELS.get(agent.resource_type, '?')
        
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
        
        if hasattr(agent, 'model') and agent.position in agent.model.resources:
            resource = agent.model.resources[agent.position]
            if resource.is_cooking():
                portrayal["stroke_color"] = "#FF8C00"
                portrayal["stroke_width"] = 3
                label = RESOURCE_LABELS.get(agent.resource_type, '?')
                portrayal["text"] = f"{label}:{resource.cooking_timer}"
            elif resource.occupied:
                portrayal["stroke_color"] = "#FF0000"
                portrayal["stroke_width"] = 3
        
        return portrayal
    
    if isinstance(agent, HeadChef):
        return {
            "Shape": "circle",
            "Filled": "true",
            "Layer": 2,
            "r": 0.6,
            "Color": "#9B59B6",
            "text": "HC",
            "text_color": "white"
        }
    
    if isinstance(agent, LineCook):
        state_colors = {
            'idle': '#3498DB',
            'moving': '#2ECC71',
            'working': '#E74C3C',
            'waiting_resource': '#F39C12',
            'waiting_path': '#F39C12'
        }
        return {
            "Shape": "circle",
            "Filled": "true",
            "Layer": 2,
            "r": 0.8,
            "Color": state_colors.get(agent.state, '#3498DB'),
            "text": str(agent.cook_id),
            "text_color": "white"
        }
    
    return None


def create_server(model_params: dict = None) -> ModularServer:
    if model_params is None:
        model_params = {
            "width": GRID_WIDTH,
            "height": GRID_HEIGHT,
            "num_cooks": 4
        }
    
    cell_size = 50
    canvas_width = GRID_WIDTH * cell_size
    canvas_height = GRID_HEIGHT * cell_size
    
    canvas = CanvasGrid(canvas_portrayal, GRID_WIDTH, GRID_HEIGHT, canvas_width, canvas_height)
    
    order_board = OrderBoardElement()
    score_panel = ScorePanelElement()
    agent_status = AgentStatusElement()
    legend = LegendElement()
    
    order_chart = ChartModule(
        [
            {"Label": "Completed", "Color": "#27AE60"},
            {"Label": "Failed", "Color": "#E74C3C"},
            {"Label": "Active", "Color": "#3498DB"}
        ],
        data_collector_name='datacollector'
    )
    
    server = ModularServer(
        KitchenModel,
        [canvas, score_panel, order_board, agent_status, legend],
        "Cooperative Kitchen Simulation",
        model_params
    )
    
    return server
