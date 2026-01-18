# Flip 7

A card game simulation framework with AI strategy tournaments. Players draw cards and must avoid duplicates while maximizing their score.

## Game Rules

- **Deck**: 
  - Number cards 0-12, with n copies of value n (e.g., 5 cards of value 5)
  - Modifier cards: +2, +4, +6, +8, +10, x2 (one of each)
  - **Action cards** (3 of each):
    - **FREEZE**: Freeze an opponent for the rest of the round (forced stay)
    - **FLIP3**: Force a player to draw 3 cards immediately
    - **SECOND_CHANCE**: Prevent one bust (duplicate card)
- Players draw cards one at a time
- **Bust**: Drawing a duplicate card in your hand (score 0 for round)
  - **Second Chance**: If held, prevents bust and is consumed
- **Flip 7**: Collecting 7 unique cards (15 point bonus)
- **Stay**: Stop drawing and bank your hand's total
- **Scoring**: Sum of number cards × 2 (if x2 present) + modifier bonuses (if +N present)
- First to 200 points wins

## Quick Start

### Run Tournament
```bash
python src/run_championship.py
```

### Interactive Notebook
```bash
jupyter notebook notebooks/championship_notebook.ipynb
```

## Project Structure

```
├── src/                        # Source code
│   ├── game_controller.py      # Core game logic
│   ├── player.py               # Player and strategy classes
│   ├── environment.py          # Game simulation environment
│   ├── league_simulation.py   # Tournament framework
│   ├── league_visualizer.py   # Results visualization
│   └── run_championship.py    # CLI tournament runner
├── notebooks/                  # Jupyter notebooks
│   ├── championship_notebook.ipynb  # Tournament analysis
│   └── flip7_simulation.ipynb       # Single game simulation
├── config/                     # Configuration files
│   └── strategy_configurations.json # 575 AI strategies
├── README.md
└── LICENSE
```

## Strategy System

### Hit/Stay Decisions
Strategies decide when to stay based on three conditions:
- **Score threshold**: Stay at target score (10/15/20/25/30)
- **Hand size limit**: Stay at card count (3/4/5/6/7)
- **High-value cards**: Stay when holding risky cards (≥6/7/8/9/10)

### Action Card Decisions (Risk-Manipulation Strategy)
When action cards are drawn, strategies make optimal decisions:

**FREEZE Decision**:
- Priority 1: Freeze players WITH Second Chance (prevents safe progress)
- Priority 2: Among those, freeze player with SMALLEST hand value
- Purpose: Deny safe scoring opportunities

**FLIP3 Decision**:
- Target players with HIGHEST number card hand values
- Purpose: Force high-risk opponents to draw and likely bust

**SECOND_CHANCE Decision**:
- Keep first one for self
- Give extras to opponent with SMALLEST hand (waste it)
- Discard if all active players already have one
- Purpose: Waste safety nets on players least likely to need them

**575 unique strategies** generated from:
- 25 single-condition strategies
- 175 two-condition combinations
- 375 three-condition combinations
- All with integrated action card decision-making

## Tournament Features

- **Turn-based structure**: 575 players, equal participation
- **Configurable**: Adjust turns, players per game, seed
- **Performance optimized**: Minimal logging for large tournaments
- **Statistical analysis**: Win rates, score distributions, strategy effectiveness
- **Visualizations**: Histograms, performance comparisons, strategy rankings

## Configuration

Edit tournament parameters in notebook or script:
```python
NUM_TURNS = 20           # Games per player
PLAYERS_PER_GAME = 5     # Players in each game
TOURNAMENT_SEED = 42     # Reproducibility
```

## Output

- **Console**: Real-time progress, summary statistics
- **JSON**: Leaderboard and results (minimal by default)
- **Visualizations**: Distribution plots, strategy analysis

## Requirements

```
python >= 3.8
matplotlib
pandas
numpy
```

## License

MIT License