# Tactical Dogfight Pathing — Project Documentation & State Tracker

This document summarizes the current status, architecture, and roadmap of the **Tactical Dogfight Pathing** project for BCSE306L (Artificial Intelligence). It serves as a catch-up guide and reference for reviews.

---

## 1. Project Overview & Proposal (Review 1 Context)
- **Domain**: 2D Grid-based aerial dogfight modelled as a two-player, zero-sum pursuit-evasion game.
- **Goal**: Jet A (Max) and Jet B (Min) manoeuvre on a 20×20 grid. A jet wins by positioning itself onto the opponent's tail — within weapons range $R$ and inside its forward firing cone ($\text{angle-off} \le \theta$) — before the opponent does.
- **Core AI Techniques**: 
  - Module 3: Game Playing.
  - Minimax Tree Search.
  - Alpha-Beta Pruning.
  - Comparative analysis of Plain Minimax vs. Alpha-Beta Minimax.

---

## 2. Mathematical Formulation

| Component | Definition |
| :--- | :--- |
| **State Space** | $(x_A, y_A, h_A, x_B, y_B, h_B, t)$ where positions are $(x, y) \in [0, 19]^2$, headings $h \in \{0^\circ, 45^\circ, 90^\circ, 135^\circ, 180^\circ, 225^\circ, 270^\circ, 315^\circ\}$, and $t$ is turn count. |
| **Action Space** | 3 actions per ply: $\{\text{Turn Left } (+45^\circ), \text{Hold Heading } (0^\circ), \text{Turn Right } (-45^\circ)\}$. After turning, jet moves 1 cell forward. |
| **Transition Model** | $h' = (h + \Delta h) \pmod{360^\circ}$, $(x', y') = \text{clip}((x + \Delta x, y + \Delta y), [0, 19])$. |
| **Terminal Condition** | Win: Euclidean distance $\le R$ ($5.0$ cells) and $\text{angle-off} \le \theta$ ($45.0^\circ$). Draw: $t \ge T_{\max}$ ($20$ turns). |
| **Evaluation Function** | $f(s) = w_1 \cdot (\text{angle-off advantage}) + w_2 \cdot (\text{range envelope}) - w_3 \cdot (\text{edge penalty})$ computed as $\text{Score}_A - \text{Score}_B$. |

---

## 3. Review 2 Requirements & Implementation Status

### Review 2 Criteria (Prof. Nancy Lydia R)
1. **Working AI Core on Real Test Case (3 marks)**:
   - End-to-end execution producing visible reasoning and output.
   - No external libraries standing in for search reasoning.
   - Prepared for arbitrary/custom input scenarios requested by the evaluator on the spot.
2. **Understanding of Algorithm (2 marks)**:
   - Viva readiness: mechanism, assumptions, failure modes.

### What is Implemented in [`dogfight_ai.py`](file:///d:/Desktop/AI%20Project/dogfight_ai.py)
1. **Dual Search Algorithms**:
   - `minimax_plain()`: Brute-force exhaustive adversarial search.
   - `minimax_alpha_beta()`: Branch-and-bound adversarial search with $\alpha$-$\beta$ cutoffs.
2. **Turn-by-Turn Algorithmic Comparison**:
   - Compares both solvers at each step.
   - Reports: Nodes explored, execution time (seconds), evaluated position score, and exact **Pruning Efficiency %**.
3. **Live 2D Terminal Grid Visualization**:
   - 20×20 ASCII grid rendered at every completed round.
   - Directional ASCII indicators: `>` ($0^\circ$), `^` ($90^\circ$), `<` ($180^\circ$), `v` ($270^\circ$), `/` ($45^\circ, 225^\circ$), `\` ($135^\circ, 315^\circ$).
4. **Dynamic Scenario Input**:
   - Prompt allows instant selection of the default benchmark scenario or custom $(x, y, h)$ coordinates for both jets on the fly.
5. **Demonstration Pacing**:
   - Integrated delays (`time.sleep`) between moves so the search process can be watched cleanly in real time.

---

## 4. Key Questions & Viva Preparation (Review 2)

### Q1: How does the Minimax with Alpha-Beta pruning mechanism work here?
- **Answer**: Game tree alternate plies between Jet A (maximizing evaluation score $f(s)$) and Jet B (minimizing $f(s)$). 
- $\alpha$ maintains the best score guaranteed to the Maximizer so far; $\beta$ maintains the best score guaranteed to the Minimizer. 
- When $\beta \le \alpha$, the current branch cannot influence the optimal decision at the root, allowing immediate branch pruning (saving up to 50%+ state expansions depending on move ordering).

### Q2: What assumptions does the model make?
- Turn-based alternating moves (rather than simultaneous continuous-time control).
- Perfect information (both aircraft know exact coordinates and headings of each other).
- Deterministic movement with hard grid bounds.

### Q3: Where can this algorithm fail or struggle?
- **Horizon Effect**: Tactical traps or missile envelopes just beyond the search depth (e.g., depth 5) cannot be anticipated without quiescence search or deeper lookahead.
- **Move Ordering**: Without heuristic move sorting (trying the best tactical moves first), worst-case pruning degrades towards standard minimax complexity $O(b^d)$.

---

## 5. Next Steps for Review 3 & Final Submission
- [ ] **Tournament & Batch Harness**: Automated simulator running $N$ games across randomized start configurations.
- [ ] **Heuristic Weight Ablation**: Compare Angle-dominant ($w_1 \gg w_2$) vs Range-dominant ($w_2 \gg w_1$) vs Balanced agents.
- [ ] **Data Logging & Visual Charts**: Generate tables and bar charts for win-rate, average game duration, and average nodes explored.
- [ ] **Optional GUI / Pygame Visualizer**: Upgrade ASCII grid to a 2D graphical display if time permits.
