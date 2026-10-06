# Tactical Dogfight Pathing — Comprehensive Study & Viva Guide

This guide is designed for **Parth Khanayat**, **Kushal Goel**, and **Jia Kumar** to study, understand, and ace the **BCSE306L Review 2 Viva**. It breaks down the exact logic, mathematics, and line-by-line code behind [`dogfight_ai.py`](file:///d:/Desktop/AI%20Project/dogfight_ai.py).

---

## 1. What Does Our Project Actually Do? (30-Second Pitch)

> *"We model a 2D grid aerial dogfight between two fighter aircraft (Jet A and Jet B) as a two-player, zero-sum pursuit-evasion game. Each turn, an aircraft can turn left 45°, fly straight, or turn right 45°, advancing one grid cell. A jet wins when it maneuvers behind its enemy — within weapons range ($R = 5$) and inside its forward firing cone ($\theta \le 45^\circ$). To decide the optimal move, we implemented adversarial Minimax search enhanced with Alpha-Beta pruning. We also benchmark this against unpruned Minimax to empirically prove how many state evaluations are saved."*

---

## 2. High-Level Architecture & Game Flow

```
[Initial Positions & Headings (A & B)]
                 │
                 ▼
      Is State Terminal? ──(Yes)──► Game Over (A Wins / B Wins / Draw)
                 │ (No)
                 ▼
  ┌──────────────────────────────────────────────┐
  │ 1. Run Plain Minimax (Brute Force)           │ -> Records: Nodes & Execution Time
  │ 2. Run Minimax with Alpha-Beta Pruning       │ -> Records: Nodes, Cutoffs & Optimal Action
  │ 3. Compute Pruning Efficiency %              │
  └──────────────────────────────────────────────┘
                 │
                 ▼
    Execute Best Action for Active Jet
                 │
                 ▼
    Update Position & Heading (Clipped to Grid)
                 │
                 ▼
    Display 2D ASCII Grid & Turn Metrics
                 │
                 ▼
    Switch Turn (A -> B -> A ...) & Repeat
```

---

## 3. Detailed Line-by-Line Code Breakdown

Open [`dogfight_ai.py`](file:///d:/Desktop/AI%20Project/dogfight_ai.py) alongside this section.

### Block 1: Imports & Global Constants (Lines 1 – 28)
```python
import math
import copy
import time
```
- **`math`**: Used for trigonometry (`atan2`, `hypot`, `degrees`, `inf`).
- **`copy`**: Used (`copy.copy`) to duplicate game states when generating child nodes without mutating parent states.
- **`time`**: Used to benchmark runtime (`time.time()`) and add pacing delays (`time.sleep()`).

```python
GRID_W = 20
GRID_H = 20
WEAPONS_RANGE = 5.0
FIRING_CONE_ANGLE = 45.0
TURN_LIMIT = 20
```
- Defines the 20×20 battle arena.
- **`WEAPONS_RANGE = 5.0`**: Maximum Euclidean distance to lock on and fire.
- **`FIRING_CONE_ANGLE = 45.0`**: Half-angle of forward radar/firing cone (total $90^\circ$ envelope, $\pm 45^\circ$).
- **`TURN_LIMIT = 20`**: Max turns before declaring a tactical draw.

```python
W1 = 10.0   # Angle-off advantage weight
W2 = 2.0    # Range-to-envelope score weight
W3 = 5.0    # Edge-proximity penalty weight
```
- Evaluation function weights ($w_1, w_2, w_3$) defining aggressive tactical priorities.

```python
HEADING_VECS = {
    0: (1, 0),     45: (1, 1),    90: (0, 1),    135: (-1, 1),
    180: (-1, 0), 225: (-1, -1), 270: (0, -1),  315: (1, -1)
}
```
- Discretizes aircraft headings into 8 compass directions. $0^\circ$ is East ($+x$), $90^\circ$ is North ($+y$), $180^\circ$ is West ($-x$), $270^\circ$ is South ($-y$).

---

### Block 2: Angle Difference Function (Lines 30 – 32)
```python
def get_angle_diff(a1, a2):
    diff = abs((a1 - a2) % 360)
    return min(diff, 360 - diff)
```
- **Why this is needed**: Standard subtraction doesn't account for circle wraparound. For example, $350^\circ$ and $10^\circ$ are only $20^\circ$ apart, not $340^\circ$. `min(diff, 360 - diff)` calculates the minimal angular distance along the circle $[0^\circ, 180^\circ]$.

---

### Block 3: The `GameState` Class (Lines 34 – 80)
The state object stores everything needed to uniquely describe the dogfight at any moment.

- **`__init__(self, xA, yA, hA, xB, yB, hB, t, current_turn='A')`**:
  - Positions $(x_A, y_A)$, $(x_B, y_B)$.
  - Headings $h_A, h_B \in [0^\circ, 315^\circ]$.
  - Turn number $t$.
  - Whos turn it is (`current_turn`: `'A'` or `'B'`).

- **`is_terminal(self)`**:
  - Evaluates if Jet A has won, Jet B has won, or the game reached a draw ($t \ge \text{TURN\_LIMIT}$).

- **`check_win(self, x1, y1, h1, x2, y2)`**:
  1. **Range Check**: `dist = math.hypot(x1 - x2, y1 - y2)`. If `dist > WEAPONS_RANGE`, return `False`.
  2. **Target Angle**: `math.atan2(y2 - y1, x2 - x1)` converts the vector from attacker to target into a polar angle in degrees.
  3. **Angle-Off Check**: Measures how far the target is from the attacker's nose. If `angle_off <= FIRING_CONE_ANGLE`, the attacker has a firing solution (kill condition achieved).

- **`get_legal_actions(self)`**:
  - Returns `[-45, 0, 45]` (Turn Right 45°, Maintain Heading, Turn Left 45°).

- **`apply_action(self, action)`**:
  - Updates heading: `(current_h + action) % 360`.
  - Moves forward by $(dx, dy)$ corresponding to new heading.
  - Bounds clipping: `max(0, min(GRID_W - 1, new_x))` prevents aircraft from leaving the grid.
  - Toggles active turn between `'A'` and `'B'`.

---

### Block 4: Heuristic Evaluation Function (Lines 82 – 113)
```python
def evaluate(state):
```
When search reaches depth 0 without a terminal win, this function rates how favorable the board state is for Jet A (positive = good for A, negative = good for B).

- **Terminal States**:
  - A wins: $+1,000,000$
  - B wins: $-1,000,000$
  - Draw: $0$
- **Non-Terminal Tactical Score (`calc_score`)**:
  1. **Angle-Off Advantage**:
     $$\text{angle\_score} = \frac{180 - \text{angle\_off}}{180}$$
     Gives $1.0$ if pointed directly at enemy, $0.0$ if pointed completely away ($180^\circ$).
  2. **Range-to-Envelope Score**:
     $$\text{range\_score} = -|\text{dist} - \text{opt\_range}|$$
     Rewards closing distance to ideal firing distance ($80\%$ of weapon range).
  3. **Edge Proximity Penalty**:
     $$\text{edge\_penalty} = \max(0, 3 - \text{dist\_to\_edge})$$
     Penalizes flying within 3 cells of the wall to prevent getting trapped.
- **Zero-Sum Utility**:
  $$f(s) = \text{Score}_A - \text{Score}_B$$

---

### Block 5: Minimax Search Algorithms (Lines 115 – 184)

#### A. Standard Minimax (`minimax_plain`, Lines 156 – 184)
- Recursively expands **all 3 actions** at every ply until `depth == 0`.
- Maximizer chooses $\max(\text{eval})$, Minimizer chooses $\min(\text{eval})$.
- Total nodes explored is roughly $O(b^d) = 3^5 = 243$ per move.

#### B. Minimax with Alpha-Beta Pruning (`minimax_alpha_beta`, Lines 117 – 152)
- **$\alpha$**: The highest score that Maximizer is guaranteed so far.
- **$\beta$**: The lowest score that Minimizer is guaranteed so far.
- **Pruning condition**:
  ```python
  if beta <= alpha:
      break
  ```
  If Minimizer already has an option with value $\le \alpha$, Maximizer would never allow the game to enter this sub-branch. The remaining sibling nodes are skipped (pruned).

---

### Block 6: Grid Visualization & Action Formatting (Lines 186 – 219)
- **`get_arrow(heading)`**:
  - Translates numerical degrees into ASCII arrows:
    - $0^\circ \to$ `>`
    - $90^\circ \to$ `^`
    - $180^\circ \to$ `<`
    - $270^\circ \to$ `v`
    - Diagonals $\to$ `/` and `\`
- **`print_grid(state)`**:
  - Prints a 20×20 Cartesian grid with Y going from 19 down to 0, showing `A` and `B` with their heading markers.
- **`action_to_str(act)`**:
  - Converts $-45 \to$ "Turn Right", $0 \to$ "Hold", $+45 \to$ "Turn Left".

---

### Block 7: Main Execution & Live Benchmark (Lines 221 – 295)
- Prompts user: Press **ENTER** for default scenario or type **`custom`** to test custom coordinates on the fly.
- Enters `while True:` loop running turns until terminal condition:
  1. Computes plain Minimax metrics.
  2. Computes Alpha-Beta Minimax metrics.
  3. Displays:
     ```text
     Algorithm Comparison at Search Depth 5:
       Standard Minimax :   364 nodes explored | Time: 0.0051s | Value: 0.00
       Alpha-Beta Minimax:   301 nodes explored | Time: 0.0038s | Value: 0.00
       --> Alpha-Beta Pruned 17.3% of search tree!
     ```
  4. Applies the action to the real state.
  5. Renders grid and pauses (`time.sleep`) so the reviewer can watch the jets dogfight step by step.

---

## 4. Expected Viva Questions & Answers (For the 2 Marks)

### Q1: "Explain how your Minimax with Alpha-Beta pruning works."
**Answer**:
> *"Our game is zero-sum and turn-based. Jet A tries to maximize our custom tactical utility score, while Jet B tries to minimize it. We search 5 plies ahead. In Alpha-Beta pruning, $\alpha$ tracks the highest value the maximizer has secured, and $\beta$ tracks the lowest value the minimizer has secured. Whenever $\beta \le \alpha$, we prune the remaining branches because the opponent would never let play reach that branch. This yields the identical mathematical optimal decision as standard Minimax, but in fewer node evaluations."*

### Q2: "Can you prove that Alpha-Beta actually prunes nodes?"
**Answer**:
> *"Yes, our script runs both Plain Minimax and Alpha-Beta Minimax side-by-side on each turn and outputs the exact node count. On our benchmark runs, Alpha-Beta consistently prunes between 15% and 40%+ of the game tree compared to plain Minimax."*

### Q3: "What are the core assumptions in your formulation?"
**Answer**:
1. **Discrete Alternating Turns**: Aircraft move sequentially on discrete 45° headings rather than simultaneous continuous aerodynamics.
2. **Perfect Information**: Full observability — both aircraft know each other's exact position and heading.
3. **Deterministic Dynamics**: Actions always succeed without wind or mechanical drift.

### Q4: "Where does this algorithm fail or suffer limitations?"
**Answer**:
1. **Horizon Effect**: If a critical tactical event occurs at depth 6, a depth-5 search cannot see it.
2. **Branching Factor / Depth Limit**: Plain Minimax is exponential ($O(b^d)$). Without pruning or depth bounding, real-time response would be impossible.
3. **Move Ordering Sensitivity**: Alpha-Beta achieves optimal $O(b^{d/2})$ complexity only if the best moves are explored first. Without heuristic move ordering, worst-case performance approaches standard Minimax.

### Q5: "If I ask you to run another coordinate set, can your code do it?"
**Answer**:
> *"Yes! When launching `python dogfight_ai.py`, we can type `custom` to input any starting X, Y, and heading for both Jet A and Jet B."*

---

## 5. Team Roles Quick Reference

| Member | Focus Area | What to Explain in Viva |
| :--- | :--- | :--- |
| **Parth Khanayat** | Game Engine & Search Core | `GameState`, transition model, `minimax_alpha_beta()`, recursive depth, $\alpha$-$\beta$ cutoffs. |
| **Kushal Goel** | Heuristic & Evaluation Design | `evaluate()`, angle-off advantage, firing cone math (`atan2`), range envelope, and edge penalties. |
| **Jia Kumar** | Benchmarking & Metrics | Pruning efficiency comparison, node count logs, execution timings, and terminal visualization. |
