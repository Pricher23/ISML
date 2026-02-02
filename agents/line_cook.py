import mesa
from typing import Dict, List, Optional, Tuple, Set
from model.recipes import Task
from agents.bdi_components import CookBeliefs, CookDesires, CookIntention, BDIReasoner
from utils.constants import (
    AgentState, TaskState, MOVEMENT_SPEED, 
    MAX_RESOURCE_WAIT, MAX_PATH_WAIT, GRID_WIDTH, GRID_HEIGHT
)
from utils.pathfinding import astar_pathfinding, find_adjacent_position, manhattan_distance


class LineCook(mesa.Agent):
    def __init__(self, unique_id: int, model, cook_id: int):
        try:
            super().__init__(unique_id, model)
        except TypeError:
            super().__init__(model)
            self.unique_id = unique_id
        self.cook_id = cook_id
        self.position: Optional[Tuple[int, int]] = None
        self.state = AgentState.IDLE
        
        self.beliefs = CookBeliefs()
        self.desires = CookDesires()
        self.intention: Optional[CookIntention] = None
        self.reasoner = BDIReasoner(self.beliefs, self.desires)
        
        self.current_task: Optional[Task] = None
        self.task_queue: List[Task] = []
        self.inventory: List[str] = []
        
        self.target_position: Optional[Tuple[int, int]] = None
        self.path: List[Tuple[int, int]] = []
        
        self.task_timer: int = 0
        self.wait_timer: int = 0
        self.path_wait_timer: int = 0
        
        self.current_resource: Optional[Tuple[int, int]] = None
    
    def step(self):
        self._update_beliefs()
        
        if self.current_task:
            self._execute_current_task()
        else:
            self.state = AgentState.IDLE
            if self.task_queue:
                next_task = self.task_queue.pop(0)
                self.current_task = next_task
                next_task.status = TaskState.IN_PROGRESS
                self._form_intention(next_task)
                self.state = AgentState.MOVING
                from utils.logger import logger
                logger.cook_received_task(self.model.time_steps, self.cook_id, 
                                         next_task.task_type, next_task.order_id)
    
    def _update_beliefs(self):
        self.beliefs.position = self.position
        self.beliefs.resource_locations = self.model.get_resource_locations()
        
        for pos, resource in self.model.resources.items():
            self.beliefs.resource_states[pos] = 'occupied' if resource.occupied else 'free'
        
        other_positions = []
        for cook in self.model.cooks:
            if cook.unique_id != self.unique_id and cook.position:
                other_positions.append(cook.position)
        if self.model.head_chef.position:
            other_positions.append(self.model.head_chef.position)
        self.beliefs.other_agent_positions = other_positions
        
        self.beliefs.clean_plate_count = self.model.get_clean_plate_count()
        self.beliefs.inventory = self.inventory.copy()
        self.beliefs.current_task = self.current_task
        self.beliefs.assigned_task = self.current_task
    
    def receive_task_announcement(self, announcement: Dict):
        pass
    
    def receive_task_award(self, task: Task):
        from utils.logger import logger
        logger.cook_received_task(self.model.time_steps, self.cook_id, task.task_type, task.order_id)
        
        self._form_intention(task)
        
        if self.current_task is None:
            self.current_task = task
            task.status = TaskState.IN_PROGRESS
            self.state = AgentState.MOVING
        else:
            self.task_queue.append(task)
    
    def _form_intention(self, task: Task):
        self.intention = CookIntention.create_task_intention(task)
        self.intention.commit()
        
        self.beliefs.assigned_task = task
        self.desires.complete_assigned_task = True
        
        from utils.logger import logger
        logger.bdi_intention_formed(self.model.time_steps, self.cook_id, 
                                   self.intention.goal, self.intention.plan)
    
    def _execute_current_task(self):
        if not self.intention:
            self._form_intention(self.current_task)
        
        current_action = self.intention.get_current_action()
        
        if current_action is None:
            self._complete_task()
            return
        
        if current_action.startswith('move_to_'):
            resource_type = current_action.replace('move_to_', '')
            self._action_move_to(resource_type)
        
        elif current_action.startswith('wait_for_'):
            resource_type = current_action.replace('wait_for_', '')
            self._action_wait_for(resource_type)
        
        elif current_action.startswith('execute_'):
            task_type = current_action.replace('execute_', '')
            self._action_execute(task_type)
        
        elif current_action == 'retrieve_ingredients':
            self._action_retrieve_ingredients()
        
        elif current_action == 'report_completion':
            self._action_report_completion()
        
        elif current_action == 'wait_for_task':
            self.state = AgentState.IDLE
    
    def _action_move_to(self, resource_type: str):
        self.state = AgentState.MOVING
        
        if self.target_position is None or not self.path:
            resource_positions = self.beliefs.resource_locations.get(resource_type, [])
            
            if not resource_positions:
                return
            
            free_resources = [p for p in resource_positions 
                           if self.beliefs.resource_states.get(p, 'free') == 'free']
            
            if free_resources:
                target = min(free_resources, 
                           key=lambda p: manhattan_distance(self.position, p))
            else:
                target = min(resource_positions,
                           key=lambda p: manhattan_distance(self.position, p))
            
            self.current_resource = target
            
            if resource_type == 'storage':
                self.target_position = target
            else:
                adjacent = find_adjacent_position(
                    target, GRID_WIDTH, GRID_HEIGHT,
                    self._get_blocked_positions(),
                    self._get_non_walkable_resources()
                )
                
                if adjacent:
                    self.target_position = adjacent
                else:
                    self.target_position = target
            
            non_walkable = self._get_non_walkable_resources()
            
            self.path = astar_pathfinding(
                self.position, self.target_position,
                GRID_WIDTH, GRID_HEIGHT,
                self._get_blocked_positions(),
                non_walkable
            ) or []
            
            if self.path and self.path[0] == self.position:
                self.path.pop(0)
        
        if self.path:
            self._execute_movement()
        
        arrived = False
        if self.position == self.target_position:
            arrived = True
        elif self.current_resource and manhattan_distance(self.position, self.current_resource) <= 1:
            if resource_type != 'storage':
                arrived = True
        
        if arrived:
            from utils.logger import logger
            logger.cook_arrived(self.model.time_steps, self.cook_id, resource_type)
            self.intention.advance_plan()
            self.path = []
            self.path_wait_timer = 0
    
    def _get_non_walkable_resources(self) -> Set[Tuple[int, int]]:
        non_walkable = set()
        for pos, resource in self.model.resources.items():
            if resource.type != 'storage':
                non_walkable.add(pos)
        return non_walkable
    
    def _action_wait_for(self, resource_type: str):
        if resource_type == 'storage':
            self.state = AgentState.WORKING
            self.wait_timer = 0
            from utils.logger import logger
            logger.cook_arrived(self.model.time_steps, self.cook_id, 'storage')
            self.intention.advance_plan()
            return
        
        if not self.current_resource:
            resource_positions = self.beliefs.resource_locations.get(resource_type, [])
            if resource_positions:
                self.current_resource = min(resource_positions,
                                          key=lambda p: manhattan_distance(self.position, p))
        
        if not self.current_resource:
            self.intention.advance_plan()
            return
        
        resource = self.model.resources.get(self.current_resource)
        
        if resource and not resource.occupied:
            if resource.occupy(self.cook_id):
                self.state = AgentState.WORKING
                self.wait_timer = 0
                self.intention.advance_plan()
            else:
                self.state = AgentState.WAITING_RESOURCE
                resource.add_to_queue(self.cook_id)
        else:
            self.state = AgentState.WAITING_RESOURCE
            self.wait_timer += 1
            
            if resource:
                resource.add_to_queue(self.cook_id)
                queue_pos = resource.get_queue_position(self.cook_id)
                from utils.logger import logger
                logger.cook_waiting_resource(self.model.time_steps, self.cook_id, 
                                            resource_type, self.wait_timer)
            
            if self.wait_timer > MAX_RESOURCE_WAIT:
                self._request_reassignment()
    
    def _action_execute(self, task_type: str):
        from model.resources import Resource
        
        self.state = AgentState.WORKING
        resource = self.model.resources.get(self.current_resource) if self.current_resource else None
        
        if Resource.is_unattended_task(task_type):
            if resource and not resource.is_cooking():
                from utils.logger import logger
                logger.cook_starting_task(self.model.time_steps, self.cook_id, task_type,
                                         self.current_task.duration, can_leave=True)
                logger.resource_cooking_started(self.model.time_steps, resource.type,
                                               task_type, self.current_task.duration)
                
                resource.start_cooking(
                    task=self.current_task,
                    cook_id=self.cook_id,
                    duration=self.current_task.duration
                )
                
                self.task_timer = 0
                self.current_resource = None
                self.target_position = None
                
                self.intention.advance_plan()
                
                if self.intention.get_current_action() == 'report_completion':
                    self.intention.advance_plan()
                
                self._complete_task_without_reporting()
            return
        
        if self.task_timer == 0:
            self.task_timer = self.current_task.duration
            from utils.logger import logger
            logger.cook_starting_task(self.model.time_steps, self.cook_id, task_type,
                                     self.task_timer, can_leave=False)
        
        self.task_timer -= 1
        self.current_task.progress += 1
        
        if self.task_timer <= 0 or self.current_task.is_complete():
            from utils.logger import logger
            logger.cook_completed_task(self.model.time_steps, self.cook_id, task_type,
                                      self.current_task.order_id)
            
            if resource:
                resource.release()
                resource.remove_from_queue(self.cook_id)
            
            self.task_timer = 0
            self.current_resource = None
            self.target_position = None
            self.intention.advance_plan()
    
    def _action_retrieve_ingredients(self):
        self.state = AgentState.WORKING
        
        if self.task_timer == 0:
            self.task_timer = self.current_task.duration
            from utils.logger import logger
            logger.cook_retrieving_ingredients(self.model.time_steps, self.cook_id,
                                              self.current_task.ingredients)
        
        self.task_timer -= 1
        self.current_task.progress += 1
        
        if self.task_timer <= 0 or self.current_task.is_complete():
            self.inventory.extend(self.current_task.ingredients)
            
            self.task_timer = 0
            self.current_resource = None
            self.target_position = None
            self.intention.advance_plan()
    
    def _action_report_completion(self):
        from utils.logger import logger
        
        if self.current_task.task_type == 'wash_dish':
            for plate in self.model.plates:
                if plate.is_dirty():
                    plate.wash()
                    logger.cook_washing_dishes(self.model.time_steps, self.cook_id)
                    break
            self.model.head_chef.notify_dish_washing_complete()
        else:
            self.model.head_chef.notify_task_complete(self.current_task, self.cook_id)
        
        self._complete_task()
    
    def _complete_task(self):
        if self.current_task:
            self.current_task.status = TaskState.COMPLETED
        
        if self.current_task and self.current_task.task_type == 'plate':
            self.inventory = []
        
        self.current_task = None
        self.intention = None
        self.target_position = None
        self.path = []
        self.task_timer = 0
        self.wait_timer = 0
        
        if self.task_queue:
            next_task = self.task_queue.pop(0)
            self.current_task = next_task
            next_task.status = TaskState.IN_PROGRESS
            self._form_intention(next_task)
            self.state = AgentState.MOVING
            from utils.logger import logger
            logger.cook_received_task(self.model.time_steps, self.cook_id,
                                     next_task.task_type, next_task.order_id)
        else:
            self.state = AgentState.IDLE
            from utils.logger import logger
            logger.cook_idle(self.model.time_steps, self.cook_id)
    
    def _complete_task_without_reporting(self):
        self.current_task = None
        self.intention = None
        self.target_position = None
        self.path = []
        self.task_timer = 0
        self.wait_timer = 0
        
        from utils.logger import logger
        logger.cook_left_cooking(self.model.time_steps, self.cook_id, 
                                self.current_task.task_type if self.current_task else 'cooking',
                                'stove/oven')
        
        if self.task_queue:
            next_task = self.task_queue.pop(0)
            self.current_task = next_task
            next_task.status = TaskState.IN_PROGRESS
            self._form_intention(next_task)
            self.state = AgentState.MOVING
            from utils.logger import logger
            logger.cook_received_task(self.model.time_steps, self.cook_id,
                                     next_task.task_type, next_task.order_id)
        else:
            self.state = AgentState.IDLE
            from utils.logger import logger
            logger.cook_idle(self.model.time_steps, self.cook_id)
    
    def _execute_movement(self):
        if not self.path:
            return
        
        moves_remaining = MOVEMENT_SPEED
        
        while moves_remaining > 0 and self.path:
            next_pos = self.path[0]
            
            if next_pos in self._get_blocked_positions():
                self.path_wait_timer += 1
                self.state = AgentState.WAITING_PATH
                
                if self.path_wait_timer > MAX_PATH_WAIT:
                    non_walkable = self._get_non_walkable_resources()
                    self.path = astar_pathfinding(
                        self.position, self.target_position,
                        GRID_WIDTH, GRID_HEIGHT,
                        self._get_blocked_positions(),
                        non_walkable
                    ) or []
                    self.path_wait_timer = 0
                    
                    if self.path and self.path[0] == self.position:
                        self.path.pop(0)
                
                return
            
            if next_pos in self._get_non_walkable_resources() and next_pos != self.target_position:
                non_walkable = self._get_non_walkable_resources()
                self.path = astar_pathfinding(
                    self.position, self.target_position,
                    GRID_WIDTH, GRID_HEIGHT,
                    self._get_blocked_positions(),
                    non_walkable
                ) or []
                
                if self.path and self.path[0] == self.position:
                    self.path.pop(0)
                return
            
            self.model.grid.move_agent(self, next_pos)
            self.position = next_pos
            self.path.pop(0)
            self.path_wait_timer = 0
            moves_remaining -= 1
    
    def _get_blocked_positions(self) -> Set[Tuple[int, int]]:
        blocked = set()
        for cook in self.model.cooks:
            if cook.unique_id != self.unique_id and cook.position:
                blocked.add(cook.position)
        if self.model.head_chef.position:
            blocked.add(self.model.head_chef.position)
        return blocked
    
    def _look_for_work(self):
        pass
    
    def _request_reassignment(self):
        self.wait_timer = 0
    
    def get_status_string(self) -> str:
        if self.state == AgentState.IDLE:
            return "Idle"
        elif self.state == AgentState.MOVING:
            if self.current_task:
                return f"Moving to {self.current_task.resource_type}"
            return "Moving"
        elif self.state == AgentState.WORKING:
            if self.current_task:
                return f"{self.current_task.task_type} [{self.current_task.progress}/{self.current_task.duration}]"
            return "Working"
        elif self.state == AgentState.WAITING_RESOURCE:
            return f"Waiting for resource ({self.wait_timer} steps)"
        elif self.state == AgentState.WAITING_PATH:
            return "Waiting for path"
        return self.state
