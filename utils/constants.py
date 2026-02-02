GRID_WIDTH = 12
GRID_HEIGHT = 10

TASK_DURATIONS = {
    'retrieve_ingredients': 3,
    'chop': 5,
    'grill': 10,
    'cook': 10,
    'saute': 10,
    'bake': 15,
    'prepare': 7,
    'assemble': 5,
    'plate': 5,
    'wash_dish': 5,
    'cook_rice': 8
}

MOVEMENT_SPEED = 2

ORDER_INTERVAL_MIN = 15
ORDER_INTERVAL_MAX = 25

WIN_THRESHOLD = 10
LOSE_THRESHOLD = 3

TOTAL_PLATES = 8
MIN_CLEAN_PLATES_THRESHOLD = 2

BID_COLLECTION_WINDOW = 2
REBROADCAST_DELAY = 5

MAX_RESOURCE_WAIT = 20
MAX_PATH_WAIT = 5

RESOURCE_TYPES = {
    'storage': 'STORAGE',
    'stove': 'STOVE',
    'oven': 'OVEN',
    'cutting_board': 'CUTTING',
    'counter': 'COUNTER',
    'sink': 'SINK'
}


class AgentState:
    IDLE = "idle"
    MOVING = "moving"
    WORKING = "working"
    WAITING_RESOURCE = "waiting_resource"
    WAITING_PATH = "waiting_path"
    BIDDING = "bidding"


class OrderState:
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class PlateState:
    CLEAN = "clean"
    IN_USE = "in_use"
    DIRTY = "dirty"


class TaskState:
    PENDING = "pending"
    BROADCAST = "broadcast"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
