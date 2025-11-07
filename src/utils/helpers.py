"""
Helper functions for the project
"""

import json
import csv
import os
from typing import Dict


def export_results_json(results: Dict, filepath: str):
    """
    Export results to JSON file
    
    Args:
        results: Results dictionary
        filepath: Output file path
    """
    os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
    
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Results exported to {filepath}")


def export_results_csv(results: Dict, filepath: str):
    """
    Export results to CSV file
    
    Args:
        results: Results dictionary
        filepath: Output file path
    """
    os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
    
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Write header
        writer.writerow(['Metric', 'Value'])
        
        # Write metrics
        writer.writerow(['Total Time (s)', results['total_time']])
        writer.writerow(['All Rooms Cleared', results['success']])
        
        for key, value in results['metrics'].items():
            writer.writerow([key, value])
            
        # Write responder summary
        writer.writerow([])
        writer.writerow(['Responder ID', 'Total Time', 'Rooms Checked', 'Distance Traveled'])
        
        for path_data in results['responder_paths']:
            writer.writerow([
                path_data['responder_id'],
                path_data['total_time'],
                len(path_data['rooms_checked']),
                path_data.get('total_distance', 0)
            ])
            
    print(f"Results exported to {filepath}")


def print_results_summary(results: Dict):
    """
    Print results summary to console
    
    Args:
        results: Results dictionary
    """
    print("\n" + "="*60)
    print("SWEEP SIMULATION RESULTS")
    print("="*60)
    
    print(f"\nTotal Time: {results['total_time']:.2f} seconds")
    print(f"All Rooms Cleared: {'Yes' if results['success'] else 'No'}")
    
    print("\nRespunder Performance:")
    print("-" * 60)
    for path_data in results['responder_paths']:
        print(f"  Responder {path_data['responder_id']}:")
        print(f"    Time: {path_data['total_time']:.2f}s")
        print(f"    Rooms: {', '.join(path_data['rooms_checked'])}")
        print(f"    Distance: {path_data.get('total_distance', 0):.1f}m")
    
    print("\nMetrics:")
    print("-" * 60)
    metrics = results['metrics']
    print(f"  Average Clearance Time: {metrics['average_clearance_time']:.2f}s")
    print(f"  Load Balance: {metrics['load_balance']:.2%}")
    print(f"  Redundancy Coverage: {metrics['redundancy_coverage']:.2%}")
    print(f"  Total Distance: {metrics['total_distance_traveled']:.1f}m")
    
    print("="*60 + "\n")

