import mesa
from typing import Dict, List, Optional, Tuple, Set
from model.recipes import Task
from model.orders import Order
from utils.constants import (
    AgentState, TaskState, BID_COLLECTION_WINDOW, 
    REBROADCAST_DELAY, MIN_CLEAN_PLATES_THRESHOLD, TASK_DURATIONS
)


class HeadChef(mesa.Agent):
    def __init__(self, unique_id: int, model):
        try:
            super().__init__(unique_id, model)
        except TypeError:
            super().__init__(model)
            self.unique_id = unique_id
        
        self.position: Optional[Tuple[int, int]] = None
        self.state = AgentState.IDLE
        
        self.pending_tasks: List[Task] = []
        self.task_id_counter = 0
        
        self.recently_assigned_cooks: Set[int] = set()
        self.assignment_round = 0
        
        self.dish_washing_requested = False
        
        self.target_position: Optional[Tuple[int, int]] = None
        self.path: List[Tuple[int, int]] = []
    
    def step(self):
        self.recently_assigned_cooks.clear()
        self.assignment_round += 1
        
        self._check_new_orders()
        self._distribute_tasks()
        self._monitor_plates()
        self._manage_movement()
    
    def _check_new_orders(self):
        from utils.logger import logger
        
        for order in self.model.order_manager.active_orders:
            pending_tasks = order.get_pending_subtasks()
            for task in pending_tasks:
                if task not in self.pending_tasks and task.status == TaskState.PENDING:
                    self.pending_tasks.append(task)
                    logger.head_chef_queued_task(self.model.time_steps, task.task_type, order.order_id)
    
    def _get_idle_cooks(self) -> List:
        return [cook for cook in self.model.cooks 
                if cook.current_task is None and cook.state == AgentState.IDLE]
    
    def _get_available_cooks(self) -> List:
        available = []
        for cook in self.model.cooks:
            if cook.current_task is None:
                available.append(cook)
            elif len(cook.task_queue) < 1 and cook.cook_id not in self.recently_assigned_cooks:
                available.append(cook)
        return available
    
    def _distribute_tasks(self):
        if not self.pending_tasks:
            return
        
        available_cooks = self._get_available_cooks()
        
        if not available_cooks:
            return
        
        self._sort_tasks_by_urgency()
        
        tasks_assigned = 0
        tasks_to_remove = []
        
        for task in self.pending_tasks[:]:
            if not available_cooks:
                break
            
            best_cook = self._find_best_cook_for_task(task, available_cooks)
            
            if best_cook:
                self._assign_task_to_cook(task, best_cook)
                tasks_to_remove.append(task)
                tasks_assigned += 1
                
                self.recently_assigned_cooks.add(best_cook.cook_id)
                
                if best_cook.current_task is not None or best_cook in available_cooks:
                    available_cooks = [c for c in available_cooks 
                                      if c.cook_id != best_cook.cook_id]
        
        for task in tasks_to_remove:
            if task in self.pending_tasks:
                self.pending_tasks.remove(task)
    
    def _sort_tasks_by_urgency(self):
        def get_task_urgency(task):
            if task.order_id < 0:
                return 0
            order = self.model.order_manager.get_order(task.order_id)
            if order:
                return order.time_remaining
            return 999
        
        self.pending_tasks.sort(key=get_task_urgency)
    
    def _find_best_cook_for_task(self, task: Task, available_cooks: List) -> Optional[object]:
        if not available_cooks:
            return None
        
        bids = []
        
        for cook in available_cooks:
            bid = self._calculate_bid_for_cook(cook, task)
            bids.append({
                'cook': cook,
                'cook_id': cook.cook_id,
                'bid_score': bid['score'],
                'distance': bid['distance'],
                'workload': bid['workload']
            })
        
        if not bids:
            return None
        
        from utils.logger import logger
        
        best_bid = min(bids, key=lambda b: b['bid_score'])
        
        for bid in bids:
            bid['winner'] = (bid == best_bid)
        logger.head_chef_cnp_bids(self.model.time_steps, task.task_type, bids)
        
        return best_bid['cook']
    
    def _calculate_bid_for_cook(self, cook, task: Task) -> Dict:
        from utils.pathfinding import manhattan_distance
        
        resource_type = task.resource_type
        resource_positions = self.model.get_resource_locations().get(resource_type, [])
        
        if resource_positions and cook.position:
            nearest = min(resource_positions, 
                         key=lambda p: manhattan_distance(cook.position, p))
            distance = manhattan_distance(cook.position, nearest)
        else:
            distance = 20
        
        workload = 0
        if cook.current_task is not None:
            workload += 2
        workload += len(cook.task_queue) * 2
        
        if cook.cook_id in self.recently_assigned_cooks:
            workload += 5
        
        score = (distance * 0.3) + (workload * 0.7)
        
        return {
            'score': score,
            'distance': distance,
            'workload': workload
        }
    
    def _assign_task_to_cook(self, task: Task, cook):
        from utils.logger import logger
        
        task.status = TaskState.ASSIGNED
        task.assigned_to = cook.cook_id
        
        cook.receive_task_award(task)
        
        logger.head_chef_assigning_task(self.model.time_steps, task.task_type, task.order_id, cook.cook_id)
    
    def _monitor_plates(self):
        clean_count = self.model.get_clean_plate_count()
        
        if clean_count < MIN_CLEAN_PLATES_THRESHOLD and not self.dish_washing_requested:
            dirty_plates = [p for p in self.model.plates if p.is_dirty()]
            
            if dirty_plates:
                wash_task = Task(
                    task_type='wash_dish',
                    resource_type='sink',
                    duration=TASK_DURATIONS['wash_dish'],
                    description="Wash dirty dishes"
                )
                wash_task.task_id = -1
                wash_task.order_id = -1
                
                from utils.logger import logger
                
                self.pending_tasks.insert(0, wash_task)
                self.dish_washing_requested = True
                
                logger.head_chef_dish_washing(self.model.time_steps, clean_count)
    
    def notify_dish_washing_complete(self):
        self.dish_washing_requested = False
    
    def notify_task_complete(self, task: Task, cook_id: int):
        if task.order_id >= 0:
            order = self.model.order_manager.get_order(task.order_id)
            if order:
                order.complete_subtask(task)
                
                if order.are_all_subtasks_complete():
                    self.model.order_manager.complete_order(order)
                    
                    if order.plate_id is not None:
                        plate = self.model.plates[order.plate_id]
                        plate.mark_dirty()
    
    def _manage_movement(self):
        if not self.position:
            return
        
        should_move = False
        for cook in self.model.cooks:
            if cook.target_position == self.position:
                should_move = True
                break
            if cook.path and self.position in cook.path:
                should_move = True
                break
        
        if should_move:
            from utils.pathfinding import get_neighbors
            from utils.constants import GRID_WIDTH, GRID_HEIGHT
            
            neighbors = get_neighbors(self.position, GRID_WIDTH, GRID_HEIGHT)
            blocked = self._get_blocked_positions()
            
            for neighbor in neighbors:
                if neighbor not in blocked and neighbor not in self.model.resource_positions:
                    self.model.grid.move_agent(self, neighbor)
                    self.position = neighbor
                    break
    
    def _get_blocked_positions(self) -> set:
        blocked = set()
        for cook in self.model.cooks:
            if cook.position:
                blocked.add(cook.position)
        return blocked
    
    def get_status_string(self) -> str:
        pending_count = len(self.pending_tasks)
        
        if pending_count > 0:
            return f"Distributing {pending_count} tasks"
        else:
            return "Monitoring kitchen"
