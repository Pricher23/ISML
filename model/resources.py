import mesa
from typing import Optional, List, Tuple
from utils.constants import PlateState


class ResourceAgent(mesa.Agent):
    def __init__(self, unique_id: int, model, resource_type: str, position: Tuple[int, int]):
        try:
            super().__init__(unique_id, model)
        except TypeError:
            super().__init__(model)
            self.unique_id = unique_id
        
        self.resource_type = resource_type
        self.position = position
        self.occupied = False
        self.occupied_by: Optional[int] = None
    
    def step(self):
        pass


class Resource:
    UNATTENDED_TASKS = {'grill', 'cook', 'saute', 'bake', 'cook_rice'}
    
    def __init__(self, resource_type: str, position: Tuple[int, int], resource_id: int):
        self.type = resource_type
        self.position = position
        self.resource_id = resource_id
        self.occupied = False
        self.occupied_by: Optional[int] = None
        self.queue: List[int] = []
        
        self.cooking = False
        self.cooking_timer: int = 0
        self.cooking_task = None
        self.cooking_started_by: Optional[int] = None
    
    def occupy(self, agent_id: int) -> bool:
        if not self.occupied:
            self.occupied = True
            self.occupied_by = agent_id
            if agent_id in self.queue:
                self.queue.remove(agent_id)
            return True
        return False
    
    def release(self) -> Optional[int]:
        self.occupied = False
        self.occupied_by = None
        
        if self.queue:
            return self.queue[0]
        return None
    
    def start_cooking(self, task, cook_id: int, duration: int):
        self.cooking = True
        self.cooking_timer = duration
        self.cooking_task = task
        self.cooking_started_by = cook_id
        self.occupied = True
        self.occupied_by = None
    
    def tick_cooking(self) -> bool:
        if not self.cooking:
            return False
        
        self.cooking_timer -= 1
        
        if self.cooking_timer <= 0:
            self.cooking = False
            completed_task = self.cooking_task
            self.cooking_task = None
            self.occupied = False
            return True
        
        return False
    
    def is_cooking(self) -> bool:
        return self.cooking
    
    def get_cooking_time_remaining(self) -> int:
        return self.cooking_timer if self.cooking else 0
    
    @classmethod
    def is_unattended_task(cls, task_type: str) -> bool:
        return task_type in cls.UNATTENDED_TASKS
    
    def add_to_queue(self, agent_id: int):
        if agent_id not in self.queue and agent_id != self.occupied_by:
            self.queue.append(agent_id)
    
    def remove_from_queue(self, agent_id: int):
        if agent_id in self.queue:
            self.queue.remove(agent_id)
    
    def get_queue_position(self, agent_id: int) -> int:
        if agent_id in self.queue:
            return self.queue.index(agent_id)
        return -1
    
    def __repr__(self):
        status = f"occupied by {self.occupied_by}" if self.occupied else "free"
        return f"Resource({self.type}, pos={self.position}, {status})"


class Plate:
    def __init__(self, plate_id: int, state: str = PlateState.CLEAN):
        self.plate_id = plate_id
        self.state = state
        self.assigned_order: Optional[int] = None
    
    def assign_to_order(self, order_id: int) -> bool:
        if self.state == PlateState.CLEAN:
            self.state = PlateState.IN_USE
            self.assigned_order = order_id
            return True
        return False
    
    def mark_dirty(self):
        self.state = PlateState.DIRTY
        self.assigned_order = None
    
    def wash(self):
        self.state = PlateState.CLEAN
        self.assigned_order = None
    
    def is_clean(self) -> bool:
        return self.state == PlateState.CLEAN
    
    def is_dirty(self) -> bool:
        return self.state == PlateState.DIRTY
    
    def __repr__(self):
        return f"Plate({self.plate_id}, state={self.state})"
