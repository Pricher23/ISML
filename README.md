# Cooperative Kitchen - Multi-Agent Simulation

A multi-agent system simulating a commercial kitchen environment using the MESA framework. The system demonstrates intelligent agent coordination, resource contention management, and task allocation through Contract Net Protocol (CNP) and Belief-Desire-Intention (BDI) architectures.

## Features

- **Contract Net Protocol (CNP)**: Head Chef broadcasts tasks, Line Cooks bid based on distance and workload
- **BDI Architecture**: Line Cooks use Beliefs, Desires, and Intentions for decision-making
- **A\* Pathfinding**: Intelligent navigation with collision avoidance
- **Resource Management**: Contention handling with queuing system
- **Unattended Cooking**: Stoves and ovens can cook without a cook present
- **Order System**: 6 recipes with time limits, win/lose conditions

## Requirements

- Python 3.8+
- MESA framework 2.1.0+
- NumPy
- Matplotlib

## Installation

1. Create and activate a virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Simulation

### Matplotlib Visualization (Default)
```bash
python run.py
```

### Web Visualization
```bash
python run.py --web
```

### Console Mode
```bash
python run.py --console
python run.py --console 1000  # Run for 1000 steps
```

### Quick Test
```bash
python run.py --test
```

## Kitchen Layout (12x10)

```
    0   1   2   3   4   5   6   7   8   9  10  11
  +---+---+---+---+---+---+---+---+---+---+---+---+
0 |STR|STR|STR| . | . | . | . | . | . | . | . | . |
  +---+---+---+---+---+---+---+---+---+---+---+---+
1 |STR|STR|STR| . |CUT|CUT| . | . | . | . | . | . |
  +---+---+---+---+---+---+---+---+---+---+---+---+
2 |STR|STR|STR| . |CUT|CUT| . | . | . | . | . | . |
  +---+---+---+---+---+---+---+---+---+---+---+---+
3 | . | . | . | . | . | . | . |CTR|CTR| . | . | . |
  +---+---+---+---+---+---+---+---+---+---+---+---+
4 | . | . | . | . | . | . | . |CTR|CTR| . | . | . |
  +---+---+---+---+---+---+---+---+---+---+---+---+
5 | . | . | . | . | . | . | . | . | . | . | . | . |
  +---+---+---+---+---+---+---+---+---+---+---+---+
6 | . | . | . | . | . | . | . | . | . | . | . | . |
  +---+---+---+---+---+---+---+---+---+---+---+---+
7 |STV|STV|STV| . | . | . | . | . |OVN|OVN| . |SNK|
  +---+---+---+---+---+---+---+---+---+---+---+---+
8 | . | . | . | . | . | . | . | . | . | . | . | . |
  +---+---+---+---+---+---+---+---+---+---+---+---+
9 | . | . | . | . | . | . | . | . | . | . | . | . |
  +---+---+---+---+---+---+---+---+---+---+---+---+

STR = Storage    CUT = Cutting Board    CTR = Counter
STV = Stove      OVN = Oven             SNK = Sink
```

## Agents

### Head Chef
- Decomposes orders into subtasks
- Broadcasts tasks using Contract Net Protocol
- Evaluates bids and assigns tasks to best cook
- Monitors plate availability

### Line Cooks (4)
- BDI architecture for decision-making
- Bid score = distance × 0.3 + workload × 0.7
- Navigate using A* pathfinding
- Handle resource contention with queues

## Recipes

| Recipe | Subtasks | Time Limit |
|--------|----------|------------|
| Burger Meal | 5 | 50 |
| Pasta Dish | 6 | 60 |
| Pizza | 5 | 55 |
| Salad | 5 | 45 |
| Grilled Chicken | 7 | 70 |
| Baked Casserole | 6 | 65 |

## Win/Lose Conditions

- **WIN**: Complete 10 orders
- **LOSE**: Fail 3 orders (timeout)

## Project Structure

```
cooperative_kitchen/
├── model/
│   ├── kitchen_model.py
│   ├── resources.py
│   ├── recipes.py
│   └── orders.py
├── agents/
│   ├── head_chef.py
│   ├── line_cook.py
│   └── bdi_components.py
├── utils/
│   ├── constants.py
│   ├── pathfinding.py
│   └── logger.py
├── visualization/
│   ├── portrayal.py
│   └── server.py
├── run.py
├── run_simple.py
├── requirements.txt
└── README.md
```

## Logging

All simulation events are logged to `kitchen_simulation.log` and displayed in the console. Configure logging in `utils/logger.py`:

- `LOG_ORDERS`: Order events
- `LOG_HEAD_CHEF`: Head Chef actions
- `LOG_COOKS`: Cook actions
- `LOG_RESOURCES`: Resource events
- `LOG_MOVEMENT`: Detailed movement (disabled by default)
- `LOG_BDI`: BDI reasoning events
