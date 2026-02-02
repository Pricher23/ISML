from typing import List, Dict, Optional
from dataclasses import dataclass, field
from utils.constants import TASK_DURATIONS, TaskState


@dataclass
class Task:
    task_type: str
    resource_type: str
    duration: int
    ingredients: List[str] = field(default_factory=list)
    description: str = ""
    
    task_id: Optional[int] = None
    order_id: Optional[int] = None
    status: str = TaskState.PENDING
    assigned_to: Optional[int] = None
    progress: int = 0
    
    def copy(self) -> 'Task':
        return Task(
            task_type=self.task_type,
            resource_type=self.resource_type,
            duration=self.duration,
            ingredients=self.ingredients.copy(),
            description=self.description,
            task_id=None,
            order_id=None,
            status=TaskState.PENDING,
            assigned_to=None,
            progress=0
        )
    
    def is_complete(self) -> bool:
        return self.progress >= self.duration
    
    def work(self) -> bool:
        self.progress += 1
        if self.progress >= self.duration:
            self.status = TaskState.COMPLETED
            return True
        return False
    
    def __repr__(self):
        return f"Task({self.task_type} at {self.resource_type}, {self.progress}/{self.duration})"


@dataclass
class Recipe:
    name: str
    subtasks: List[Task]
    ingredients: List[str]
    complexity: int
    time_limit: int
    
    def get_subtasks_copy(self) -> List[Task]:
        return [task.copy() for task in self.subtasks]
    
    def __repr__(self):
        return f"Recipe({self.name}, {self.complexity} tasks, {self.time_limit} time limit)"


RECIPES: Dict[str, Recipe] = {}

RECIPES['burger'] = Recipe(
    name="Burger Meal",
    subtasks=[
        Task(
            task_type='retrieve_ingredients',
            resource_type='storage',
            duration=TASK_DURATIONS['retrieve_ingredients'],
            ingredients=['bun', 'patty', 'lettuce', 'tomato'],
            description="Get burger ingredients from storage"
        ),
        Task(
            task_type='chop',
            resource_type='cutting_board',
            duration=TASK_DURATIONS['chop'],
            ingredients=[],
            description="Chop vegetables (lettuce, tomato)"
        ),
        Task(
            task_type='grill',
            resource_type='stove',
            duration=TASK_DURATIONS['grill'],
            ingredients=[],
            description="Grill the patty"
        ),
        Task(
            task_type='assemble',
            resource_type='counter',
            duration=TASK_DURATIONS['assemble'],
            ingredients=[],
            description="Assemble the burger"
        ),
        Task(
            task_type='plate',
            resource_type='counter',
            duration=TASK_DURATIONS['plate'],
            ingredients=[],
            description="Plate the burger meal"
        ),
    ],
    ingredients=['bun', 'patty', 'lettuce', 'tomato'],
    complexity=5,
    time_limit=50
)

RECIPES['pasta'] = Recipe(
    name="Pasta Dish",
    subtasks=[
        Task(
            task_type='retrieve_ingredients',
            resource_type='storage',
            duration=TASK_DURATIONS['retrieve_ingredients'],
            ingredients=['pasta', 'sauce', 'bell_pepper', 'onion'],
            description="Get pasta ingredients from storage"
        ),
        Task(
            task_type='chop',
            resource_type='cutting_board',
            duration=TASK_DURATIONS['chop'],
            ingredients=[],
            description="Chop vegetables"
        ),
        Task(
            task_type='cook',
            resource_type='stove',
            duration=TASK_DURATIONS['cook'],
            ingredients=[],
            description="Cook pasta"
        ),
        Task(
            task_type='saute',
            resource_type='stove',
            duration=TASK_DURATIONS['saute'],
            ingredients=[],
            description="Saute vegetables"
        ),
        Task(
            task_type='assemble',
            resource_type='counter',
            duration=TASK_DURATIONS['assemble'],
            ingredients=[],
            description="Assemble the dish"
        ),
        Task(
            task_type='plate',
            resource_type='counter',
            duration=TASK_DURATIONS['plate'],
            ingredients=[],
            description="Plate the pasta dish"
        ),
    ],
    ingredients=['pasta', 'sauce', 'bell_pepper', 'onion'],
    complexity=6,
    time_limit=60
)

RECIPES['pizza'] = Recipe(
    name="Pizza",
    subtasks=[
        Task(
            task_type='retrieve_ingredients',
            resource_type='storage',
            duration=TASK_DURATIONS['retrieve_ingredients'],
            ingredients=['dough', 'cheese', 'sauce', 'pepperoni', 'mushrooms'],
            description="Get pizza ingredients from storage"
        ),
        Task(
            task_type='chop',
            resource_type='cutting_board',
            duration=TASK_DURATIONS['chop'],
            ingredients=[],
            description="Chop toppings"
        ),
        Task(
            task_type='prepare',
            resource_type='counter',
            duration=TASK_DURATIONS['prepare'],
            ingredients=[],
            description="Prepare pizza"
        ),
        Task(
            task_type='bake',
            resource_type='oven',
            duration=TASK_DURATIONS['bake'],
            ingredients=[],
            description="Bake pizza in oven"
        ),
        Task(
            task_type='plate',
            resource_type='counter',
            duration=TASK_DURATIONS['plate'],
            ingredients=[],
            description="Plate the pizza"
        ),
    ],
    ingredients=['dough', 'cheese', 'sauce', 'pepperoni', 'mushrooms'],
    complexity=5,
    time_limit=55
)

RECIPES['salad'] = Recipe(
    name="Salad",
    subtasks=[
        Task(
            task_type='retrieve_ingredients',
            resource_type='storage',
            duration=TASK_DURATIONS['retrieve_ingredients'],
            ingredients=['lettuce', 'tomato', 'cucumber', 'dressing'],
            description="Get salad ingredients from storage"
        ),
        Task(
            task_type='chop',
            resource_type='cutting_board',
            duration=TASK_DURATIONS['chop'],
            ingredients=[],
            description="Chop vegetables"
        ),
        Task(
            task_type='chop',
            resource_type='cutting_board',
            duration=TASK_DURATIONS['chop'],
            ingredients=[],
            description="Chop more vegetables"
        ),
        Task(
            task_type='assemble',
            resource_type='counter',
            duration=TASK_DURATIONS['assemble'],
            ingredients=[],
            description="Assemble salad"
        ),
        Task(
            task_type='plate',
            resource_type='counter',
            duration=TASK_DURATIONS['plate'],
            ingredients=[],
            description="Plate the salad"
        ),
    ],
    ingredients=['lettuce', 'tomato', 'cucumber', 'dressing'],
    complexity=5,
    time_limit=45
)

RECIPES['grilled_chicken'] = Recipe(
    name="Grilled Chicken Plate",
    subtasks=[
        Task(
            task_type='retrieve_ingredients',
            resource_type='storage',
            duration=TASK_DURATIONS['retrieve_ingredients'],
            ingredients=['chicken_breast', 'broccoli', 'carrots', 'rice'],
            description="Get chicken ingredients from storage"
        ),
        Task(
            task_type='chop',
            resource_type='cutting_board',
            duration=TASK_DURATIONS['chop'],
            ingredients=[],
            description="Chop vegetables"
        ),
        Task(
            task_type='grill',
            resource_type='stove',
            duration=TASK_DURATIONS['grill'],
            ingredients=[],
            description="Grill chicken"
        ),
        Task(
            task_type='cook_rice',
            resource_type='stove',
            duration=TASK_DURATIONS['cook_rice'],
            ingredients=[],
            description="Cook rice"
        ),
        Task(
            task_type='saute',
            resource_type='stove',
            duration=TASK_DURATIONS['saute'],
            ingredients=[],
            description="Saute vegetables"
        ),
        Task(
            task_type='assemble',
            resource_type='counter',
            duration=TASK_DURATIONS['assemble'],
            ingredients=[],
            description="Assemble plate"
        ),
        Task(
            task_type='plate',
            resource_type='counter',
            duration=TASK_DURATIONS['plate'],
            ingredients=[],
            description="Plate the dish"
        ),
    ],
    ingredients=['chicken_breast', 'broccoli', 'carrots', 'rice'],
    complexity=7,
    time_limit=70
)

RECIPES['casserole'] = Recipe(
    name="Baked Casserole",
    subtasks=[
        Task(
            task_type='retrieve_ingredients',
            resource_type='storage',
            duration=TASK_DURATIONS['retrieve_ingredients'],
            ingredients=['pasta', 'cheese', 'spinach', 'mushrooms', 'cream_sauce'],
            description="Get casserole ingredients from storage"
        ),
        Task(
            task_type='chop',
            resource_type='cutting_board',
            duration=TASK_DURATIONS['chop'],
            ingredients=[],
            description="Chop vegetables"
        ),
        Task(
            task_type='cook',
            resource_type='stove',
            duration=TASK_DURATIONS['cook'],
            ingredients=[],
            description="Cook pasta"
        ),
        Task(
            task_type='prepare',
            resource_type='counter',
            duration=TASK_DURATIONS['prepare'],
            ingredients=[],
            description="Prepare casserole"
        ),
        Task(
            task_type='bake',
            resource_type='oven',
            duration=TASK_DURATIONS['bake'],
            ingredients=[],
            description="Bake casserole in oven"
        ),
        Task(
            task_type='plate',
            resource_type='counter',
            duration=TASK_DURATIONS['plate'],
            ingredients=[],
            description="Plate the casserole"
        ),
    ],
    ingredients=['pasta', 'cheese', 'spinach', 'mushrooms', 'cream_sauce'],
    complexity=6,
    time_limit=65
)


def get_recipe(recipe_name: str) -> Optional[Recipe]:
    return RECIPES.get(recipe_name)


def get_all_recipe_names() -> List[str]:
    return list(RECIPES.keys())


def get_random_recipe() -> Recipe:
    import random
    return random.choice(list(RECIPES.values()))
