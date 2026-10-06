import math
import copy
import time

# --- CONFIGURATION ---
GRID_W = 20
GRID_H = 20
WEAPONS_RANGE = 5.0
FIRING_CONE_ANGLE = 45.0  # degrees (+/- 45 means a 90 degree cone, or just angle-off <= 45)
TURN_LIMIT = 20

# Evaluation weights
W1 = 10.0   # Angle-off advantage
W2 = 2.0    # Range score (closer is better, up to a point)
W3 = 5.0    # Edge-proximity penalty

HEADING_VECS = {
    0: (1, 0),
    45: (1, 1),
    90: (0, 1),
    135: (-1, 1),
    180: (-1, 0),
    225: (-1, -1),
    270: (0, -1),
    315: (1, -1)
}

def get_angle_diff(a1, a2):
    diff = abs((a1 - a2) % 360)
    return min(diff, 360 - diff)

class GameState:
    def __init__(self, xA, yA, hA, xB, yB, hB, t, current_turn='A'):
        self.xA = xA
        self.yA = yA
        self.hA = hA
        self.xB = xB
        self.yB = yB
        self.hB = hB
        self.t = t
        self.current_turn = current_turn  # 'A' or 'B'
        
    def is_terminal(self):
        # A wins
        if self.check_win(self.xA, self.yA, self.hA, self.xB, self.yB):
            return True, 'A'
        # B wins
        if self.check_win(self.xB, self.yB, self.hB, self.xA, self.yA):
            return True, 'B'
        # Draw
        if self.t >= TURN_LIMIT:
            return True, 'Draw'
        return False, None
        
    def check_win(self, x1, y1, h1, x2, y2):
        dist = math.hypot(x1 - x2, y1 - y2)
        if dist > WEAPONS_RANGE or dist == 0:
            return False
            
        target_angle = math.degrees(math.atan2(y2 - y1, x2 - x1)) % 360
        angle_off = get_angle_diff(h1, target_angle)
        
        if angle_off <= FIRING_CONE_ANGLE:
            return True
        return False
        
    def get_legal_actions(self):
        return [-45, 0, 45]  # Right turn, Hold heading, Left turn
        
    def apply_action(self, action):
        new_state = copy.copy(self)
        if self.current_turn == 'A':
            new_state.hA = (self.hA + action) % 360
            dx, dy = HEADING_VECS[new_state.hA]
            new_state.xA = max(0, min(GRID_W - 1, self.xA + dx))
            new_state.yA = max(0, min(GRID_H - 1, self.yA + dy))
            new_state.current_turn = 'B'
        else:
            new_state.hB = (self.hB + action) % 360
            dx, dy = HEADING_VECS[new_state.hB]
            new_state.xB = max(0, min(GRID_W - 1, self.xB + dx))
            new_state.yB = max(0, min(GRID_H - 1, self.yB + dy))
            new_state.current_turn = 'A'
            new_state.t += 1
        return new_state

def evaluate(state):
    terminal, winner = state.is_terminal()
    if terminal:
        if winner == 'A': return 1000000
        if winner == 'B': return -1000000
        return 0
        
    def calc_score(x1, y1, h1, x2, y2):
        target_angle = math.degrees(math.atan2(y2 - y1, x2 - x1)) % 360
        angle_off = get_angle_diff(h1, target_angle)
        angle_score = (180 - angle_off) / 180.0
        
        dist = math.hypot(x1 - x2, y1 - y2)
        # Optimal range is slightly less than WEAPONS_RANGE
        opt_range = WEAPONS_RANGE * 0.8
        range_score = -abs(dist - opt_range)
        
        dist_to_edge = min(x1, GRID_W - 1 - x1, y1, GRID_H - 1 - y1)
        edge_penalty = max(0, 3 - dist_to_edge)
        
        return W1 * angle_score + W2 * range_score - W3 * edge_penalty

    score_A = calc_score(state.xA, state.yA, state.hA, state.xB, state.yB)
    score_B = calc_score(state.xB, state.yB, state.hB, state.xA, state.yA)
    
    return score_A - score_B

# Global variable to track explored nodes
nodes_explored = 0

def minimax_alpha_beta(state, depth, alpha, beta, maximizing_player):
    global nodes_explored
    nodes_explored += 1
    
    terminal, _ = state.is_terminal()
    if depth == 0 or terminal:
        return evaluate(state), None
        
    best_action = None
    if maximizing_player:
        max_eval = -math.inf
        for action in state.get_legal_actions():
            child_state = state.apply_action(action)
            # Next turn belongs to B, so we minimize
            eval_score, _ = minimax_alpha_beta(child_state, depth - 1, alpha, beta, False)
            if eval_score > max_eval:
                max_eval = eval_score
                best_action = action
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval, best_action
    else:
        min_eval = math.inf
        for action in state.get_legal_actions():
            child_state = state.apply_action(action)
            # Next turn belongs to A, so we maximize
            eval_score, _ = minimax_alpha_beta(child_state, depth - 1, alpha, beta, True)
            if eval_score < min_eval:
                min_eval = eval_score
                best_action = action
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval, best_action

def action_to_str(act):
    if act == 0: return "Hold"
    if act == -45: return "Turn Right"
    if act == 45: return "Turn Left"
    return "Unknown"

if __name__ == "__main__":
    print("==================================================")
    print("Tactical Dogfight Pathing - AI Engine Execution")
    print("==================================================\n")
    
    # Initialize real test case
    # Jet A starts at (2, 2) facing Right (0 deg)
    # Jet B starts at (15, 15) facing Left (180 deg)
    initial_state = GameState(xA=2, yA=2, hA=0, xB=15, yB=15, hB=180, t=0, current_turn='A')
    
    search_depth = 5 # 5 plies (A -> B -> A -> B -> A)
    current_state = initial_state
    
    print(f"Starting Conditions:")
    print(f"Jet A: pos({current_state.xA},{current_state.yA}) heading {current_state.hA}°")
    print(f"Jet B: pos({current_state.xB},{current_state.yB}) heading {current_state.hB}°")
    print(f"Weapons Range: {WEAPONS_RANGE}, Firing Cone: {FIRING_CONE_ANGLE}°\n")
    
    while True:
        term, winner = current_state.is_terminal()
        if term:
            print(f"\nGame Over! Result: {'Jet A Wins!' if winner == 'A' else 'Jet B Wins!' if winner == 'B' else 'Draw'}")
            break
            
        print(f"--- Turn {current_state.t}, Player {current_state.current_turn} to move ---")
        
        nodes_explored = 0
        start_time = time.time()
        
        is_max = (current_state.current_turn == 'A')
        val, best_act = minimax_alpha_beta(current_state, search_depth, -math.inf, math.inf, is_max)
        
        end_time = time.time()
        
        print(f"Nodes explored: {nodes_explored} in {end_time-start_time:.3f}s")
        print(f"Evaluation Score: {val:.2f}")
        print(f"Chosen Action: {action_to_str(best_act)} ({best_act}°)")
        
        current_state = current_state.apply_action(best_act)
        
        if current_state.current_turn == 'B':
            print(f"Jet A updated state: pos({current_state.xA},{current_state.yA}) heading {current_state.hA}°\n")
        else:
            print(f"Jet B updated state: pos({current_state.xB},{current_state.yB}) heading {current_state.hB}°\n")
            
        # Optional: break after a few turns if you just want to show it running
        # if current_state.t >= 5: break
