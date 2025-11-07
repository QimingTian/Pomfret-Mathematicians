# Emergency Evacuation Sweep Optimization Model

**2025 HiMCM Problem A Solution**

A mathematical model to optimize sweeping strategies in multi-floor buildings during emergency evacuations.

## 🚀 Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### Run Basic Scenario

```bash
# Run the basic 6-room scenario
python examples/run_basic_scenario.py

# Run all three scenarios
python examples/run_all_scenarios.py

# Run with visualization
python examples/run_with_visualization.py
```

## 📁 Project Structure

```
HiMCM/
├── src/
│   ├── models/           # Core data structures
│   │   ├── building.py   # Building and room classes
│   │   ├── responder.py  # Responder class
│   │   └── graph.py      # Graph representation
│   ├── algorithms/       # Optimization algorithms
│   │   ├── greedy.py     # Greedy algorithm
│   │   ├── genetic.py    # Genetic algorithm
│   │   └── simulator.py  # Simulation engine
│   ├── visualization/    # Visualization tools
│   │   ├── plotter.py    # Static plots
│   │   └── animator.py   # Animation generator
│   └── utils/           # Utility functions
│       └── helpers.py    # Helper functions
├── data/
│   ├── scenarios/       # Input data (JSON)
│   └── results/         # Output results
├── examples/            # Example scripts
└── tests/              # Unit tests
```

## 💡 Usage Examples

### Example 1: Basic Scenario

```python
from src.models.building import Building
from src.algorithms.greedy import GreedyOptimizer
from src.algorithms.simulator import Simulator

# Load building
building = Building.from_json('data/scenarios/scenario1_basic.json')

# Optimize
optimizer = GreedyOptimizer(building, n_responders=2)
assignment = optimizer.optimize()

# Simulate
simulator = Simulator(building, assignment)
results = simulator.run()

print(f"Total time: {results['total_time']:.2f} seconds")
```

### Example 2: Custom Building

```python
from src.models.building import Building

# Create building programmatically
building = Building.create_simple(
    n_rooms=6,
    layout='two_sided_corridor',
    room_size=16,
    corridor_length=30
)

building.add_exit('E1', position=[0, 15])
building.add_exit('E2', position=[30, 15])

# Continue with optimization...
```

### Example 3: With Visualization

```python
from src.visualization.plotter import Plotter

# After running simulation
plotter = Plotter(building, results)
plotter.plot_paths()
plotter.plot_gantt()
plotter.plot_metrics()
plotter.save_all('data/results/')
```

## 🎯 Key Features

- ✅ Multiple optimization algorithms (Greedy, Genetic Algorithm)
- ✅ Realistic simulation with time-varying hazards
- ✅ Support for multi-floor buildings
- ✅ Room priority and occupancy modeling
- ✅ Interactive visualizations
- ✅ Comprehensive performance metrics
- ✅ Export results to JSON/CSV

## 📊 Three Scenarios

1. **Scenario 1: Basic Office Building**
   - 1 floor, 6 rooms, 2 responders
   - Two-sided corridor layout

2. **Scenario 2: Three-Floor Office**
   - 3 floors, 30 rooms, 4 responders
   - Multiple stairs, fire spread simulation

3. **Scenario 3: Daycare Center**
   - 1 floor, 8 rooms, 3 responders
   - High priority rooms, extended check time

## 🔧 Configuration

Edit scenario files in `data/scenarios/` to customize:
- Building layout
- Number of responders
- Room properties
- Emergency parameters

## 📈 Output

The model generates:
- **JSON/CSV files**: Detailed results
- **Path visualization**: Responder routes
- **Gantt charts**: Timeline analysis
- **Performance metrics**: Time, efficiency, load balance
- **Animations**: Step-by-step simulation (optional)

## 🧪 Testing

```bash
# Run tests
python -m pytest tests/

# Run specific test
python tests/test_basic_scenario.py
```

## 📝 Authors

HiMCM 2025 Team

## 📄 License

Educational use for HiMCM competition

