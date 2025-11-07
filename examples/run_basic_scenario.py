#!/usr/bin/env python3
"""
Run basic scenario (Scenario 1: 6 rooms, 2 responders)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.models.building import Building
from src.algorithms.greedy import GreedyOptimizer
from src.algorithms.simulator import Simulator
from src.visualization.plotter import Plotter
from src.utils.helpers import export_results_json, print_results_summary


def main():
    print("="*70)
    print("SCENARIO 1: Basic Office Building (6 rooms, 2 responders)")
    print("="*70)
    
    # Load building from JSON
    print("\n1. Loading building...")
    building = Building.from_json('data/scenarios/scenario1_basic.json')
    print(f"   Loaded: {building}")
    
    # Run greedy optimization
    print("\n2. Running greedy optimization...")
    optimizer = GreedyOptimizer(building, n_responders=2, strategy='balanced')
    assignment = optimizer.optimize()
    
    print("   Assignment:")
    for responder_id, rooms in assignment.items():
        print(f"     Responder {responder_id}: {rooms}")
    
    # Simulate
    print("\n3. Running simulation...")
    team = optimizer.get_team()
    results = Simulator.run_quick(building, team, assignment)
    
    # Print results
    print_results_summary(results)
    
    # Export results
    print("\n4. Exporting results...")
    os.makedirs('data/results/scenario1', exist_ok=True)
    export_results_json(results, 'data/results/scenario1/results.json')
    
    # Visualize
    print("\n5. Creating visualizations...")
    plotter = Plotter(building, results)
    plotter.save_all('data/results/scenario1')
    
    print("\n✓ Scenario 1 complete!")
    print(f"  Total time: {results['total_time']:.2f} seconds")
    print(f"  Results saved to: data/results/scenario1/")
    
    # Show plots
    print("\n6. Displaying plots...")
    plotter.plot_paths()
    plotter.plot_gantt()
    plotter.plot_metrics()


if __name__ == '__main__':
    main()

