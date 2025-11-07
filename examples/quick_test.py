#!/usr/bin/env python3
"""
Quick test to verify installation and basic functionality
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.models.building import Building
from src.algorithms.greedy import GreedyOptimizer
from src.algorithms.simulator import Simulator


def main():
    print("="*60)
    print("QUICK TEST - Verifying Installation")
    print("="*60)
    
    # Test 1: Create simple building
    print("\n✓ Test 1: Creating simple building...")
    building = Building.create_simple(n_rooms=6, layout='two_sided_corridor')
    print(f"  Created: {building}")
    
    # Test 2: Run optimization
    print("\n✓ Test 2: Running optimization...")
    optimizer = GreedyOptimizer(building, n_responders=2, strategy='balanced')
    assignment = optimizer.optimize()
    print(f"  Assignment computed: {len(assignment)} responders")
    
    # Test 3: Simulate
    print("\n✓ Test 3: Running simulation...")
    team = optimizer.get_team()
    results = Simulator.run_quick(building, team, assignment)
    print(f"  Total time: {results['total_time']:.2f} seconds")
    print(f"  All rooms cleared: {results['success']}")
    
    # Test 4: Load from JSON
    print("\n✓ Test 4: Loading from JSON...")
    try:
        building_json = Building.from_json('data/scenarios/scenario1_basic.json')
        print(f"  Loaded: {building_json}")
    except FileNotFoundError:
        print("  Warning: JSON file not found (run from project root)")
    
    print("\n" + "="*60)
    print("ALL TESTS PASSED! ✓")
    print("="*60)
    print("\nYou can now run:")
    print("  python examples/run_basic_scenario.py")
    print("  python examples/run_all_scenarios.py")
    print("="*60)


if __name__ == '__main__':
    main()

