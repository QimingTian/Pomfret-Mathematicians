#!/usr/bin/env python3
"""
Simple runner - only generate structure and path visualizations
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import matplotlib
matplotlib.use('Agg')

from src.models.building import Building
from src.algorithms.smart_optimizer import SmartOptimizer
from src.algorithms.simulator import Simulator
from src.visualization.blueprint import BlueprintDrawer
from src.visualization.plotter import Plotter


def run_scenario(scenario_file, output_dir):
    """Run scenario and generate only 2 visualizations"""
    import json
    
    # Load building
    building = Building.from_json(scenario_file)
    
    # Get responder count
    with open(scenario_file) as f:
        data = json.load(f)
    n_responders = data['responders']['count']
    
    print(f"\n{building.name}")
    print(f"  Rooms: {len(building.rooms)}, Floors: {building.n_floors}, Responders: {n_responders}")
    
    # 1. Generate structure blueprints
    print(f"  Generating blueprints...")
    for floor in range(1, building.n_floors + 1):
        drawer = BlueprintDrawer(building, floor)
        if building.n_floors == 1:
            save_path = os.path.join(output_dir, '1_structure.png')
        else:
            save_path = os.path.join(output_dir, f'1_structure_floor_{floor}.png')
        drawer.draw_blueprint(save_path=save_path)
    
    # 2. Run optimization
    optimizer = SmartOptimizer(building, n_responders=n_responders)
    assignment = optimizer.optimize()
    
    # 3. Simulate
    team = optimizer.get_team()
    results = Simulator.run_quick(building, team, assignment)
    
    print(f"  Strategy: {optimizer.selected_strategy.upper()}")
    print(f"  Total Time: {results['total_time']:.1f}s")
    
    # 4. Generate path visualization
    print(f"  Generating path visualization...")
    plotter = Plotter(building, results)
    if building.n_floors == 1:
        save_path = os.path.join(output_dir, '2_paths.png')
    else:
        save_path = os.path.join(output_dir, '2_paths_all_floors.png')
    plotter.plot_paths(save_path=save_path, show=False)
    
    return results


def main():
    print("="*60)
    print("SIMPLE OUTPUT - Structure + Paths Only")
    print("="*60)
    
    scenarios = [
        ('data/scenarios/scenario1_basic.json', 'data/results/scenario1'),
        ('data/scenarios/scenario2_three_floors.json', 'data/results/scenario2'),
        ('data/scenarios/scenario3_school.json', 'data/results/scenario3')
    ]
    
    for scenario_file, output_dir in scenarios:
        run_scenario(scenario_file, output_dir)
    
    print("\n" + "="*60)
    print("COMPLETE!")
    print("="*60)
    print("\nGenerated files:")
    print("  Scenario 1:")
    print("    - data/results/scenario1/1_structure.png")
    print("    - data/results/scenario1/2_paths.png")
    print("  Scenario 2:")
    print("    - data/results/scenario2/1_structure_floor_1.png")
    print("    - data/results/scenario2/1_structure_floor_2.png")
    print("    - data/results/scenario2/1_structure_floor_3.png")
    print("    - data/results/scenario2/2_paths_all_floors.png")
    print("  Scenario 3:")
    print("    - data/results/scenario3/1_structure_floor_1.png")
    print("    - data/results/scenario3/1_structure_floor_2.png")
    print("    - data/results/scenario3/2_paths_all_floors.png")


if __name__ == '__main__':
    main()

