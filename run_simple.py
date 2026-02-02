import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.animation import FuncAnimation
import numpy as np

from model.kitchen_model import KitchenModel
from utils.constants import GRID_WIDTH, GRID_HEIGHT, WIN_THRESHOLD, LOSE_THRESHOLD

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

AGENT_COLORS = {
    'head_chef': '#9B59B6',
    'idle': '#3498DB',
    'moving': '#2ECC71',
    'working': '#E74C3C',
    'waiting_resource': '#F39C12',
    'waiting_path': '#F39C12'
}


class KitchenVisualizer:
    def __init__(self, model: KitchenModel):
        self.model = model
        self.fig, self.axes = plt.subplots(1, 2, figsize=(16, 8))
        self.ax_grid = self.axes[0]
        self.ax_info = self.axes[1]
        
        self.ax_grid.set_xlim(-0.5, GRID_WIDTH - 0.5)
        self.ax_grid.set_ylim(-0.5, GRID_HEIGHT - 0.5)
        self.ax_grid.set_aspect('equal')
        self.ax_grid.invert_yaxis()
        self.ax_grid.set_title('Cooperative Kitchen Simulation', fontsize=14, fontweight='bold')
        
        self.ax_grid.set_xticks(range(GRID_WIDTH))
        self.ax_grid.set_yticks(range(GRID_HEIGHT))
        self.ax_grid.grid(True, linewidth=0.5, color='gray', alpha=0.3)
        
        self.ax_info.axis('off')
        plt.tight_layout()
    
    def draw_frame(self):
        self.ax_grid.clear()
        self.ax_info.clear()
        
        self.ax_grid.set_xlim(-0.5, GRID_WIDTH - 0.5)
        self.ax_grid.set_ylim(-0.5, GRID_HEIGHT - 0.5)
        self.ax_grid.set_aspect('equal')
        self.ax_grid.invert_yaxis()
        self.ax_grid.set_xticks(range(GRID_WIDTH))
        self.ax_grid.set_yticks(range(GRID_HEIGHT))
        self.ax_grid.grid(True, linewidth=0.5, color='gray', alpha=0.3)
        
        for x in range(GRID_WIDTH):
            for y in range(GRID_HEIGHT):
                rect = mpatches.Rectangle((x-0.5, y-0.5), 1, 1, 
                                         facecolor='#F5F5F5', edgecolor='gray', linewidth=0.5)
                self.ax_grid.add_patch(rect)
        
        for pos, resource in self.model.resources.items():
            x, y = pos
            color = RESOURCE_COLORS.get(resource.type, '#808080')
            
            if resource.is_cooking():
                edge_color = '#FF8C00'
                edge_width = 4
            elif resource.occupied:
                edge_color = '#FF0000'
                edge_width = 3
            else:
                edge_color = 'black'
                edge_width = 1
            
            rect = mpatches.Rectangle((x-0.45, y-0.45), 0.9, 0.9,
                                      facecolor=color, edgecolor=edge_color, linewidth=edge_width)
            self.ax_grid.add_patch(rect)
            
            label = RESOURCE_LABELS.get(resource.type, '?')
            if resource.is_cooking():
                label = f"{label}\n{resource.cooking_timer}"
            self.ax_grid.text(x, y, label, ha='center', va='center', 
                            fontsize=7, fontweight='bold', color='white')
        
        if self.model.head_chef and self.model.head_chef.position:
            x, y = self.model.head_chef.position
            circle = mpatches.Circle((x, y), 0.35, facecolor='#9B59B6', edgecolor='black', linewidth=2)
            self.ax_grid.add_patch(circle)
            self.ax_grid.text(x, y, 'HC', ha='center', va='center', 
                            fontsize=9, fontweight='bold', color='white')
        
        for cook in self.model.cooks:
            if cook.position:
                x, y = cook.position
                color = AGENT_COLORS.get(cook.state, '#3498DB')
                circle = mpatches.Circle((x, y), 0.4, facecolor=color, edgecolor='black', linewidth=2)
                self.ax_grid.add_patch(circle)
                self.ax_grid.text(x, y, str(cook.cook_id), ha='center', va='center',
                                fontsize=10, fontweight='bold', color='white')
        
        completed = self.model.order_manager.get_completed_count()
        failed = self.model.order_manager.get_failed_count()
        title = f'Kitchen - Step {self.model.time_steps} | Completed: {completed}/{WIN_THRESHOLD} | Failed: {failed}/{LOSE_THRESHOLD}'
        
        if self.model.game_over:
            if self.model.game_result == 'win':
                title += ' | YOU WIN!'
            else:
                title += ' | GAME OVER'
        
        self.ax_grid.set_title(title, fontsize=12, fontweight='bold')
        
        self.ax_info.axis('off')
        self._draw_info_panel()
        
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
    
    def _draw_info_panel(self):
        info_text = []
        
        info_text.append("=== ACTIVE ORDERS ===")
        if self.model.order_manager.active_orders:
            for order in self.model.order_manager.active_orders[:5]:
                progress = order.get_completion_percentage()
                time_pct = order.time_remaining / order.time_limit * 100
                urgency = "[!!!]" if time_pct < 25 else "[!! ]" if time_pct < 50 else "[OK ]"
                info_text.append(f"{urgency} Order #{order.order_id}: {order.recipe.name}")
                info_text.append(f"   Time: {order.time_remaining}/{order.time_limit} | Progress: {progress:.0f}%")
            if len(self.model.order_manager.active_orders) > 5:
                info_text.append(f"   ... and {len(self.model.order_manager.active_orders) - 5} more")
        else:
            info_text.append("   No active orders")
        
        info_text.append("")
        
        clean = self.model.get_clean_plate_count()
        dirty = self.model.get_dirty_plate_count()
        info_text.append("=== PLATES ===")
        info_text.append(f"   Clean: {clean} | Dirty: {dirty} | In Use: {8 - clean - dirty}")
        
        info_text.append("")
        
        info_text.append("=== AGENTS ===")
        if self.model.head_chef:
            info_text.append(f"   [HC] Head Chef: {self.model.head_chef.get_status_string()}")
        
        for cook in self.model.cooks:
            status = cook.get_status_string()
            state_marker = {"idle": "[IDLE]", "moving": "[MOVE]", "working": "[WORK]", 
                          "waiting_resource": "[WAIT]", "waiting_path": "[PATH]"}.get(cook.state, "[???]")
            info_text.append(f"   {state_marker} Cook {cook.cook_id}: {status}")
        
        info_text.append("")
        
        info_text.append("=== LEGEND ===")
        info_text.append("   Resources: STR=Storage, CUT=Cutting, CTR=Counter")
        info_text.append("              STV=Stove, OVN=Oven, SNK=Sink")
        info_text.append("   Borders: Orange=Cooking, Red=Occupied")
        info_text.append("   States: Blue=Idle, Green=Move, Red=Work, Orange=Wait")
        
        full_text = "\n".join(info_text)
        self.ax_info.text(0.05, 0.95, full_text, transform=self.ax_info.transAxes,
                         fontsize=10, fontfamily='monospace', verticalalignment='top')


def run_simulation():
    print("Starting Cooperative Kitchen Simulation (Matplotlib mode)...")
    print("Close the window to stop.")
    print("Logs are saved to: kitchen_simulation.log")
    print()
    
    from utils.logger import logger
    
    model = KitchenModel(num_cooks=4)
    viz = KitchenVisualizer(model)
    
    plt.ion()
    
    try:
        while model.running:
            model.step()
            viz.draw_frame()
            plt.pause(0.3)
            
            if not plt.fignum_exists(viz.fig.number):
                break
        
        if plt.fignum_exists(viz.fig.number):
            viz.draw_frame()
            print("\nSimulation ended. Close the window to exit.")
            plt.ioff()
            plt.show()
    
    except KeyboardInterrupt:
        print("\nSimulation stopped by user.")
    
    finally:
        plt.close('all')
        from utils.logger import logger
        logger.close()
        print(f"\nLogs saved to: kitchen_simulation.log")
    
    print("\n" + "=" * 50)
    print("FINAL STATISTICS")
    print("=" * 50)
    print(f"Total time steps: {model.time_steps}")
    print(f"Completed orders: {model.order_manager.get_completed_count()}")
    print(f"Failed orders: {model.order_manager.get_failed_count()}")
    print(f"Result: {'WIN' if model.game_result == 'win' else 'LOSE' if model.game_result == 'lose' else 'INCOMPLETE'}")


if __name__ == "__main__":
    run_simulation()
