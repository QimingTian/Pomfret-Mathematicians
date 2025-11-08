# Emergency Evacuation Sweep Optimization Model

**HiMCM 2025 Problem A Solution**

A mathematical model to optimize emergency sweeping strategies in multi-story buildings during evacuations, minimizing the time required to clear all rooms while prioritizing safety and efficiency.

## 🚀 Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Run the Model

```bash
python3 examples/test_top_down.py
```

This will:
- Generate optimized sweep paths for all 3 scenarios
- Create professional blueprints with navigation nodes
- Produce individual path visualizations for each responder
- Save all results to `data/results/`

## 📁 Project Structure

```
HiMCM/
├── data/
│   ├── scenarios/              # Building scenario definitions (JSON)
│   │   ├── scenario1_basic.json           # Single-floor office (6 rooms, 2 responders)
│   │   ├── scenario2_three_floors.json    # 3-floor office (24 rooms, 3 responders)
│   │   └── scenario3_school.json          # 2-floor school (16 rooms, 3 responders)
│   └── results/                # Generated visualizations (PNG)
│       ├── scenario1/          # 3 files: 1 structure + 2 responder paths
│       ├── scenario2/          # 15 files: 3 structures + 12 responder paths
│       └── scenario3/          # 11 files: 2 structures + 9 responder paths
│
├── examples/
│   └── test_top_down.py       # Main execution script
│
├── src/
│   ├── algorithms/            # Optimization algorithms
│   │   ├── greedy.py         # Three greedy strategies
│   │   ├── genetic.py        # Genetic algorithm
│   │   ├── smart_optimizer.py     # Auto strategy selection
│   │   ├── top_down_optimizer.py  # Top-down multi-floor sweep
│   │   └── node_simulator.py      # Realistic path simulation
│   │
│   ├── models/               # Data structures
│   │   ├── building.py       # Building model (rooms, corridors, exits, stairs)
│   │   ├── node_based_building.py # Graph with navigation nodes
│   │   ├── responder.py      # Responder team with capabilities
│   │   └── graph.py          # Graph utilities (Dijkstra, etc.)
│   │
│   ├── visualization/        # Blueprint generation
│   │   └── blueprint.py      # Professional architectural diagrams
│   │
│   └── utils/
│       └── helpers.py        # Utility functions
│
├── README.md
├── requirements.txt          # Python dependencies
├── modeling_framework.md     # Mathematical framework
├── input_output_design.md    # I/O specifications
├── problem_analysis.md       # Problem breakdown
└── 2025_HiMCM_Problem_A.pdf # Original problem statement
```

## 🎯 Key Features

### Optimization Algorithms
- **Greedy Strategies**: Nearest First, Priority First, Balanced
- **Genetic Algorithm**: For complex optimization
- **Smart Optimizer**: Automatically selects best strategy based on building characteristics
- **Top-Down Sweep**: Multi-floor buildings swept from top to bottom

### Realistic Modeling
- **Node-Based Navigation**: Paths follow doors, corridors, and stairs (no wall penetration)
- **Detailed Timing**: Accounts for walking speed, stair traversal, and room checking
- **Multi-Floor Support**: Vertical movement through stairwells
- **Room Priorities**: Critical rooms (classrooms, offices with occupants) checked first

### Professional Visualizations
- **Blueprint Diagrams**: Walls, doors, dimensions, room labels
- **Navigation Nodes**: Shows all pathfinding nodes (room centers, doors, corridor points, stairs, exits)
- **Path Arrows**: Directional arrows showing responder movement
- **Separate Responder Paths**: Each responder's path on individual diagrams for clarity

## 📊 Three Scenarios

### Scenario 1: Basic Office Building
- **Layout**: 1 floor, 6 rooms, 1 corridor, 2 exits
- **Responders**: 2
- **Strategy**: Balanced distribution
- **Time**: ~97 seconds

### Scenario 2: Three-Floor Office Building
- **Layout**: 3 floors, 24 rooms, 2 stairwells
- **Responders**: 3
- **Strategy**: Top-down sweep
- **Time**: ~374 seconds

### Scenario 3: Elementary School
- **Layout**: 2 floors, 16 rooms (classrooms, offices, restrooms)
- **Responders**: 3
- **Strategy**: Top-down with priority
- **Time**: ~712 seconds

## 📈 Output Files

Each scenario generates:

1. **Structure Diagram**: `1_structure_with_nodes[_floor_X].png`
   - Shows building layout with walls, doors, and rooms
   - Displays all navigation nodes (color-coded by type)
   - Includes dimensions and room labels

2. **Path Diagrams**: `2_paths[_floor_X]_responder_Y.png`
   - One diagram per responder showing their complete route
   - Directional arrows indicate movement
   - Room visit order numbered
   - Time annotation

## 🔧 Key Assumptions

- Firefighters walk at **1.79 m/s** (wearing full gear)
- Stair climbing: **0.4 m/s** up, **0.7 m/s** down
- Room check time: **1.0 s/m²** + 10s base time
- All responders start/end at building exits
- No dynamic hazards or obstructions

## 📝 Documentation

- `modeling_framework.md`: Mathematical model, equations, algorithms
- `input_output_design.md`: JSON schema, data structures, output format
- `problem_analysis.md`: Problem breakdown and approach

## 💡 Usage Example

```python
from src.models.building import Building
from src.models.node_based_building import NodeBasedBuilding
from src.algorithms.top_down_optimizer import TopDownOptimizer
from src.algorithms.node_simulator import NodeSimulator

# Load building
building = Building.from_json('data/scenarios/scenario1_basic.json')
node_building = NodeBasedBuilding(building)

# Optimize
optimizer = TopDownOptimizer(building, n_responders=2)
assignment = optimizer.optimize()

# Simulate
team = optimizer.get_team()
results = NodeSimulator.run_quick(building, node_building, team, assignment)

print(f"Total time: {results['total_time']:.1f}s")
print(f"All rooms cleared: {results['success']}")
```

## 🧪 Verification

The model has been tested on all three scenarios:
- All rooms successfully cleared
- Paths are physically valid (no wall penetration)
- Times are realistic based on walking speeds and distances
- Multi-floor navigation works correctly

## 👥 Authors

HiMCM 2025 Team

## 📄 License

Educational use for HiMCM competition
