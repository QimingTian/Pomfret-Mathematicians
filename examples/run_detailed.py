#!/usr/bin/env python3
"""
Run with detailed path tracking (through doors and corridors)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

from src.models.building_v2 import BuildingWithDoors
from src.algorithms.detailed_optimizer import DetailedOptimizer
from src.algorithms.detailed_simulator import DetailedSimulator


def draw_detailed_blueprint_with_paths(building, results, floor_num, save_path):
    """Draw blueprint with accurate paths through doors and corridors"""
    fig, ax = plt.subplots(figsize=(16, 12))
    ax.set_facecolor('#F8F9FA')
    
    wall_thickness = 0.2
    door_width = 1.0
    
    # Get floor data
    floor_rooms = {rid: r for rid, r in building.rooms.items() if r.floor == floor_num}
    floor_exits = {eid: e for eid, e in building.exits.items() if e.get('floor', 1) == floor_num}
    floor_corridors = {cid: c for cid, c in building.corridors.items() if c.get('floor', 1) == floor_num}
    
    # Draw corridors
    for corridor in floor_corridors.values():
        start = np.array(corridor['start'])
        end = np.array(corridor['end'])
        width = corridor.get('width', 2)
        
        direction = end - start
        length = np.linalg.norm(direction)
        if length > 0:
            direction = direction / length
            perpendicular = np.array([-direction[1], direction[0]])
            
            corners = [
                start - perpendicular * width/2,
                start + perpendicular * width/2,
                end + perpendicular * width/2,
                end - perpendicular * width/2
            ]
            
            poly = patches.Polygon(corners, facecolor='#E8E8E8', 
                                 edgecolor='#666666', linewidth=1.5,
                                 linestyle='--', alpha=0.5, zorder=1)
            ax.add_patch(poly)
    
    # Draw rooms
    for room in floor_rooms.values():
        x, y = room.position
        size = np.sqrt(room.area)
        
        # Walls
        outer_rect = patches.Rectangle(
            (x - size/2, y - size/2), size, size,
            linewidth=3, edgecolor='#2C3E50',
            facecolor='white', zorder=3)
        ax.add_patch(outer_rect)
        
        # Fill
        color = '#E74C3C' if room.priority >= 3 else ('#F39C12' if room.priority >= 2 else '#3498DB')
        inner_rect = patches.Rectangle(
            (x - size/2 + wall_thickness, y - size/2 + wall_thickness),
            size - 2*wall_thickness, size - 2*wall_thickness,
            linewidth=0, facecolor=color, alpha=0.25, zorder=3)
        ax.add_patch(inner_rect)
        
        # Door (automatically toward corridor)
        door_id = f"{room.id}_door"
        if door_id in building.doors and building.doors[door_id]['position']:
            door_pos = building.doors[door_id]['position']
            # Draw door opening
            dx = door_pos[0] - x
            dy = door_pos[1] - y
            
            if abs(dx) > abs(dy):  # Door on left/right
                ax.plot([door_pos[0], door_pos[0]], 
                       [door_pos[1] - door_width/2, door_pos[1] + door_width/2],
                       color='white', linewidth=5, zorder=4)
            else:  # Door on top/bottom
                ax.plot([door_pos[0] - door_width/2, door_pos[0] + door_width/2],
                       [door_pos[1], door_pos[1]],
                       color='white', linewidth=5, zorder=4)
        
        # Labels
        ax.text(x, y, room.id, ha='center', va='center',
               fontsize=10, fontweight='bold', color='#2C3E50', zorder=5)
        ax.text(x, y - size/3, f'{room.area}m²', ha='center', va='center',
               fontsize=7, color='#666', zorder=5)
    
    # Draw exits (simple text label only)
    for exit_id, exit_data in floor_exits.items():
        x, y = exit_data['position']
        # Simple EXIT label with background
        ax.text(x, y, f'EXIT\n{exit_id}', ha='center', va='center',
               fontsize=11, fontweight='bold', color='#27AE60',
               bbox=dict(boxstyle='round,pad=0.5', facecolor='white', 
                        edgecolor='#27AE60', linewidth=2, alpha=0.9),
               zorder=10)
    
    # === Draw detailed paths ===
    colors = plt.cm.Set3(np.linspace(0, 1, 12))
    
    for i, path_data in enumerate(results['responder_paths']):
        if 'detailed_positions' in path_data and len(path_data['detailed_positions']) > 0:
            positions = path_data['detailed_positions']
            
            # Filter positions on this floor
            floor_positions = []
            for j, pos in enumerate(positions):
                node_id = path_data['detailed_path'][j]
                if node_id in building.rooms:
                    if building.rooms[node_id].floor == floor_num:
                        floor_positions.append(pos)
                elif node_id in building.exits:
                    if building.exits[node_id].get('floor', 1) == floor_num:
                        floor_positions.append(pos)
                elif node_id in building.doors:
                    if building.doors[node_id]['floor'] == floor_num:
                        floor_positions.append(pos)
                else:
                    # Corridor or other node - check if on floor
                    floor_positions.append(pos)
            
            if len(floor_positions) >= 2:
                xs, ys = zip(*floor_positions)
                color = colors[i % len(colors)]
                
                # Draw smooth path
                ax.plot(xs, ys, '-', color=color, linewidth=3.5, 
                       alpha=0.85, zorder=20,
                       label=f'Responder {path_data["responder_id"]}: {path_data["total_time"]:.1f}s')
                
                # Mark key points (rooms only)
                room_positions = [(x, y) for x, y, node in zip(xs, ys, path_data['detailed_path']) 
                                 if node in building.rooms]
                if room_positions:
                    rx, ry = zip(*room_positions)
                    ax.plot(rx, ry, 'o', color=color, markersize=11, 
                           markeredgecolor='white', markeredgewidth=2.5,
                           alpha=0.95, zorder=21)
    
    # Finalize
    ax.legend(loc='lower right', fontsize=10, framealpha=0.95, 
             edgecolor='black', title='Sweep Paths')
    ax.set_xlabel('Distance (meters)', fontsize=11, fontweight='bold')
    ax.set_ylabel('Distance (meters)', fontsize=11, fontweight='bold')
    ax.grid(True, alpha=0.2, linestyle='--', linewidth=0.5, color='gray')
    ax.set_aspect('equal')
    
    title_text = f'{building.name}\nFloor {floor_num} - Sweep Paths (Total: {results["total_time"]:.1f}s)'
    ax.text(0.02, 0.98, title_text, transform=ax.transAxes,
           fontsize=13, fontweight='bold', verticalalignment='top',
           bbox=dict(boxstyle='round', facecolor='white', 
                    edgecolor='black', linewidth=2, alpha=0.95))
    
    if floor_rooms:
        all_x = [room.position[0] for room in floor_rooms.values()]
        all_y = [room.position[1] for room in floor_rooms.values()]
        padding = 3
        ax.set_xlim(min(all_x) - padding, max(all_x) + padding)
        ax.set_ylim(min(all_y) - padding, max(all_y) + padding)
    
    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else '.', exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  ✓ Detailed path saved: {save_path}")


def main():
    print("="*70)
    print("DETAILED PATH SIMULATION - No Wall Penetration")
    print("="*70)
    
    # Test with Scenario 1
    print("\nScenario 1: Basic Office Building")
    building = BuildingWithDoors.from_json('data/scenarios/scenario1_basic.json')
    print(f"  Building: {building}")
    print(f"  Doors created: {len(building.doors)}")
    
    # Optimize with detailed optimizer
    optimizer = DetailedOptimizer(building, n_responders=2, strategy='balanced')
    assignment = optimizer.optimize()
    team = optimizer.get_team()
    
    print(f"  Assignment: {assignment}")
    
    # Simulate with detailed paths
    results = DetailedSimulator.run_quick(building, team, assignment)
    
    print(f"  Total time: {results['total_time']:.1f}s")
    print(f"  All rooms cleared: {results['success']}")
    
    # Generate visualization
    os.makedirs('data/results/scenario1', exist_ok=True)
    draw_detailed_blueprint_with_paths(building, results, 1, 
                                      'data/results/scenario1/3_detailed_paths.png')
    
    print("\n✓ Complete!")
    print("  Check: data/results/scenario1/3_detailed_paths.png")


if __name__ == '__main__':
    main()

