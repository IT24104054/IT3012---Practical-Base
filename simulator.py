# simulator.py
from visual_grid_game import VisualGridHuntGame
from agent import ModelBasedAgent

def run_grid_hunt():
    env = VisualGridHuntGame()
    agent = ModelBasedAgent()

    print("=== UC Berkeley Style Small Grid Hunt Started ===")
    while not env.is_done():
        percept = env.get_percept()
        action = agent.sense_and_act(percept)
        env.execute_action(action)
        print(f"Action: {action} | Wall Ahead: {percept['wall_ahead']} | Food Here: {percept['food_here']} | Score: {percept['score']}")

    print(f"\nGame Over! Final Score: {env.score} after {env.steps} steps.")
    print(f"Food Remaining: {len(env.food_positions)}")
    print(f"Traps Remaining: {len(env.toxic_traps)}")

if __name__ == "__main__":
    run_grid_hunt()