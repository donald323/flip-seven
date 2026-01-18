# Flip 7

A card game simulation framework with AI strategy tournaments. Players draw cards and must avoid duplicates while maximizing their score.

## Game Rules

- Deck: Cards 0-12, with n copies of value n (e.g., 5 cards of value 5)
- Players draw cards one at a time
- **Bust**: Drawing a duplicate card in your hand (score 0 for round)
- **Flip 7**: Collecting 7 unique cards (15 point bonus)
- **Stay**: Stop drawing and bank your hand's total
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

Strategies decide when to stay based on three conditions:
- **Score threshold**: Stay at target score (10/15/20/25/30)
- **Hand size limit**: Stay at card count (3/4/5/6/7)
- **High-value cards**: Stay when holding risky cards (≥6/7/8/9/10)

**575 unique strategies** generated from:
- 25 single-condition strategies
- 175 two-condition combinations
- 375 three-condition combinations

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