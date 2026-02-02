from __future__ import annotations

import mesa
import random
from typing import Dict, List, Tuple, Optional, Set, TYPE_CHECKING

try:
    from mesa.datacollection import DataCollector
except ImportError:
    from mesa import DataCollector

try:
    from mesa.time import RandomActivation
except (ImportError, AttributeError):
    RandomActivation = None

try:
    from mesa.space import MultiGrid
except ImportError:
    MultiGrid = None

from model.resources import Resource, Plate, ResourceAgent
from model.recipes import get_random_recipe, RECIPES
from model.orders import Order, OrderManager
from utils.constants import (
    GRID_WIDTH, GRID_HEIGHT, TOTAL_PLATES,
    ORDER_INTERVAL_MIN, ORDER_INTERVAL_MAX,
    WIN_THRESHOLD, LOSE_THRESHOLD, PlateState, TaskState
)

if TYPE_CHECKING:
    from agents.head_chef import HeadChef
    from agents.line_cook import LineCook


class KitchenModel(mesa.Model):
    def __init__(self, width: int = GRID_WIDTH, height: int = GRID_HEIGHT, num_cooks: int = 4):
        super().__init__()
        
        if MultiGrid is not None:
            self.grid = MultiGrid(width, height, torus=False)
        else:
            self.grid = mesa.space.MultiGrid(width, height, torus=False)
        
        if RandomActivation is not None:
            self.schedule = RandomActivation(self)
        else:
            self.schedule = None
            self._agents_list = []
        
        self.running = True
        self.time_steps = 0
        self.game_over = False
        self.game_result = None
        
        self.order_manager = OrderManager()
        self.next_order_time = random.randint(ORDER_INTERVAL_MIN, ORDER_INTERVAL_MAX)
        
        self.resources: Dict[Tuple[int, int], Resource] = {}
        self.resource_agents: Dict[Tuple[int, int], ResourceAgent] = {}
        self.resource_positions: Set[Tuple[int, int]] = set()
        self.resource_id_counter = 0
        self.agent_id_counter = 1000
        
        self.plates: List[Plate] = [Plate(i, PlateState.CLEAN) for i in range(TOTAL_PLATES)]
        
        self.head_chef: Optional['HeadChef'] = None
        self.cooks: List['LineCook'] = []
        
        self._setup_kitchen_layout()
        self._setup_agents(num_cooks)
        
        self.datacollector = DataCollector(
            model_reporters={
                "Completed": lambda m: m.order_manager.get_completed_count(),
                "Failed": lambda m: m.order_manager.get_failed_count(),
                "Active": lambda m: m.order_manager.get_active_count(),
                "Clean_Plates": lambda m: m.get_clean_plate_count()
            }
        )
        
        print("\n" + "=" * 40)
        print("  COOPERATIVE KITCHEN SIMULATION")
        print("=" * 40)
        print(f"  Grid: {width}x{height} | Cooks: {num_cooks}")
        print(f"  Win: {WIN_THRESHOLD} orders | Lose: {LOSE_THRESHOLD} failures")
        print("=" * 40 + "\n")
    
    def _setup_kitchen_layout(self):
        storage_positions = [
            (0, 0), (1, 0), (2, 0),
            (0, 1), (1, 1), (2, 1),
            (0, 2), (1, 2), (2, 2)
        ]
        for pos in storage_positions:
            self._add_resource('storage', pos)
        
        cutting_positions = [
            (4, 1), (5, 1),
            (4, 2), (5, 2)
        ]
        for pos in cutting_positions:
            self._add_resource('cutting_board', pos)
        
        counter_positions = [
            (7, 3), (8, 3),
            (7, 4), (8, 4)
        ]
        for pos in counter_positions:
            self._add_resource('counter', pos)
        
        stove_positions = [(0, 7), (1, 7), (2, 7)]
        for pos in stove_positions:
            self._add_resource('stove', pos)
        
        oven_positions = [(8, 7), (9, 7)]
        for pos in oven_positions:
            self._add_resource('oven', pos)
        
        self._add_resource('sink', (11, 7))
    
    def _add_resource(self, resource_type: str, position: Tuple[int, int]):
        resource = Resource(resource_type, position, self.resource_id_counter)
        self.resources[position] = resource
        self.resource_positions.add(position)
        self.resource_id_counter += 1
        
        resource_agent = ResourceAgent(self.agent_id_counter, self, resource_type, position)
        self.resource_agents[position] = resource_agent
        self.grid.place_agent(resource_agent, position)
        self.agent_id_counter += 1
    
    def _setup_agents(self, num_cooks: int):
        from agents.head_chef import HeadChef
        from agents.line_cook import LineCook
        
        valid_positions = []
        for x in range(GRID_WIDTH):
            for y in range(GRID_HEIGHT):
                if (x, y) not in self.resource_positions:
                    valid_positions.append((x, y))
        
        random.shuffle(valid_positions)
        
        self.head_chef = HeadChef(0, self)
        hc_pos = valid_positions.pop()
        self.grid.place_agent(self.head_chef, hc_pos)
        self.head_chef.position = hc_pos
        self._add_agent_to_schedule(self.head_chef)
        
        for i in range(num_cooks):
            cook = LineCook(i + 1, self, cook_id=i + 1)
            cook_pos = valid_positions.pop()
            self.grid.place_agent(cook, cook_pos)
            cook.position = cook_pos
            self.cooks.append(cook)
            self._add_agent_to_schedule(cook)
    
    def _add_agent_to_schedule(self, agent):
        if self.schedule is not None:
            self.schedule.add(agent)
        else:
            self._agents_list.append(agent)
    
    def _step_agents(self):
        if self.schedule is not None:
            self.schedule.step()
        else:
            random.shuffle(self._agents_list)
            for agent in self._agents_list:
                agent.step()
    
    def step(self):
        if not self.running:
            return
        
        from utils.logger import logger
        
        self.time_steps += 1
        logger.time_step_header(self.time_steps)
        
        failed_orders = self.order_manager.tick_all_orders()
        for order in failed_orders:
            if order.plate_id is not None:
                self.plates[order.plate_id].mark_dirty()
        
        self._tick_cooking_resources()
        
        if self.time_steps >= self.next_order_time:
            self._generate_order()
            self.next_order_time = self.time_steps + random.randint(ORDER_INTERVAL_MIN, ORDER_INTERVAL_MAX)
        
        self._step_agents()
        
        self._check_game_state()
        
        self.datacollector.collect(self)
        
        self._print_status()
    
    def _tick_cooking_resources(self):
        from utils.logger import logger
        
        for pos, resource in self.resources.items():
            if resource.is_cooking():
                task = resource.cooking_task
                cook_id = resource.cooking_started_by
                
                if resource.tick_cooking():
                    if task:
                        logger.resource_cooking_done(self.time_steps, resource.type, 
                                                    task.task_type, task.order_id)
                        
                        task.status = TaskState.COMPLETED
                        task.progress = task.duration
                        self.head_chef.notify_task_complete(task, cook_id)
    
    def _generate_order(self):
        recipe = get_random_recipe()
        order = self.order_manager.create_order(recipe, self.time_steps)
        
        clean_plates = [p for p in self.plates if p.is_clean()]
        if clean_plates:
            plate = clean_plates[0]
            plate.assign_to_order(order.order_id)
            order.assign_plate(plate.plate_id)
    
    def _check_game_state(self):
        completed = self.order_manager.get_completed_count()
        failed = self.order_manager.get_failed_count()
        
        from utils.logger import logger
        
        if failed >= LOSE_THRESHOLD:
            self.running = False
            self.game_over = True
            self.game_result = 'lose'
            logger.game_lose(self.time_steps, completed, failed)
        
        elif completed >= WIN_THRESHOLD:
            self.running = False
            self.game_over = True
            self.game_result = 'win'
            logger.game_win(self.time_steps, completed, failed)
    
    def _print_status(self):
        completed = self.order_manager.get_completed_count()
        failed = self.order_manager.get_failed_count()
        active = self.order_manager.get_active_count()
        clean_plates = self.get_clean_plate_count()
        
        print(f"Status: Completed {completed}/{WIN_THRESHOLD} | Failed {failed}/{LOSE_THRESHOLD} | "
              f"Active {active} | Plates {clean_plates}")
    
    def get_resource_locations(self) -> Dict[str, List[Tuple[int, int]]]:
        locations = {}
        for pos, resource in self.resources.items():
            if resource.type not in locations:
                locations[resource.type] = []
            locations[resource.type].append(pos)
        return locations
    
    def get_cook_by_id(self, cook_id: int) -> Optional['LineCook']:
        for cook in self.cooks:
            if cook.cook_id == cook_id:
                return cook
        return None
    
    def get_clean_plate_count(self) -> int:
        return sum(1 for p in self.plates if p.is_clean())
    
    def get_dirty_plate_count(self) -> int:
        return sum(1 for p in self.plates if p.is_dirty())
    
    def is_position_walkable(self, position: Tuple[int, int]) -> bool:
        if position in self.resources:
            return self.resources[position].type == 'storage'
        return True
