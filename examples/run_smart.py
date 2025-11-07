#!/usr/bin/env python3
"""
Run all scenarios with smart strategy selection
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Set matplotlib to non-interactive backend
import matplotlib
matplotlib.use('Agg')

from src.models.building import Building
from src.algorithms.smart_optimizer import SmartOptimizer
from src.algorithms.simulator import Simulator
from src.visualization.plotter import Plotter
from src.utils.helpers import export_results_json, print_results_summary
import matplotlib.pyplot as plt
import json


def run_scenario_smart(scenario_file, output_dir, scenario_name):
    """Run a single scenario with smart strategy selection"""
    print(f"\n{'='*70}")
    print(f"{scenario_name}")
    print('='*70)
    
    # Load building
    building = Building.from_json(scenario_file)
    print(f"Building: {building}")
    
    # Get responder count from scenario file
    with open(scenario_file) as f:
        data = json.load(f)
    n_responders = data['responders']['count']
    
    # Use Smart Optimizer
    print(f"\nAnalyzing building characteristics...")
    optimizer = SmartOptimizer(building, n_responders=n_responders)
    
    # Print strategy selection analysis
    optimizer.print_analysis()
    
    # Optimize
    assignment = optimizer.optimize()
    
    print("Assignment:")
    for responder_id, rooms in assignment.items():
        print(f"  Responder {responder_id}: {rooms[:5]}{'...' if len(rooms) > 5 else ''} ({len(rooms)} rooms)")
    
    # Simulate
    team = optimizer.get_team()
    results = Simulator.run_quick(building, team, assignment)
    
    # Add strategy info to results
    results['strategy_used'] = optimizer.selected_strategy
    results['strategy_analysis'] = optimizer.get_analysis()
    
    # Print summary
    print_results_summary(results)
    
    # Save results
    os.makedirs(output_dir, exist_ok=True)
    export_results_json(results, os.path.join(output_dir, 'results.json'))
    
    # Visualize
    plotter = Plotter(building, results)
    plotter.save_all(output_dir)
    
    return results


def compare_scenarios(all_results, scenario_names):
    """Create comparison plots"""
    print("\n" + "="*70)
    print("COMPARISON ACROSS SCENARIOS")
    print("="*70)
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    display_names = ['Scenario 1\nBasic Office', 'Scenario 2\n3-Floor Office', 'Scenario 3\nSchool']
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
    
    # 1. Total time comparison
    ax = axes[0, 0]
    times = [r['total_time'] for r in all_results]
    bars = ax.bar(display_names, times, color=colors)
    ax.set_ylabel('Total Time (seconds)', fontsize=11)
    ax.set_title('Total Sweep Time', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')
    
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
               f'{height:.0f}s',
               ha='center', va='bottom', fontsize=10)
    
    # 2. Strategy used
    ax = axes[0, 1]
    strategies = [r['strategy_used'] for r in all_results]
    strategy_colors = {'balanced': '#FFB347', 'priority': '#98D8C8', 'nearest': '#F7DC6F'}
    bars = ax.bar(display_names, [1, 1, 1], color=[strategy_colors.get(s, '#95a5a6') for s in strategies])
    ax.set_ylim(0, 1.5)
    ax.set_yticks([])
    ax.set_title('Strategy Selected', fontsize=12, fontweight='bold')
    
    for i, (bar, strategy) in enumerate(zip(bars, strategies)):
        ax.text(bar.get_x() + bar.get_width()/2., 0.5,
               strategy.upper(),
               ha='center', va='center', fontsize=11, fontweight='bold')
    
    # 3. Efficiency comparison
    ax = axes[1, 0]
    n_rooms = [r['metrics']['n_rooms'] for r in all_results]
    efficiency = [n / t for n, t in zip(n_rooms, times)]
    bars = ax.bar(display_names, efficiency, color=colors)
    ax.set_ylabel('Rooms per Second', fontsize=11)
    ax.set_title('Efficiency', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')
    
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
               f'{height:.2f}',
               ha='center', va='bottom', fontsize=10)
    
    # 4. Priority rooms handled
    ax = axes[1, 1]
    high_priority = [r['strategy_analysis']['stats']['high_priority_rooms'] for r in all_results]
    critical = [r['strategy_analysis']['stats']['critical_rooms'] for r in all_results]
    
    x = range(len(display_names))
    width = 0.35
    bars1 = ax.bar([i - width/2 for i in x], high_priority, width, label='High Priority', color='#F39C12')
    bars2 = ax.bar([i + width/2 for i in x], critical, width, label='Critical', color='#E74C3C')
    
    ax.set_ylabel('Number of Rooms', fontsize=11)
    ax.set_title('Priority Room Distribution', fontsize=12, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(display_names)
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    os.makedirs('data/results', exist_ok=True)
    plt.savefig('data/results/smart_comparison.png', dpi=300, bbox_inches='tight')
    print("\n✓ Comparison plot saved to: data/results/smart_comparison.png")
    plt.close()
    
    # Print comparison table
    print("\n" + "="*70)
    print("COMPARISON TABLE")
    print("="*70)
    print(f"{'Metric':<35} {'Scenario 1':<15} {'Scenario 2':<15} {'Scenario 3':<15}")
    print("-" * 70)
    
    metrics_to_compare = [
        ('Building Type', None),
        ('Total Rooms', 'n_rooms'),
        ('Floors', None),
        ('Responders', 'n_responders'),
        ('High Priority Rooms', None),
        ('Critical Rooms', None),
        ('Strategy Used', None),
        ('Total Time (s)', None),
        ('Avg Clearance (s)', 'average_clearance_time'),
        ('Load Balance', 'load_balance'),
        ('Efficiency (rooms/s)', None)
    ]
    
    for metric_name, metric_key in metrics_to_compare:
        values = []
        for i, r in enumerate(all_results):
            if metric_name == 'Building Type':
                types = ['Basic Office', '3-Floor Office', 'School']
                values.append(types[i])
            elif metric_name == 'Floors':
                floors = [1, 3, 2]
                values.append(str(floors[i]))
            elif metric_name == 'High Priority Rooms':
                val = r['strategy_analysis']['stats']['high_priority_rooms']
                values.append(str(val))
            elif metric_name == 'Critical Rooms':
                val = r['strategy_analysis']['stats']['critical_rooms']
                values.append(str(val))
            elif metric_name == 'Strategy Used':
                values.append(r['strategy_used'])
            elif metric_name == 'Efficiency (rooms/s)':
                eff = r['metrics']['n_rooms'] / r['total_time']
                values.append(f"{eff:.2f}")
            elif metric_key is None:
                values.append(f"{r['total_time']:.0f}")
            else:
                val = r['metrics'][metric_key]
                if isinstance(val, float):
                    values.append(f"{val:.2f}")
                else:
                    values.append(str(val))
        
        print(f"{metric_name:<35} {values[0]:<15} {values[1]:<15} {values[2]:<15}")
    
    print("="*70)


def main():
    print("="*70)
    print("SMART OPTIMIZER - AUTOMATIC STRATEGY SELECTION")
    print("="*70)
    
    scenarios = [
        ('data/scenarios/scenario1_basic.json', 'data/results/scenario1', 'SCENARIO 1: Basic Office Building'),
        ('data/scenarios/scenario2_three_floors.json', 'data/results/scenario2', 'SCENARIO 2: Three-Floor Office'),
        ('data/scenarios/scenario3_school.json', 'data/results/scenario3', 'SCENARIO 3: Elementary School')
    ]
    
    all_results = []
    
    for scenario_file, output_dir, scenario_name in scenarios:
        results = run_scenario_smart(scenario_file, output_dir, scenario_name)
        all_results.append(results)
    
    # Compare scenarios
    compare_scenarios(all_results, [s[2] for s in scenarios])
    
    print("\n" + "="*70)
    print("ALL SCENARIOS COMPLETE!")
    print("="*70)
    print("\nResults saved to:")
    for _, output_dir, _ in scenarios:
        print(f"  - {output_dir}/")
    print("  - data/results/smart_comparison.png")
    
    print("\n" + "="*70)
    print("STRATEGY SUMMARY")
    print("="*70)
    for i, (scenario_file, _, scenario_name) in enumerate(scenarios, 1):
        strategy = all_results[i-1]['strategy_used']
        time = all_results[i-1]['total_time']
        print(f"Scenario {i}: {strategy.upper()} strategy → {time:.0f}s")
    print("="*70)


if __name__ == '__main__':
    main()

