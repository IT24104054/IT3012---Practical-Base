from collections import defaultdict, deque
import heapq
import math

from logic_engine import KnowledgeBase

class SimpleReflexAgent:
    def sense_and_act(self, percept):
        if percept.get('food_here'):
            return 'suck'
        elif percept.get('wall_ahead'):
            return 'turn_left'
        else:
            return 'move_forward'


class ModelBasedAgent:
    def __init__(self):
        self.visit_counts = defaultdict(int)
        self.known_walls = set()
        self.current_pos = (0, 0)
        self.facing = 'Up'
        self.last_action = None

    def get_visit_count(self, cell):
        if cell in self.known_walls:
            return 999999
        return self.visit_counts[cell]

    def sense_and_act(self, percept):
        dirs = ['Up', 'Right', 'Down', 'Left']
        dir_offsets = {
            'Up': (0, 1),
            'Right': (1, 0),
            'Down': (0, -1),
            'Left': (-1, 0)
        }

        if self.last_action == 'turn_left':
            idx = dirs.index(self.facing)
            self.facing = dirs[(idx - 1) % 4]
        elif self.last_action == 'turn_right':
            idx = dirs.index(self.facing)
            self.facing = dirs[(idx + 1) % 4]
        elif self.last_action == 'move_forward':
            dx, dy = dir_offsets[self.facing]
            self.current_pos = (self.current_pos[0] + dx, self.current_pos[1] + dy)

        self.visit_counts[self.current_pos] += 1

        idx = dirs.index(self.facing)
        front_dir = dirs[idx]
        left_dir = dirs[(idx - 1) % 4]
        right_dir = dirs[(idx + 1) % 4]

        fx, fy = dir_offsets[front_dir]
        lx, ly = dir_offsets[left_dir]
        rx, ry = dir_offsets[right_dir]

        front_cell = (self.current_pos[0] + fx, self.current_pos[1] + fy)
        left_cell = (self.current_pos[0] + lx, self.current_pos[1] + ly)
        right_cell = (self.current_pos[0] + rx, self.current_pos[1] + ry)

        if percept.get('wall_ahead'):
            self.known_walls.add(front_cell)

        if percept.get('food_here'):
            action = 'suck'
        elif percept.get('wall_ahead'):
            left_count = self.get_visit_count(left_cell)
            right_count = self.get_visit_count(right_cell)
            if left_count < right_count:
                action = 'turn_left'
            else:
                action = 'turn_right'
        else:
            front_count = self.get_visit_count(front_cell)
            left_count = self.get_visit_count(left_cell)
            right_count = self.get_visit_count(right_cell)

            if front_count == 0:
                action = 'move_forward'
            elif left_count == 0:
                action = 'turn_left'
            elif right_count == 0:
                action = 'turn_right'
            else:
                min_count = min(front_count, left_count, right_count)
                if min_count == front_count:
                    action = 'move_forward'
                elif min_count == left_count:
                    action = 'turn_left'
                else:
                    action = 'turn_right'

        self.last_action = action
        return action


class SearchAgent:
    """Goal-based agent that plans an offline path to the nearest food using
    an uninformed search strategy (BFS, DFS, or UCS) before acting."""

    # Direction -> (dx, dy) offset. These match the movement actions accepted
    # directly by execute_action in the grid environments.
    DIRECTIONS = {
        'Up': (0, 1),
        'Down': (0, -1),
        'Left': (-1, 0),
        'Right': (1, 0)
    }

    def __init__(self):
        self.plan = []
        self.active_algo = 'BFS'
        self.current_pos = (0, 0)
        self.kb = KnowledgeBase()
        self.kb.tell_rule(['TargetVisible', 'HasDust'], 'SafeToEngage')
        self.kb.tell_rule(['SafeToEngage', 'BloodseekerMissing'], 'Retreat')

    # ---------------------------------------------------------------
    # Planning entry point
    # ---------------------------------------------------------------
    def sense_and_act(self, percept):
        if not self.plan:
            all_food = percept.get('all_food', [])
            grid_size = percept.get('grid_size', (10, 10))
            walls = percept.get('walls', [])
            remaining_food = percept.get('remaining_food', len(all_food))

            if not all_food or remaining_food == 0:
                # Nothing left to plan for.
                return 'suck'

            goal = self._closest_food(self.current_pos, all_food)

            if self.active_algo == 'DFS':
                path = self.dfs_search(self.current_pos, goal, walls, grid_size)
            elif self.active_algo == 'UCS':
                path = self.ucs_search(self.current_pos, goal, walls, grid_size)
            elif self.active_algo == 'AStar':
                path = self.astar_search(self.current_pos, goal, walls, grid_size, percept=percept)
            else:
                path = self.bfs_search(self.current_pos, goal, walls, grid_size)

            # If no path exists (e.g. food is walled off), fall back to a
            # single no-op so the agent doesn't crash.
            self.plan = path if path else ['suck']

        action = self.plan.pop(0)

        # Keep our internal model of position in sync with the plan we
        # committed to (this is a Goal-Based agent operating on its own
        # world model, so it doesn't need a fresh percept every step).
        if action in self.DIRECTIONS:
            dx, dy = self.DIRECTIONS[action]
            self.current_pos = (self.current_pos[0] + dx, self.current_pos[1] + dy)

        return action

    @staticmethod
    def _closest_food(pos, all_food):
        return min(
            all_food,
            key=lambda f: abs(f[0] - pos[0]) + abs(f[1] - pos[1])
        )

    # ---------------------------------------------------------------
    # Shared helpers
    # ---------------------------------------------------------------
    def _neighbors(self, cell, walls, grid_size):
        width, height = grid_size
        x, y = cell
        for action, (dx, dy) in self.DIRECTIONS.items():
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in walls:
                yield action, (nx, ny)

    @staticmethod
    def _reconstruct_path(parent, start, goal):
        if goal not in parent:
            return None
        actions = []
        node = goal
        while node != start:
            prev_node, action = parent[node]
            actions.append(action)
            node = prev_node
        actions.reverse()
        return actions

    # ---------------------------------------------------------------
    # Breadth-First Search - FIFO frontier (deque.popleft)
    # ---------------------------------------------------------------
    def bfs_search(self, start, goal, walls, grid_size):
        walls = set(walls)
        start, goal = tuple(start), tuple(goal)

        frontier = deque([start])
        reached = {start}
        parent = {start: (None, None)}

        while frontier:
            current = frontier.popleft()
            if current == goal:
                return self._reconstruct_path(parent, start, goal)

            for action, neighbor in self._neighbors(current, walls, grid_size):
                if neighbor not in reached:
                    reached.add(neighbor)
                    parent[neighbor] = (current, action)
                    frontier.append(neighbor)

        return None

    # ---------------------------------------------------------------
    # Depth-First Search - LIFO frontier (list.pop)
    # ---------------------------------------------------------------
    def dfs_search(self, start, goal, walls, grid_size):
        walls = set(walls)
        start, goal = tuple(start), tuple(goal)

        frontier = [start]
        reached = {start}
        parent = {start: (None, None)}

        while frontier:
            current = frontier.pop()
            if current == goal:
                return self._reconstruct_path(parent, start, goal)

            for action, neighbor in self._neighbors(current, walls, grid_size):
                if neighbor not in reached:
                    reached.add(neighbor)
                    parent[neighbor] = (current, action)
                    frontier.append(neighbor)

        return None

    # ---------------------------------------------------------------
    # Uniform-Cost Search - Priority Queue (heapq), g(n) = step cost
    # ---------------------------------------------------------------
    def ucs_search(self, start, goal, walls, grid_size):
        walls = set(walls)
        start, goal = tuple(start), tuple(goal)

        counter = 0  # tie-breaker so heapq never compares tuples with equal cells
        frontier = [(0, counter, start)]
        cost_so_far = {start: 0}
        parent = {start: (None, None)}

        while frontier:
            cost, _, current = heapq.heappop(frontier)

            if current == goal:
                return self._reconstruct_path(parent, start, goal)

            if cost > cost_so_far.get(current, float('inf')):
                continue  # stale entry

            for action, neighbor in self._neighbors(current, walls, grid_size):
                new_cost = cost_so_far[current] + 1  # uniform step cost
                if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                    cost_so_far[neighbor] = new_cost
                    parent[neighbor] = (current, action)
                    counter += 1
                    heapq.heappush(frontier, (new_cost, counter, neighbor))

        return None

    # ---------------------------------------------------------------
    # Heuristic functions - h(n): estimated cost from pos to goal
    # ---------------------------------------------------------------
    def manhattan_distance(self, pos, goal):
        x1, y1 = pos
        x2, y2 = goal
        return abs(x1 - x2) + abs(y1 - y2)

    def euclidean_distance(self, pos, goal):
        x1, y1 = pos
        x2, y2 = goal
        return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

    def _is_feasible(self, tile, percept):
        """Use the KB to reject logically unsafe, physically reachable tiles."""
        self.kb.clear_facts()
        percept = percept or {}

        target_positions = {tuple(position) for position in percept.get(
            'target_positions', percept.get('all_food', []))}
        dust_positions = {tuple(position) for position in percept.get(
            'dust_positions', percept.get('toxic_traps', []))}
        bloodseeker_positions = {tuple(position) for position in percept.get(
            'bloodseeker_positions', percept.get('opponents', []))}

        if tile in target_positions:
            self.kb.tell_fact('TargetVisible')
        if tile in dust_positions:
            self.kb.tell_fact('HasDust')
        if percept.get('bloodseeker_missing', not bloodseeker_positions):
            self.kb.tell_fact('BloodseekerMissing')

        self.kb.forward_chain()
        return 'Retreat' not in self.kb.facts

    # ---------------------------------------------------------------
    # A* Search - Priority Queue ordered by f(n) = g(n) + h(n)
    # ---------------------------------------------------------------
    def astar_search(self, start_pos, goal_pos, walls, grid_size,
                     heuristic_type='manhattan', percept=None):
        walls = set(walls)
        start_pos, goal_pos = tuple(start_pos), tuple(goal_pos)

        heuristic_fn = (self.euclidean_distance if heuristic_type == 'euclidean'
                         else self.manhattan_distance)

        g_start = 0
        h_start = heuristic_fn(start_pos, goal_pos)
        f_start = g_start + h_start

        # A* tuple format: (f_cost, g_cost, current_pos, path_taken)
        frontier = [(f_start, g_start, start_pos, [])]
        reached_states = set()

        while frontier:
            f_cost, g_cost, current_pos, path_taken = heapq.heappop(frontier)

            if current_pos == goal_pos:
                return path_taken

            if current_pos in reached_states:
                continue
            reached_states.add(current_pos)

            for action, neighbor in self._neighbors(current_pos, walls, grid_size):
                if neighbor in reached_states:
                    continue
                if not self._is_feasible(neighbor, percept):
                    continue
                g_new = g_cost + 1
                h_new = heuristic_fn(neighbor, goal_pos)
                f_new = g_new + h_new
                heapq.heappush(frontier, (f_new, g_new, neighbor, path_taken + [action]))

        return None