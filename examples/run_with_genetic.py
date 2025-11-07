#!/usr/bin/env python3
"""
Run scenario with genetic algorithm optimization
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.models.building import Building
from src.algorithms.greedy import GreedyOptimizer
from src.algorithms.genetic import GeneticOptimizer
from src.algorithms.simulator import Simulator
from src.visualization.plotter import Plotter
from src.utils.helpers import print_results_summary
import matplotlib.pyplot as plt


def main():
    print("="*70)
    print("GENETIC ALGORITHM vs GREEDY ALGORITHM")
    print("="*70)
    
    # Load building
    print("\n1. Loading building (Scenario 2: Three Floors)...")
    building = Building.from_json('data/scenarios/scenario2_three_floors.json')
    print(f"   {building}")
    
    # Run greedy
    print("\n2. Running Greedy Algorithm...")
    greedy_optimizer = GreedyOptimizer(building, n_responders=4, strategy='balanced')
    greedy_assignment = greedy_optimizer.optimize()
    greedy_team = greedy_optimizer.get_team()
    greedy_results = Simulator.run_quick(building, greedy_team, greedy_assignment)
    
    print(f"   Greedy Total Time: {greedy_results['total_time']:.2f} seconds")
    
    # Run genetic
    print("\n3. Running Genetic Algorithm (this may take a minute)...")
    genetic_optimizer = GeneticOptimizer(
        building, 
        n_responders=4,
        population_size=50,
        generations=100,
        mutation_rate=0.15,
        crossover_rate=0.8
    )
    genetic_assignment = genetic_optimizer.optimize()
    genetic_team = genetic_optimizer.get_team()
    genetic_results = Simulator.run_quick(building, genetic_team, genetic_assignment)
    
    print(f"   Genetic Total Time: {genetic_results['total_time']:.2f} seconds")
    
    # Compare
    improvement = ((greedy_results['total_time'] - genetic_results['total_time']) / 
                   greedy_results['total_time'] * 100)
    
    print("\n" + "="*70)
    print("COMPARISON")
    print("="*70)
    print(f"Greedy Algorithm:   {greedy_results['total_time']:.2f} seconds")
    print(f"Genetic Algorithm:  {genetic_results['total_time']:.2f} seconds")
    print(f"Improvement:        {improvement:+.2f}%")
    print("="*70)
    
    # Plot fitness history
    print("\n4. Plotting genetic algorithm convergence...")
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Fitness history
    ax = axes[0]
    fitness_history = genetic_optimizer.get_fitness_history()
    ax.plot(fitness_history, linewidth=2, color='#4ECDC4')
    ax.axhline(y=greedy_results['total_time'], color='r', linestyle='--', 
               linewidth=2, label=f'Greedy Solution ({greedy_results["total_time"]:.1f}s)')
    ax.set_xlabel('Generation', fontsize=11)
    ax.set_ylabel('Best Fitness (Total Time, s)', fontsize=11)
    ax.set_title('Genetic Algorithm Convergence', fontsize=12, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Bar comparison
    ax = axes[1]
    algorithms = ['Greedy', 'Genetic']
    times = [greedy_results['total_time'], genetic_results['total_time']]
    colors = ['#FF6B6B', '#4ECDC4']
    bars = ax.bar(algorithms, times, color=colors, width=0.6)
    ax.set_ylabel('Total Time (seconds)', fontsize=11)
    ax.set_title('Algorithm Comparison', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
               f'{height:.1f}s',
               ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('data/results/genetic_vs_greedy.png', dpi=300, bbox_inches='tight')
    print("   Saved to: data/results/genetic_vs_greedy.png")
    plt.show()
    
    # Show detailed results for genetic
    print("\n5. Detailed results for Genetic Algorithm:")
    print_results_summary(genetic_results)
    
    # Visualize genetic solution
    print("\n6. Creating visualizations...")
    os.makedirs('data/results/genetic', exist_ok=True)
    plotter = Plotter(building, genetic_results)
    plotter.save_all('data/results/genetic')
    plotter.plot_paths()
    plotter.plot_gantt()


if __name__ == '__main__':
    main()

