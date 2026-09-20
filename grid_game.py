# grid_game.py
import random


class GridHuntGame:
    """A small Pacman-style grid environment (4x4) where an agent collects food."""

    def __init__(self, width=4, height=4):
        self.width = width
        self.height = height
        self.agent_pos = [0, 0]  # Starting position (x, y)

        # Place a few random food pellets and obstacles (walls)
        self.food_positions = {(1, 2), (2, 3), (3, 0), (2, 1)}
        self.walls = {(1, 1), (2, 2)}
        self.toxic_traps = {(3, 2), (1, 3)}

        self.score = 0
        self.steps = 0
        self.facing = 'Up'

    def get_percept(self, agent=None) -> dict:
        dx, dy = 0, 0
        if self.facing == 'Up':
            dy = 1
        elif self.facing == 'Down':
            dy = -1
        elif self.facing == 'Left':
            dx = -1
        elif self.facing == 'Right':
            dx = 1

        front_x = self.agent_pos[0] + dx
        front_y = self.agent_pos[1] + dy

        wall_ahead = (
            front_x < 0 or front_x >= self.width or
            front_y < 0 or front_y >= self.height or
            (front_x, front_y) in self.walls
        )

        return {
            'wall_ahead': wall_ahead,
            'food_here': tuple(self.agent_pos) in self.food_positions,
            'score': self.score,
            'remaining_food': len(self.food_positions)
        }

    def execute_action(self, action: str, agent=None):
        self.steps += 1
        dirs = ['Up', 'Right', 'Down', 'Left']

        if action == 'turn_left':
            idx = dirs.index(self.facing)
            self.facing = dirs[(idx - 1) % 4]
        elif action == 'turn_right':
            idx = dirs.index(self.facing)
            self.facing = dirs[(idx + 1) % 4]
        elif action == 'suck':
            tuple_pos = tuple(self.agent_pos)
            if tuple_pos in self.food_positions:
                self.food_positions.remove(tuple_pos)
                self.score += 20
        elif action == 'move_forward' or action in ['Up', 'Down', 'Left', 'Right']:
            new_pos = list(self.agent_pos)
            move_dir = self.facing if action == 'move_forward' else action
            if move_dir == 'Up':
                new_pos[1] = min(self.height - 1, new_pos[1] + 1)
            elif move_dir == 'Down':
                new_pos[1] = max(0, new_pos[1] - 1)
            elif move_dir == 'Left':
                new_pos[0] = max(0, new_pos[0] - 1)
            elif move_dir == 'Right':
                new_pos[0] = min(self.width - 1, new_pos[0] + 1)

            if tuple(new_pos) in self.walls:
                self.score -= 5
            else:
                self.agent_pos = new_pos

        tuple_pos = tuple(self.agent_pos)
        if tuple_pos in self.toxic_traps:
            self.score -= 15
            self.toxic_traps.remove(tuple_pos)

    def is_done(self) -> bool:
        return len(self.food_positions) == 0 or self.steps >= 20