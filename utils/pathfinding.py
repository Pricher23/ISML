import heapq
from typing import List, Tuple, Set, Optional


def manhattan_distance(pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])


def get_neighbors(pos: Tuple[int, int], grid_width: int, grid_height: int) -> List[Tuple[int, int]]:
    x, y = pos
    neighbors = []
    
    for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
        nx, ny = x + dx, y + dy
        if 0 <= nx < grid_width and 0 <= ny < grid_height:
            neighbors.append((nx, ny))
    
    return neighbors


def astar_pathfinding(
    start: Tuple[int, int],
    goal: Tuple[int, int],
    grid_width: int,
    grid_height: int,
    blocked_positions: Set[Tuple[int, int]],
    resource_positions: Set[Tuple[int, int]] = None
) -> Optional[List[Tuple[int, int]]]:
    if start == goal:
        return [start]
    
    if resource_positions is None:
        resource_positions = set()
    
    walkable_resources = {goal} if goal in resource_positions else set()
    blocked_resources = resource_positions - walkable_resources
    
    counter = 0
    open_set = [(0, counter, start)]
    heapq.heapify(open_set)
    
    came_from = {}
    g_score = {start: 0}
    f_score = {start: manhattan_distance(start, goal)}
    
    open_set_hash = {start}
    
    while open_set:
        _, _, current = heapq.heappop(open_set)
        open_set_hash.discard(current)
        
        if current == goal:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            path.reverse()
            return path
        
        for neighbor in get_neighbors(current, grid_width, grid_height):
            if neighbor in blocked_positions:
                continue
            if neighbor in blocked_resources:
                continue
            
            tentative_g_score = g_score[current] + 1
            
            if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = tentative_g_score + manhattan_distance(neighbor, goal)
                
                if neighbor not in open_set_hash:
                    counter += 1
                    heapq.heappush(open_set, (f_score[neighbor], counter, neighbor))
                    open_set_hash.add(neighbor)
    
    return None


def find_adjacent_position(
    target: Tuple[int, int],
    grid_width: int,
    grid_height: int,
    blocked_positions: Set[Tuple[int, int]],
    resource_positions: Set[Tuple[int, int]]
) -> Optional[Tuple[int, int]]:
    for neighbor in get_neighbors(target, grid_width, grid_height):
        if neighbor not in blocked_positions and neighbor not in resource_positions:
            return neighbor
    return None


def find_nearest_resource(
    start: Tuple[int, int],
    resource_positions: List[Tuple[int, int]],
    blocked_positions: Set[Tuple[int, int]] = None
) -> Optional[Tuple[int, int]]:
    if not resource_positions:
        return None
    
    if blocked_positions is None:
        blocked_positions = set()
    
    available = [pos for pos in resource_positions if pos not in blocked_positions]
    
    if not available:
        available = resource_positions
    
    return min(available, key=lambda pos: manhattan_distance(start, pos))
