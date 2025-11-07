"""
Generate separate floor plan for each floor in multi-story buildings
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import os


def plot_single_floor(building, floor_num, ax):
    """
    Plot a single floor
    
    Args:
        building: Building instance
        floor_num: Floor number to plot
        ax: Matplotlib axis
    """
    # Get rooms on this floor
    floor_rooms = {rid: r for rid, r in building.rooms.items() if r.floor == floor_num}
    
    if not floor_rooms:
        ax.text(0.5, 0.5, f'Floor {floor_num}\n(No rooms)', 
               ha='center', va='center', fontsize=14, transform=ax.transAxes)
        return
    
    # Get corridors on this floor
    floor_corridors = {cid: c for cid, c in building.corridors.items() if c.get('floor', 1) == floor_num}
    
    # Get exits on this floor
    floor_exits = {eid: e for eid, e in building.exits.items() if e.get('floor', 1) == floor_num}
    
    # Get stairs on this floor
    floor_stairs = {sid: s for sid, s in building.stairs.items() 
                    if floor_num in s.get('connects', [])}
    
    # Draw corridors
    for corridor_id, corridor in floor_corridors.items():
        start = np.array(corridor['start'])
        end = np.array(corridor['end'])
        width = corridor.get('width', 2)
        
        ax.plot([start[0], end[0]], [start[1], end[1]], 
               color='lightgray', linewidth=width*5, solid_capstyle='round',
               alpha=0.8, zorder=1, label='Corridor' if corridor_id == list(floor_corridors.keys())[0] else '')
        
        mid = (start + end) / 2
        ax.text(mid[0], mid[1], corridor_id, 
               ha='center', va='center', fontsize=8, 
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.7),
               zorder=2)
    
    # Draw rooms
    for room_id, room in floor_rooms.items():
        x, y = room.position
        size = np.sqrt(room.area)
        
        # Color by priority
        if room.priority >= 3:
            color = '#E74C3C'
            alpha = 0.7
        elif room.priority >= 2:
            color = '#F39C12'
            alpha = 0.6
        else:
            color = '#3498DB'
            alpha = 0.5
        
        rect = patches.Rectangle(
            (x - size/2, y - size/2), size, size,
            linewidth=2,
            edgecolor='black',
            facecolor=color,
            alpha=alpha,
            zorder=3
        )
        ax.add_patch(rect)
        
        # Room label
        ax.text(x, y, room_id, 
               ha='center', va='center', 
               fontsize=9, fontweight='bold',
               color='white',
               zorder=4)
        
        # Room type and size
        info = f"{room.type}\n{room.area}m²"
        if room.priority > 1:
            info += f"\nP{room.priority}"
        ax.text(x, y - size/2 - 0.8, info,
               ha='center', va='top',
               fontsize=7, color='gray',
               zorder=4)
    
    # Draw exits
    for exit_id, exit_data in floor_exits.items():
        x, y = exit_data['position']
        
        circle = patches.Circle(
            (x, y), 1.5,
            facecolor='#2ECC71',
            edgecolor='darkgreen',
            linewidth=2,
            zorder=5
        )
        ax.add_patch(circle)
        
        ax.text(x, y, 'EXIT',
               ha='center', va='center',
               fontsize=8, fontweight='bold',
               color='white',
               zorder=6)
        ax.text(x, y - 2.5, exit_id,
               ha='center', va='top',
               fontsize=9, fontweight='bold',
               color='darkgreen',
               zorder=6)
    
    # Draw stairs
    for stair_id, stair_data in floor_stairs.items():
        x, y = stair_data['position']
        
        rect = patches.Rectangle(
            (x - 1.5, y - 1.5), 3, 3,
            facecolor='#9B59B6',
            edgecolor='purple',
            linewidth=2,
            zorder=5
        )
        ax.add_patch(rect)
        
        ax.text(x, y, 'STAIRS',
               ha='center', va='center',
               fontsize=7, fontweight='bold',
               color='white',
               zorder=6)
        
        connects_str = ','.join(map(str, stair_data['connects']))
        ax.text(x, y - 2.5, f"{stair_id}\n(F{connects_str})",
               ha='center', va='top',
               fontsize=7,
               color='purple',
               zorder=6)
    
    # Set title
    ax.set_title(f'Floor {floor_num}', fontsize=12, fontweight='bold', pad=10)
    ax.set_xlabel('X (meters)', fontsize=10)
    ax.set_ylabel('Y (meters)', fontsize=10)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_aspect('equal')
    
    # Auto-adjust limits
    all_x = [room.position[0] for room in floor_rooms.values()]
    all_y = [room.position[1] for room in floor_rooms.values()]
    all_x.extend([e['position'][0] for e in floor_exits.values()])
    all_y.extend([e['position'][1] for e in floor_exits.values()])
    
    if all_x and all_y:
        padding = 5
        ax.set_xlim(min(all_x) - padding, max(all_x) + padding)
        ax.set_ylim(min(all_y) - padding, max(all_y) + padding)


def plot_building_by_floors(building, save_dir):
    """
    Generate floor plans for each floor
    
    Args:
        building: Building instance
        save_dir: Directory to save floor plans
    """
    os.makedirs(save_dir, exist_ok=True)
    
    if building.n_floors == 1:
        # Single floor - one image
        fig, ax = plt.subplots(figsize=(12, 10))
        plot_single_floor(building, 1, ax)
        
        # Add legend
        legend_elements = [
            patches.Patch(facecolor='#3498DB', alpha=0.5, edgecolor='black', label='Normal Priority'),
            patches.Patch(facecolor='#F39C12', alpha=0.6, edgecolor='black', label='High Priority'),
            patches.Patch(facecolor='#E74C3C', alpha=0.7, edgecolor='black', label='Critical Priority'),
            patches.Circle((0, 0), 0.5, facecolor='#2ECC71', edgecolor='darkgreen', label='Exit'),
            patches.Patch(facecolor='lightgray', alpha=0.8, label='Corridor')
        ]
        ax.legend(handles=legend_elements, loc='upper right', fontsize=9)
        
        fig.suptitle(f'{building.name} - Floor Plan', fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        save_path = os.path.join(save_dir, 'floor_plan.png')
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✓ Floor plan saved: {save_path}")
        
    else:
        # Multi-floor - separate images for each floor
        for floor in range(1, building.n_floors + 1):
            fig, ax = plt.subplots(figsize=(12, 10))
            plot_single_floor(building, floor, ax)
            
            # Add legend
            legend_elements = [
                patches.Patch(facecolor='#3498DB', alpha=0.5, edgecolor='black', label='Normal'),
                patches.Patch(facecolor='#F39C12', alpha=0.6, edgecolor='black', label='High Priority'),
                patches.Patch(facecolor='#E74C3C', alpha=0.7, edgecolor='black', label='Critical'),
                patches.Circle((0, 0), 0.5, facecolor='#2ECC71', edgecolor='darkgreen', label='Exit'),
                patches.Rectangle((0, 0), 1, 1, facecolor='#9B59B6', edgecolor='purple', label='Stairs')
            ]
            ax.legend(handles=legend_elements, loc='upper right', fontsize=9)
            
            fig.suptitle(f'{building.name} - Floor {floor}', fontsize=14, fontweight='bold')
            plt.tight_layout()
            
            save_path = os.path.join(save_dir, f'floor_{floor}_plan.png')
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
            print(f"  ✓ Floor {floor} plan saved: {save_path}")


def generate_all_floor_plans():
    """Generate floor plans for all scenarios"""
    import sys
    sys.path.insert(0, '.')
    from src.models.building import Building
    
    scenarios = [
        ('data/scenarios/scenario1_basic.json', 'data/results/scenario1', 'Scenario 1'),
        ('data/scenarios/scenario2_three_floors.json', 'data/results/scenario2', 'Scenario 2'),
        ('data/scenarios/scenario3_school.json', 'data/results/scenario3', 'Scenario 3')
    ]
    
    for scenario_file, output_dir, name in scenarios:
        print(f"\n{name}:")
        building = Building.from_json(scenario_file)
        print(f"  Building: {building.name} ({building.n_floors} floor(s))")
        plot_building_by_floors(building, output_dir)
    
    print("\n✓ All floor plans generated!")


if __name__ == '__main__':
    generate_all_floor_plans()

