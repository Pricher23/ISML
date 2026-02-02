from datetime import datetime
from typing import Optional
import os


class KitchenLogger:
    COLORS = {
        'RESET': '\033[0m',
        'BOLD': '\033[1m',
        'RED': '\033[91m',
        'GREEN': '\033[92m',
        'YELLOW': '\033[93m',
        'BLUE': '\033[94m',
        'MAGENTA': '\033[95m',
        'CYAN': '\033[96m',
        'WHITE': '\033[97m',
        'ORANGE': '\033[38;5;208m',
    }
    
    USE_COLORS = True
    LOG_TO_FILE = True
    LOG_FILE_PATH = "kitchen_simulation.log"
    
    LOG_ORDERS = True
    LOG_HEAD_CHEF = True
    LOG_COOKS = True
    LOG_RESOURCES = True
    LOG_MOVEMENT = False
    LOG_BDI = True
    
    _file_handle = None
    _initialized = False
    
    @classmethod
    def _init_file(cls):
        if cls._initialized:
            return
        
        if cls.LOG_TO_FILE:
            try:
                cls._file_handle = open(cls.LOG_FILE_PATH, 'w', encoding='utf-8')
                cls._file_handle.write(f"=== Kitchen Simulation Log ===\n")
                cls._file_handle.write(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                cls._file_handle.write("=" * 50 + "\n\n")
                cls._file_handle.flush()
                cls._initialized = True
            except Exception as e:
                print(f"Warning: Could not create log file: {e}")
                cls.LOG_TO_FILE = False
    
    @classmethod
    def _write_to_file(cls, message: str):
        if not cls.LOG_TO_FILE:
            return
        
        cls._init_file()
        
        if cls._file_handle:
            try:
                clean_message = message
                for color_code in cls.COLORS.values():
                    clean_message = clean_message.replace(color_code, '')
                
                cls._file_handle.write(clean_message + "\n")
                cls._file_handle.flush()
            except Exception:
                pass
    
    @classmethod
    def _log(cls, message: str, also_print: bool = True):
        if also_print:
            print(message)
        cls._write_to_file(message)
    
    @classmethod
    def close(cls):
        if cls._file_handle:
            cls._file_handle.write(f"\n=== Log ended: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
            cls._file_handle.close()
            cls._file_handle = None
            cls._initialized = False
    
    @classmethod
    def _color(cls, text: str, color: str) -> str:
        if cls.USE_COLORS and color in cls.COLORS:
            return f"{cls.COLORS[color]}{text}{cls.COLORS['RESET']}"
        return text
    
    @classmethod
    def _format_time(cls, time_step: int) -> str:
        return f"[T{time_step:04d}]"
    
    @classmethod
    def order_created(cls, time_step: int, order_id: int, recipe_name: str, time_limit: int):
        if not cls.LOG_ORDERS:
            return
        time = cls._format_time(time_step)
        msg = cls._color(f"[ORDER] NEW ORDER #{order_id}: {recipe_name} (Time limit: {time_limit} steps)", 'CYAN')
        cls._log(f"{time} {msg}")
    
    @classmethod
    def order_completed(cls, time_step: int, order_id: int, recipe_name: str, time_remaining: int):
        if not cls.LOG_ORDERS:
            return
        time = cls._format_time(time_step)
        msg = cls._color(f"[ORDER] ORDER #{order_id} COMPLETED: {recipe_name} (Time remaining: {time_remaining})", 'GREEN')
        cls._log(f"{time} {msg}")
    
    @classmethod
    def order_failed(cls, time_step: int, order_id: int, recipe_name: str):
        if not cls.LOG_ORDERS:
            return
        time = cls._format_time(time_step)
        msg = cls._color(f"[ORDER] ORDER #{order_id} FAILED: {recipe_name} - Time ran out!", 'RED')
        cls._log(f"{time} {msg}")
    
    @classmethod
    def head_chef_queued_task(cls, time_step: int, task_type: str, order_id: int):
        if not cls.LOG_HEAD_CHEF:
            return
        time = cls._format_time(time_step)
        msg = cls._color(f"[HEAD CHEF] Queued task '{task_type}' for Order #{order_id}", 'MAGENTA')
        cls._log(f"{time} {msg}")
    
    @classmethod
    def head_chef_assigning_task(cls, time_step: int, task_type: str, order_id: int, cook_id: int):
        if not cls.LOG_HEAD_CHEF:
            return
        time = cls._format_time(time_step)
        msg = cls._color(f"[HEAD CHEF] Assigning '{task_type}' (Order #{order_id}) -> Cook {cook_id}", 'MAGENTA')
        cls._log(f"{time} {msg}")
    
    @classmethod
    def head_chef_cnp_bids(cls, time_step: int, task_type: str, bids: list):
        if not cls.LOG_HEAD_CHEF:
            return
        time = cls._format_time(time_step)
        cls._log(f"{time} {cls._color('[HEAD CHEF] Evaluating bids for', 'MAGENTA')} '{task_type}':")
        for bid in bids:
            winner_mark = " ** WINNER **" if bid.get('winner') else ""
            cls._log(f"         Cook {bid['cook_id']}: distance={bid['distance']}, "
                  f"workload={bid['workload']}, score={bid['bid_score']:.2f}{winner_mark}")
    
    @classmethod
    def head_chef_dish_washing(cls, time_step: int, clean_plates: int):
        if not cls.LOG_HEAD_CHEF:
            return
        time = cls._format_time(time_step)
        msg = cls._color(f"[HEAD CHEF] Requesting dish washing! Only {clean_plates} clean plates left!", 'YELLOW')
        cls._log(f"{time} {msg}")
    
    @classmethod
    def head_chef_status(cls, time_step: int, pending_tasks: int, active_orders: int):
        if not cls.LOG_HEAD_CHEF:
            return
        time = cls._format_time(time_step)
        msg = cls._color(f"[HEAD CHEF] Monitoring - {pending_tasks} tasks pending, {active_orders} active orders", 'MAGENTA')
        cls._log(f"{time} {msg}")
    
    @classmethod
    def cook_received_task(cls, time_step: int, cook_id: int, task_type: str, order_id: int):
        if not cls.LOG_COOKS:
            return
        time = cls._format_time(time_step)
        msg = cls._color(f"[COOK {cook_id}] Received task '{task_type}' for Order #{order_id}", 'BLUE')
        cls._log(f"{time} {msg}")
    
    @classmethod
    def cook_moving_to(cls, time_step: int, cook_id: int, destination: str, position: tuple):
        if not cls.LOG_MOVEMENT:
            return
        time = cls._format_time(time_step)
        msg = cls._color(f"[COOK {cook_id}] Moving to {destination} at {position}", 'BLUE')
        cls._log(f"{time} {msg}")
    
    @classmethod
    def cook_arrived(cls, time_step: int, cook_id: int, location: str):
        if not cls.LOG_COOKS:
            return
        time = cls._format_time(time_step)
        msg = cls._color(f"[COOK {cook_id}] Arrived at {location}", 'BLUE')
        cls._log(f"{time} {msg}")
    
    @classmethod
    def cook_starting_task(cls, time_step: int, cook_id: int, task_type: str, duration: int, can_leave: bool = False):
        if not cls.LOG_COOKS:
            return
        time = cls._format_time(time_step)
        leave_msg = " (can leave unattended)" if can_leave else " (must stay)"
        msg = cls._color(f"[COOK {cook_id}] Starting '{task_type}' - {duration} steps{leave_msg}", 'BLUE')
        cls._log(f"{time} {msg}")
    
    @classmethod
    def cook_working(cls, time_step: int, cook_id: int, task_type: str, progress: int, total: int):
        if not cls.LOG_COOKS:
            return
        if progress == 1 or progress == total // 2 or progress == total:
            time = cls._format_time(time_step)
            msg = cls._color(f"[COOK {cook_id}] Working on '{task_type}' ({progress}/{total})", 'BLUE')
            cls._log(f"{time} {msg}")
    
    @classmethod
    def cook_completed_task(cls, time_step: int, cook_id: int, task_type: str, order_id: int):
        if not cls.LOG_COOKS:
            return
        time = cls._format_time(time_step)
        msg = cls._color(f"[COOK {cook_id}] COMPLETED '{task_type}' for Order #{order_id}", 'GREEN')
        cls._log(f"{time} {msg}")
    
    @classmethod
    def cook_left_cooking(cls, time_step: int, cook_id: int, task_type: str, resource_type: str):
        if not cls.LOG_COOKS:
            return
        time = cls._format_time(time_step)
        msg = cls._color(f"[COOK {cook_id}] Left '{task_type}' cooking on {resource_type}, now free", 'CYAN')
        cls._log(f"{time} {msg}")
    
    @classmethod
    def cook_waiting_resource(cls, time_step: int, cook_id: int, resource_type: str, wait_time: int):
        if not cls.LOG_COOKS:
            return
        if wait_time == 1 or wait_time % 5 == 0:
            time = cls._format_time(time_step)
            msg = cls._color(f"[COOK {cook_id}] Waiting for {resource_type} ({wait_time} steps)", 'YELLOW')
            cls._log(f"{time} {msg}")
    
    @classmethod
    def cook_idle(cls, time_step: int, cook_id: int):
        if not cls.LOG_COOKS:
            return
        time = cls._format_time(time_step)
        msg = cls._color(f"[COOK {cook_id}] Now IDLE, waiting for task", 'BLUE')
        cls._log(f"{time} {msg}")
    
    @classmethod
    def cook_retrieving_ingredients(cls, time_step: int, cook_id: int, ingredients: list):
        if not cls.LOG_COOKS:
            return
        time = cls._format_time(time_step)
        ing_str = ", ".join(ingredients) if ingredients else "ingredients"
        msg = cls._color(f"[COOK {cook_id}] Retrieving {ing_str} from storage", 'BLUE')
        cls._log(f"{time} {msg}")
    
    @classmethod
    def cook_washing_dishes(cls, time_step: int, cook_id: int):
        if not cls.LOG_COOKS:
            return
        time = cls._format_time(time_step)
        msg = cls._color(f"[COOK {cook_id}] Washing dirty dishes", 'BLUE')
        cls._log(f"{time} {msg}")
    
    @classmethod
    def resource_cooking_started(cls, time_step: int, resource_type: str, task_type: str, duration: int):
        if not cls.LOG_RESOURCES:
            return
        time = cls._format_time(time_step)
        msg = cls._color(f"[{resource_type.upper()}] Started cooking '{task_type}' - {duration} steps remaining", 'ORANGE')
        cls._log(f"{time} {msg}")
    
    @classmethod
    def resource_cooking_done(cls, time_step: int, resource_type: str, task_type: str, order_id: int):
        if not cls.LOG_RESOURCES:
            return
        time = cls._format_time(time_step)
        msg = cls._color(f"[{resource_type.upper()}] DONE '{task_type}'! (Order #{order_id})", 'GREEN')
        cls._log(f"{time} {msg}")
    
    @classmethod
    def bdi_belief_update(cls, time_step: int, cook_id: int, belief: str, value: str):
        if not cls.LOG_BDI:
            return
        time = cls._format_time(time_step)
        msg = cls._color(f"[BDI] COOK {cook_id} BELIEF: {belief} = {value}", 'CYAN')
        cls._log(f"{time} {msg}")
    
    @classmethod
    def bdi_intention_formed(cls, time_step: int, cook_id: int, goal: str, plan: list):
        if not cls.LOG_BDI:
            return
        time = cls._format_time(time_step)
        plan_str = " -> ".join(plan[:4])
        if len(plan) > 4:
            plan_str += " -> ..."
        msg = cls._color(f"[BDI] COOK {cook_id} INTENTION: {goal}", 'CYAN')
        cls._log(f"{time} {msg}")
        cls._log(f"         Plan: {plan_str}")
    
    @classmethod
    def game_win(cls, time_step: int, completed: int, failed: int):
        time = cls._format_time(time_step)
        cls._log(f"\n{time} {'='*50}")
        msg = cls._color(f"*** VICTORY! Kitchen completed {completed} orders! ***", 'GREEN')
        cls._log(f"{time} {msg}")
        cls._log(f"{time} Failed orders: {failed}")
        cls._log(f"{time} {'='*50}\n")
    
    @classmethod
    def game_lose(cls, time_step: int, completed: int, failed: int):
        time = cls._format_time(time_step)
        cls._log(f"\n{time} {'='*50}")
        msg = cls._color(f"*** GAME OVER! Too many failed orders ({failed})! ***", 'RED')
        cls._log(f"{time} {msg}")
        cls._log(f"{time} Completed orders: {completed}")
        cls._log(f"{time} {'='*50}\n")
    
    @classmethod
    def time_step_header(cls, time_step: int):
        cls._log(f"\n{'─'*60}")
        msg = cls._color(f"TIME STEP {time_step}", 'BOLD')
        cls._log(f"  {msg}")
        cls._log(f"{'─'*60}")


logger = KitchenLogger()
