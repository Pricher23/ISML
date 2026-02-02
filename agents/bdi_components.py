from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field
from model.recipes import Task


@dataclass
class CookBeliefs:
    position: Tuple[int, int] = (0, 0)
    inventory: List[str] = field(default_factory=list)
    current_task: Optional[Task] = None
    
    resource_locations: Dict[str, List[Tuple[int, int]]] = field(default_factory=dict)
    resource_states: Dict[Tuple[int, int], str] = field(default_factory=dict)
    resource_queues: Dict[Tuple[int, int], int] = field(default_factory=dict)
    
    other_agent_positions: List[Tuple[int, int]] = field(default_factory=list)
    head_chef_position: Optional[Tuple[int, int]] = None
    
    clean_plate_count: int = 8
    
    known_paths: Dict[Tuple[Tuple[int, int], Tuple[int, int]], List[Tuple[int, int]]] = field(default_factory=dict)
    
    assigned_task: Optional[Task] = None
    target_resource: Optional[Tuple[int, int]] = None
    
    def update_position(self, new_position: Tuple[int, int]):
        self.position = new_position
    
    def update_resource_state(self, position: Tuple[int, int], state: str):
        self.resource_states[position] = state
    
    def update_other_agents(self, positions: List[Tuple[int, int]]):
        self.other_agent_positions = positions
    
    def add_to_inventory(self, ingredients: List[str]):
        self.inventory.extend(ingredients)
    
    def clear_inventory(self):
        self.inventory = []
    
    def get_nearest_resource(self, resource_type: str) -> Optional[Tuple[int, int]]:
        if resource_type not in self.resource_locations:
            return None
        
        locations = self.resource_locations[resource_type]
        if not locations:
            return None
        
        def distance(pos):
            return abs(pos[0] - self.position[0]) + abs(pos[1] - self.position[1])
        
        return min(locations, key=distance)
    
    def get_free_resources(self, resource_type: str) -> List[Tuple[int, int]]:
        if resource_type not in self.resource_locations:
            return []
        
        return [
            pos for pos in self.resource_locations[resource_type]
            if self.resource_states.get(pos, 'free') == 'free'
        ]
    
    def __repr__(self):
        return f"Beliefs(pos={self.position}, inventory={self.inventory}, task={self.current_task})"


@dataclass
class CookDesires:
    complete_assigned_task: bool = True
    minimize_idle_time: bool = True
    avoid_collisions: bool = True
    access_required_resource: bool = False
    acquire_ingredients: bool = False
    wash_dishes: bool = False
    
    priority_weights: Dict[str, float] = field(default_factory=lambda: {
        'complete_assigned_task': 1.0,
        'wash_dishes': 0.9,
        'acquire_ingredients': 0.8,
        'access_required_resource': 0.7,
        'minimize_idle_time': 0.5,
        'avoid_collisions': 0.3
    })
    
    def activate_desire(self, desire_name: str):
        if hasattr(self, desire_name):
            setattr(self, desire_name, True)
    
    def deactivate_desire(self, desire_name: str):
        if hasattr(self, desire_name):
            setattr(self, desire_name, False)
    
    def get_active_desires(self) -> List[str]:
        desires = ['complete_assigned_task', 'minimize_idle_time', 'avoid_collisions',
                   'access_required_resource', 'acquire_ingredients', 'wash_dishes']
        return [d for d in desires if getattr(self, d, False)]
    
    def get_highest_priority_desire(self) -> Optional[str]:
        active = self.get_active_desires()
        if not active:
            return None
        return max(active, key=lambda d: self.priority_weights.get(d, 0))


@dataclass
class CookIntention:
    goal: str
    plan: List[str] = field(default_factory=list)
    committed: bool = False
    current_action_index: int = 0
    task: Optional[Task] = None
    target_position: Optional[Tuple[int, int]] = None
    started: bool = False
    
    def commit(self):
        self.committed = True
        self.started = True
    
    def abandon(self):
        self.committed = False
    
    def get_current_action(self) -> Optional[str]:
        if self.current_action_index < len(self.plan):
            return self.plan[self.current_action_index]
        return None
    
    def advance_plan(self) -> bool:
        self.current_action_index += 1
        return self.current_action_index >= len(self.plan)
    
    def is_complete(self) -> bool:
        return self.current_action_index >= len(self.plan)
    
    def reset(self):
        self.current_action_index = 0
        self.committed = False
        self.started = False
    
    @staticmethod
    def create_task_intention(task: Task, needs_ingredients: bool = True) -> 'CookIntention':
        plan = []
        
        if task.task_type == 'retrieve_ingredients':
            plan = [
                'move_to_storage',
                'wait_for_storage',
                'retrieve_ingredients',
                'report_completion'
            ]
        elif task.task_type == 'wash_dish':
            plan = [
                'move_to_sink',
                'wait_for_sink',
                'execute_wash_dish',
                'report_completion'
            ]
        else:
            resource = task.resource_type
            plan = [
                f'move_to_{resource}',
                f'wait_for_{resource}',
                f'execute_{task.task_type}',
                'report_completion'
            ]
        
        return CookIntention(
            goal=f'complete_{task.task_type}_task',
            plan=plan,
            task=task
        )
    
    @staticmethod
    def create_idle_intention() -> 'CookIntention':
        return CookIntention(
            goal='idle',
            plan=['wait_for_task'],
            committed=True
        )
    
    def __repr__(self):
        current = self.get_current_action() or "none"
        return f"Intention(goal={self.goal}, action={current}, {self.current_action_index}/{len(self.plan)})"


class BDIReasoner:
    def __init__(self, beliefs: CookBeliefs, desires: CookDesires):
        self.beliefs = beliefs
        self.desires = desires
        self.intention: Optional[CookIntention] = None
    
    def update_beliefs(self, perception: Dict):
        if 'position' in perception:
            self.beliefs.update_position(perception['position'])
        
        if 'resource_states' in perception:
            for pos, state in perception['resource_states'].items():
                self.beliefs.update_resource_state(pos, state)
        
        if 'other_agents' in perception:
            self.beliefs.update_other_agents(perception['other_agents'])
        
        if 'clean_plates' in perception:
            self.beliefs.clean_plate_count = perception['clean_plates']
        
        if 'inventory' in perception:
            self.beliefs.inventory = perception['inventory']
    
    def generate_options(self) -> List[CookIntention]:
        options = []
        
        if self.beliefs.assigned_task:
            task = self.beliefs.assigned_task
            intention = CookIntention.create_task_intention(task)
            options.append(intention)
        
        if self.beliefs.clean_plate_count < 2 and not self.beliefs.assigned_task:
            pass
        
        if not options:
            options.append(CookIntention.create_idle_intention())
        
        return options
    
    def filter_options(self, options: List[CookIntention]) -> List[CookIntention]:
        feasible = []
        
        for option in options:
            if option.goal == 'idle':
                feasible.append(option)
            elif option.task:
                resource_type = option.task.resource_type
                if resource_type in self.beliefs.resource_locations:
                    feasible.append(option)
                else:
                    feasible.append(option)
        
        return feasible if feasible else options
    
    def select_intention(self, options: List[CookIntention]) -> CookIntention:
        if not options:
            return CookIntention.create_idle_intention()
        
        for option in options:
            if option.goal != 'idle':
                return option
        
        return options[0]
    
    def should_reconsider(self) -> bool:
        if not self.intention:
            return True
        
        if not self.intention.committed:
            return True
        
        if self.intention.task and self.beliefs.assigned_task != self.intention.task:
            return True
        
        return False
    
    def deliberate(self) -> CookIntention:
        if self.should_reconsider():
            options = self.generate_options()
            feasible = self.filter_options(options)
            self.intention = self.select_intention(feasible)
            self.intention.commit()
        
        return self.intention
