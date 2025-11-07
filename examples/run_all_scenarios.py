#!/usr/bin/env python3
"""
Run all three scenarios and compare results
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.models.building import Building
from src.algorithms.greedy import GreedyOptimizer
from src.algorithms.genetic import GeneticOptimizer
from src.algorithms.simulator import Simulator
from src.visualization.plotter import Plotter
from src.utils.helpers import export_results_json, print_results_summary
import matplotlib.pyplot as plt


def run_scenario(scenario_file, output_dir, use_genetic=False):
    """Run a single scenario"""
    print(f"\n{'='*70}")
    print(f"Running: {scenario_file}")
    print('='*70)
    
    # Load building
    building = Building.from_json(scenario_file)
    print(f"Building: {building}")
    
    # Get responder count from scenario file
    import json
    with open(scenario_file) as f:
        data = json.load(f)
    n_responders = data['responders']['count']
    
    # Optimize
    if use_genetic:
        print(f"Using Genetic Algorithm (this may take a minute)...")
        optimizer = GeneticOptimizer(
            building, 
            n_responders=n_responders,
            population_size=30,
            generations=50
        )
    else:
        print(f"Using Greedy Algorithm (balanced strategy)...")
        optimizer = GreedyOptimizer(building, n_responders=n_responders, strategy='balanced')
    
    assignment = optimizer.optimize()
    
    # Simulate
    team = optimizer.get_team()
    results = Simulator.run_quick(building, team, assignment)
    
    # Print summary
    print_results_summary(results)
    
    # Save results
    os.makedirs(output_dir, exist_ok=True)
    export_results_json(results, os.path.join(output_dir, 'results.json'))
    
    # Visualize
    plotter = Plotter(building, results)
    plotter.save_all(output_dir)
    
    return results


def compare_scenarios(all_results):
    """Create comparison plots"""
    print("\n" + "="*70)
    print("COMPARISON ACROSS SCENARIOS")
    print("="*70)
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    scenario_names = ['Scenario 1\n(Basic)', 'Scenario 2\n(3 Floors)', 'Scenario 3\n(Daycare)']
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
    
    # Total time comparison
    ax = axes[0]
    times = [r['total_time'] for r in all_results]
    bars = ax.bar(scenario_names, times, color=colors)
    ax.set_ylabel('Total Time (seconds)', fontsize=11)
    ax.set_title('Total Sweep Time', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
               f'{height:.1f}s',
               ha='center', va='bottom', fontsize=10)
    
    # Efficiency comparison (rooms per second)
    ax = axes[1]
    n_rooms = [r['metrics']['n_rooms'] for r in all_results]
    efficiency = [n / t for n, t in zip(n_rooms, times)]
    bars = ax.bar(scenario_names, efficiency, color=colors)
    ax.set_ylabel('Rooms per Second', fontsize=11)
    ax.set_title('Efficiency', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')
    
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
               f'{height:.2f}',
               ha='center', va='bottom', fontsize=10)
    
    # Load balance comparison
    ax = axes[2]
    load_balance = [r['metrics']['load_balance'] for r in all_results]
    bars = ax.bar(scenario_names, load_balance, color=colors)
    ax.set_ylabel('Load Balance (0-1)', fontsize=11)
    ax.set_title('Load Balance', fontsize=12, fontweight='bold')
    ax.set_ylim(0, 1.1)
    ax.grid(True, alpha=0.3, axis='y')
    
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
               f'{height:.2f}',
               ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    plt.savefig('data/results/comparison.png', dpi=300, bbox_inches='tight')
    print("\n✓ Comparison plot saved to: data/results/comparison.png")
    plt.show()
    
    # Print comparison table
    print("\nComparison Table:")
    print("-" * 70)
    print(f"{'Metric':<30} {'Scenario 1':<15} {'Scenario 2':<15} {'Scenario 3':<15}")
    print("-" * 70)
    
    metrics_to_compare = [
        ('Rooms', 'n_rooms'),
        ('Responders', 'n_responders'),
        ('Total Time (s)', None),
        ('Avg Clearance (s)', 'average_clearance_time'),
        ('Load Balance', 'load_balance'),
        ('Total Distance (m)', 'total_distance_traveled')
    ]
    
    for metric_name, metric_key in metrics_to_compare:
        values = []
        for r in all_results:
            if metric_key is None:
                values.append(f"{r['total_time']:.2f}")
            else:
                val = r['metrics'][metric_key]
                if isinstance(val, float):
                    values.append(f"{val:.2f}")
                else:
                    values.append(str(val))
        
        print(f"{metric_name:<30} {values[0]:<15} {values[1]:<15} {values[2]:<15}")
    
    print("-" * 70)


def main():
    print("="*70)
    print("RUNNING ALL THREE SCENARIOS")
    print("="*70)
    
    scenarios = [
        ('data/scenarios/scenario1_basic.json', 'data/results/scenario1'),
        ('data/scenarios/scenario2_three_floors.json', 'data/results/scenario2'),
        ('data/scenarios/scenario3_daycare.json', 'data/results/scenario3')
    ]
    
    all_results = []
    
    for scenario_file, output_dir in scenarios:
        results = run_scenario(scenario_file, output_dir, use_genetic=False)
        all_results.append(results)
    
    # Compare scenarios
    compare_scenarios(all_results)
    
    print("\n" + "="*70)
    print("ALL SCENARIOS COMPLETE!")
    print("="*70)
    print("\nResults saved to:")
    for _, output_dir in scenarios:
        print(f"  - {output_dir}/")


if __name__ == '__main__':
    main()

