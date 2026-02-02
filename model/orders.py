from typing import List, Optional, Dict
from dataclasses import dataclass, field
from model.recipes import Recipe, Task
from utils.constants import OrderState, TaskState


@dataclass
class Order:
    order_id: int
    recipe: Recipe
    time_limit: int
    time_remaining: int
    status: str = OrderState.PENDING
    subtasks: List[Task] = field(default_factory=list)
    completed_subtasks: List[Task] = field(default_factory=list)
    plate_id: Optional[int] = None
    creation_time: int = 0
    
    def __post_init__(self):
        if not self.subtasks:
            self.subtasks = self.recipe.get_subtasks_copy()
            for i, task in enumerate(self.subtasks):
                task.order_id = self.order_id
                task.task_id = i
    
    def tick(self) -> bool:
        if self.status in [OrderState.COMPLETED, OrderState.FAILED]:
            return False
        
        self.time_remaining -= 1
        
        if self.time_remaining <= 0:
            self.status = OrderState.FAILED
            return True
        
        return False
    
    def get_pending_subtasks(self) -> List[Task]:
        return [t for t in self.subtasks if t.status == TaskState.PENDING]
    
    def get_in_progress_subtasks(self) -> List[Task]:
        return [t for t in self.subtasks if t.status == TaskState.IN_PROGRESS]
    
    def get_assigned_subtasks(self) -> List[Task]:
        return [t for t in self.subtasks if t.status == TaskState.ASSIGNED]
    
    def complete_subtask(self, task: Task):
        task.status = TaskState.COMPLETED
        if task not in self.completed_subtasks:
            self.completed_subtasks.append(task)
        
        if self.are_all_subtasks_complete():
            self.status = OrderState.COMPLETED
    
    def are_all_subtasks_complete(self) -> bool:
        return all(t.status == TaskState.COMPLETED for t in self.subtasks)
    
    def get_completion_percentage(self) -> float:
        if not self.subtasks:
            return 0.0
        completed = sum(1 for t in self.subtasks if t.status == TaskState.COMPLETED)
        return (completed / len(self.subtasks)) * 100
    
    def assign_plate(self, plate_id: int):
        self.plate_id = plate_id
    
    def needs_plate(self) -> bool:
        plating_tasks = [t for t in self.subtasks if t.task_type == 'plate']
        if not plating_tasks:
            return False
        
        for task in plating_tasks:
            if task.status in [TaskState.PENDING, TaskState.ASSIGNED, TaskState.IN_PROGRESS]:
                return self.plate_id is None
        
        return False
    
    def get_next_available_task(self) -> Optional[Task]:
        pending = self.get_pending_subtasks()
        if pending:
            return pending[0]
        return None
    
    def __repr__(self):
        return f"Order({self.order_id}, {self.recipe.name}, {self.time_remaining}/{self.time_limit}, {self.status})"


class OrderManager:
    def __init__(self):
        self.orders: Dict[int, Order] = {}
        self.active_orders: List[Order] = []
        self.completed_orders: List[Order] = []
        self.failed_orders: List[Order] = []
        self.order_id_counter = 0
    
    def create_order(self, recipe: Recipe, current_time: int) -> Order:
        order = Order(
            order_id=self.order_id_counter,
            recipe=recipe,
            time_limit=recipe.time_limit,
            time_remaining=recipe.time_limit,
            creation_time=current_time
        )
        
        self.orders[order.order_id] = order
        self.active_orders.append(order)
        self.order_id_counter += 1
        
        from utils.logger import logger
        logger.order_created(current_time, order.order_id, recipe.name, recipe.time_limit)
        
        return order
    
    def tick_all_orders(self) -> List[Order]:
        failed_this_tick = []
        
        from utils.logger import logger
        
        for order in self.active_orders[:]:
            if order.tick():
                failed_this_tick.append(order)
                self.active_orders.remove(order)
                self.failed_orders.append(order)
                logger.order_failed(0, order.order_id, order.recipe.name)
        
        return failed_this_tick
    
    def complete_order(self, order: Order):
        from utils.logger import logger
        
        order.status = OrderState.COMPLETED
        if order in self.active_orders:
            self.active_orders.remove(order)
        if order not in self.completed_orders:
            self.completed_orders.append(order)
        
        logger.order_completed(0, order.order_id, order.recipe.name, order.time_remaining)
    
    def get_order(self, order_id: int) -> Optional[Order]:
        return self.orders.get(order_id)
    
    def get_all_pending_tasks(self) -> List[Task]:
        tasks = []
        for order in self.active_orders:
            tasks.extend(order.get_pending_subtasks())
        return tasks
    
    def get_completed_count(self) -> int:
        return len(self.completed_orders)
    
    def get_failed_count(self) -> int:
        return len(self.failed_orders)
    
    def get_active_count(self) -> int:
        return len(self.active_orders)
