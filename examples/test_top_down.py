#!/usr/bin/env python3
"""
Test top-down sweep strategy with arrows on paths
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyArrowPatch
import numpy as np
import json

from src.models.building import Building
from src.models.node_based_building import NodeBasedBuilding
from src.algorithms.top_down_optimizer import TopDownOptimizer
from src.algorithms.node_simulator import NodeSimulator
from src.visualization.blueprint import BlueprintDrawer


def draw_structure_with_arrows(building, node_building, results, floor_num, save_path, responder_id=None):
    """Draw blueprint with paths that have directional arrows
    
    Args:
        responder_id: If specified, only draw this responder's path. If None, draw all.
    """
    fig, ax = plt.subplots(figsize=(16, 12))
    ax.set_facecolor('#F8F9FA')
    
    floor_rooms = {rid: r for rid, r in building.rooms.items() if r.floor == floor_num}
    floor_exits = {eid: e for eid, e in building.exits.items() if e.get('floor', 1) == floor_num}
    floor_corridors = {cid: c for cid, c in building.corridors.items() if c.get('floor', 1) == floor_num}
    floor_stairs = {sid: s for sid, s in building.stairs.items() if floor_num in s.get('connects', [])}
    
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
    
    # Draw rooms with walls and doors
    for room in floor_rooms.values():
        x, y = room.position
        size = 4.0
        
        rect = patches.Rectangle(
            (x - size/2, y - size/2), size, size,
            linewidth=3, edgecolor='#2C3E50',
            facecolor='white', zorder=3)
        ax.add_patch(rect)
        
        color = '#E74C3C' if room.priority >= 3 else ('#F39C12' if room.priority >= 2 else '#3498DB')
        inner_rect = patches.Rectangle(
            (x - size/2 + 0.2, y - size/2 + 0.2),
            size - 0.4, size - 0.4,
            linewidth=0, facecolor=color, alpha=0.25, zorder=3)
        ax.add_patch(inner_rect)
        
        # Door
        corridor = list(floor_corridors.values())[0] if floor_corridors else None
        if corridor:
            c_start = np.array(corridor['start'])
            c_end = np.array(corridor['end'])
            
            if abs(c_end[0] - c_start[0]) < 1:  # Vertical corridor
                corridor_x = c_start[0]
                if corridor_x > x:
                    door_pos = (x + size/2, y)
                    ax.plot([door_pos[0], door_pos[0]], [door_pos[1] - 0.5, door_pos[1] + 0.5],
                           color='white', linewidth=5, zorder=4)
                else:
                    door_pos = (x - size/2, y)
                    ax.plot([door_pos[0], door_pos[0]], [door_pos[1] - 0.5, door_pos[1] + 0.5],
                           color='white', linewidth=5, zorder=4)
        
        ax.text(x, y, room.id, ha='center', va='center',
               fontsize=10, fontweight='bold', color='#2C3E50', zorder=5)
        ax.text(x, y - size/3, f'{room.area}m²\nF{room.floor}', ha='center', va='center',
               fontsize=7, color='#666', zorder=5)
    
    # Draw stairs
    for stair_id, stair_data in floor_stairs.items():
        x, y = stair_data['position']
        stair_rect = patches.Rectangle(
            (x - 1, y - 1), 2, 2,
            linewidth=2.5, edgecolor='#8E44AD',
            facecolor='#D7BDE2', alpha=0.7, zorder=8)
        ax.add_patch(stair_rect)
        
        for i in range(6):
            y_step = y - 0.8 + i * 1.6 / 6
            ax.plot([x - 0.8, x + 0.8], [y_step, y_step],
                   color='#8E44AD', linewidth=1.5, alpha=0.8, zorder=9)
        
        connects_str = '-'.join(map(str, stair_data['connects']))
        ax.text(x, y, f'{stair_id.split("_")[-1]}\nF{connects_str}', 
               ha='center', va='center',
               fontsize=7, fontweight='bold', color='#8E44AD', zorder=10)
    
    # Draw exits
    for exit_id, exit_data in floor_exits.items():
        x, y = exit_data['position']
        ax.text(x, y, f'EXIT\n{exit_id}', ha='center', va='center',
               fontsize=11, fontweight='bold', color='#27AE60',
               bbox=dict(boxstyle='round,pad=0.5', facecolor='white', 
                        edgecolor='#27AE60', linewidth=2, alpha=0.9),
               zorder=10)
    
    # === Draw paths with arrows ===
    colors = plt.cm.Set3(np.linspace(0, 1, 12))
    
    # Filter responders to draw
    responder_paths_to_draw = results.get('responder_paths', [])
    if responder_id is not None:
        responder_paths_to_draw = [p for p in responder_paths_to_draw if p['responder_id'] == responder_id]
    
    for i, path_data in enumerate(responder_paths_to_draw):
        current_resp_id = path_data['responder_id']
        
        # Use detailed path from simulator
        if 'detailed_path_positions' in path_data and path_data['detailed_path_positions']:
            all_positions = path_data['detailed_path_positions']
            all_nodes = path_data.get('detailed_path_nodes', [])
            
            # Filter to current floor (include stairs on this floor)
            floor_positions = []
            floor_nodes = []
            
            for j, pos in enumerate(all_positions):
                if j < len(all_nodes):
                    node_id = all_nodes[j]
                    node_data = node_building.nodes.get(node_id, {})
                    
                    # Include if on current floor or is a stair node on current floor
                    if node_data.get('floor') == floor_num:
                        floor_positions.append(pos)
                        floor_nodes.append(node_id)
            
            if len(floor_positions) < 2:
                continue
            
        else:
            continue
        
        if len(floor_positions) >= 2:
            xs, ys = zip(*floor_positions)
            color = colors[(current_resp_id - 1) % len(colors)]
            
            # Draw path line (no offset)
            ax.plot(xs, ys, '-', color=color, linewidth=4, 
                   alpha=0.85, zorder=20)
            
            # Add arrows along path (every 4 segments)
            for j in range(2, len(xs)-1, 4):
                dx = xs[j+1] - xs[j]
                dy = ys[j+1] - ys[j]
                length = np.sqrt(dx**2 + dy**2)
                
                if length > 0.8:
                    mid_x = (xs[j] + xs[j+1]) / 2
                    mid_y = (ys[j] + ys[j+1]) / 2
                    
                    arrow = FancyArrowPatch(
                        (mid_x - dx*0.2, mid_y - dy*0.2),
                        (mid_x + dx*0.2, mid_y + dy*0.2),
                        arrowstyle='->', mutation_scale=20,
                        linewidth=2.5, color=color,
                        alpha=0.95, zorder=21
                    )
                    ax.add_patch(arrow)
            
            # Mark room centers
            room_positions = []
            for j, node_id in enumerate(floor_nodes):
                if '_center' in node_id:
                    room_positions.append(floor_positions[j])
            
            if room_positions:
                rx, ry = zip(*room_positions)
                ax.plot(rx, ry, 'o', color=color, markersize=14, 
                       markeredgecolor='white', markeredgewidth=2.5,
                       alpha=0.95, zorder=22)
                
                # Number the rooms
                for idx, (px, py) in enumerate(room_positions):
                    ax.text(px, py, str(idx+1), 
                           ha='center', va='center',
                           fontsize=9, fontweight='bold',
                           color='white', zorder=23)
            
            # Add to legend
            ax.plot([], [], '-', color=color, linewidth=4, 
                   label=f'R{current_resp_id} (F{floor_num}): {path_data["total_time"]:.1f}s')
    
    # Finalize
    ax.legend(loc='lower right', fontsize=9, framealpha=0.95, edgecolor='black',
             title=f'Floor {floor_num} Paths', title_fontsize=10)
    ax.set_xlabel('Distance (meters)', fontsize=11, fontweight='bold')
    ax.set_ylabel('Distance (meters)', fontsize=11, fontweight='bold')
    ax.grid(True, alpha=0.2, linestyle='--', linewidth=0.5)
    ax.set_aspect('equal')
    
    title = f'{building.name} - Floor {floor_num}\nTop-Down Sweep Strategy'
    ax.text(0.02, 0.98, title, transform=ax.transAxes,
           fontsize=13, fontweight='bold', verticalalignment='top',
           bbox=dict(boxstyle='round', facecolor='white', 
                    edgecolor='black', linewidth=2, alpha=0.95))
    
    if floor_rooms:
        all_x = [r.position[0] for r in floor_rooms.values()]
        all_y = [r.position[1] for r in floor_rooms.values()]
        padding = 3
        ax.set_xlim(min(all_x) - padding, max(all_x) + padding)
        ax.set_ylim(min(all_y) - padding, max(all_y) + padding)
    
    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else '.', exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()


def run_scenario(scenario_file, output_dir):
    """Run scenario with top-down strategy"""
    building = Building.from_json(scenario_file)
    
    with open(scenario_file) as f:
        data = json.load(f)
    n_responders = data['responders']['count']
    capabilities = data['responders'].get('capabilities', {})
    
    print(f"\n{'='*60}")
    print(f"{building.name}")
    print('='*60)
    print(f"  Floors: {building.n_floors}, Rooms: {len(building.rooms)}, Responders: {n_responders}")
    
    # Create node-based building
    node_building = NodeBasedBuilding(building)
    print(f"  Navigation nodes: {len(node_building.nodes)}")
    
    # Optimize with top-down strategy
    optimizer = TopDownOptimizer(building, n_responders=n_responders, capabilities=capabilities)
    assignment = optimizer.optimize()
    
    print(f"\n  Strategy: {optimizer.get_strategy_name().upper()}")
    print(f"  Assignment (top-down order):")
    for resp_id, rooms in assignment.items():
        if building.n_floors > 1:
            # Show floor distribution
            by_floor = {}
            for room_id in rooms:
                floor = building.rooms[room_id].floor
                if floor not in by_floor:
                    by_floor[floor] = []
                by_floor[floor].append(room_id)
            
            floor_str = ', '.join([f"F{f}:{len(by_floor[f])}rooms" for f in sorted(by_floor.keys(), reverse=True)])
            print(f"    Responder {resp_id}: {floor_str}")
        else:
            print(f"    Responder {resp_id}: {len(rooms)} rooms")
    
    # Simulate with node-based simulator
    team = optimizer.get_team()
    results = NodeSimulator.run_quick(building, node_building, team, assignment)
    
    print(f"\n  Total time: {results['total_time']:.1f}s")
    print(f"  All rooms cleared: {results['success']}")
    
    # Generate blueprints
    os.makedirs(output_dir, exist_ok=True)
    
    # Get number of responders
    num_responders = len(results.get('responder_paths', []))
    
    for floor in range(1, building.n_floors + 1):
        # Structure with nodes using BlueprintDrawer
        if building.n_floors == 1:
            structure_path = os.path.join(output_dir, '1_structure_with_nodes.png')
        else:
            structure_path = os.path.join(output_dir, f'1_structure_with_nodes_floor_{floor}.png')
        
        drawer = BlueprintDrawer(building, floor_num=floor, node_building=node_building)
        drawer.draw_blueprint(save_path=structure_path, show=False, show_nodes=True)
        
        # Generate path for each responder separately
        for resp_id in range(1, num_responders + 1):
            if building.n_floors == 1:
                paths_path = os.path.join(output_dir, f'2_paths_responder_{resp_id}.png')
            else:
                paths_path = os.path.join(output_dir, f'2_paths_floor_{floor}_responder_{resp_id}.png')
            
            draw_structure_with_arrows(building, node_building, results, floor, paths_path, responder_id=resp_id)
        
        print(f"  ✓ Floor {floor} blueprints saved")


def main():
    print("="*70)
    print("TOP-DOWN SWEEP STRATEGY - All Scenarios")
    print("="*70)
    print("\nStrategy:")
    print("  - Single floor: Balanced distribution")
    print("  - Multi-floor: Start from top, sweep downwards")
    print("  - Paths show arrows indicating movement direction")
    
    scenarios = [
        ('data/scenarios/scenario1_basic.json', 'data/results/scenario1'),
        ('data/scenarios/scenario2_three_floors.json', 'data/results/scenario2'),
        ('data/scenarios/scenario3_school.json', 'data/results/scenario3')
    ]
    
    for scenario_file, output_dir in scenarios:
        run_scenario(scenario_file, output_dir)
    
    print("\n" + "="*70)
    print("COMPLETE!")
    print("="*70)


if __name__ == '__main__':
    main()

