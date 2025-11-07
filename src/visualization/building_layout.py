"""
Building layout visualization - clean structure diagram only
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import os


def plot_building_structure(building, save_path=None, show=False):
    """
    Plot clean building structure without any paths
    
    Args:
        building: Building instance
        save_path: Path to save figure
        show: Whether to display
    """
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # Draw corridors first (as background)
    for corridor_id, corridor in building.corridors.items():
        start = np.array(corridor['start'])
        end = np.array(corridor['end'])
        width = corridor.get('width', 2)
        
        # Draw corridor as thick line
        ax.plot([start[0], end[0]], [start[1], end[1]], 
               color='lightgray', linewidth=width*5, solid_capstyle='round',
               alpha=0.8, zorder=1)
        
        # Label corridor
        mid = (start + end) / 2
        ax.text(mid[0], mid[1], corridor_id, 
               ha='center', va='center', fontsize=9, 
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.7),
               zorder=2)
    
    # Draw rooms
    for room_id, room in building.rooms.items():
        x, y = room.position
        
        # Determine room size (assume 4x4 for 16m² rooms)
        size = np.sqrt(room.area)
        
        # Color by priority
        if room.priority >= 3:
            color = '#E74C3C'  # Red - critical
            alpha = 0.7
        elif room.priority >= 2:
            color = '#F39C12'  # Orange - high priority
            alpha = 0.6
        else:
            color = '#3498DB'  # Blue - normal
            alpha = 0.5
        
        # Draw room rectangle
        rect = patches.Rectangle(
            (x - size/2, y - size/2), size, size,
            linewidth=2.5,
            edgecolor='black',
            facecolor=color,
            alpha=alpha,
            zorder=3
        )
        ax.add_patch(rect)
        
        # Room label
        ax.text(x, y, room_id, 
               ha='center', va='center', 
               fontsize=11, fontweight='bold',
               color='white',
               zorder=4)
        
        # Room info below
        info = f"{room.area}m²"
        if room.priority > 1:
            info += f"\nP{room.priority}"
        ax.text(x, y - size/2 - 1, info,
               ha='center', va='top',
               fontsize=8, color='gray',
               zorder=4)
    
    # Draw exits
    for exit_id, exit_data in building.exits.items():
        x, y = exit_data['position']
        
        # Draw exit as large green circle
        circle = patches.Circle(
            (x, y), 1.5,
            facecolor='#2ECC71',
            edgecolor='darkgreen',
            linewidth=2.5,
            zorder=5
        )
        ax.add_patch(circle)
        
        # Exit label
        ax.text(x, y, '🚪',
               ha='center', va='center',
               fontsize=16,
               zorder=6)
        ax.text(x, y - 3, exit_id,
               ha='center', va='top',
               fontsize=10, fontweight='bold',
               color='darkgreen',
               zorder=6)
    
    # Draw stairs (if any)
    for stair_id, stair_data in building.stairs.items():
        x, y = stair_data['position']
        
        # Draw stairs as purple square
        rect = patches.Rectangle(
            (x - 1.5, y - 1.5), 3, 3,
            facecolor='#9B59B6',
            edgecolor='purple',
            linewidth=2,
            zorder=5
        )
        ax.add_patch(rect)
        
        ax.text(x, y, '🪜',
               ha='center', va='center',
               fontsize=14,
               zorder=6)
    
    # Set axis properties
    ax.set_xlabel('X Position (meters)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Y Position (meters)', fontsize=12, fontweight='bold')
    ax.set_title(f'{building.name} - Floor Plan Structure\n{len(building.rooms)} Rooms, {building.n_floors} Floor(s)',
                fontsize=14, fontweight='bold', pad=20)
    
    # Add legend
    legend_elements = [
        patches.Patch(facecolor='#3498DB', alpha=0.5, edgecolor='black', label='Normal Priority'),
        patches.Patch(facecolor='#F39C12', alpha=0.6, edgecolor='black', label='High Priority'),
        patches.Patch(facecolor='#E74C3C', alpha=0.7, edgecolor='black', label='Critical Priority'),
        patches.Circle((0, 0), 0.5, facecolor='#2ECC71', edgecolor='darkgreen', label='Exit'),
        patches.Rectangle((0, 0), 1, 1, facecolor='lightgray', alpha=0.8, label='Corridor')
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=10, framealpha=0.9)
    
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_aspect('equal')
    
    # Auto-adjust limits with padding
    all_x = [room.position[0] for room in building.rooms.values()]
    all_y = [room.position[1] for room in building.rooms.values()]
    all_x.extend([exit_data['position'][0] for exit_data in building.exits.values()])
    all_y.extend([exit_data['position'][1] for exit_data in building.exits.values()])
    
    padding = 5
    ax.set_xlim(min(all_x) - padding, max(all_x) + padding)
    ax.set_ylim(min(all_y) - padding, max(all_y) + padding)
    
    plt.tight_layout()
    
    if save_path:
        os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else '.', exist_ok=True)
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✓ Building structure saved to: {save_path}")
    
    if show:
        plt.show()
    else:
        plt.close()


def plot_all_scenarios_structure():
    """Plot structure for all scenarios"""
    import sys
    sys.path.insert(0, '.')
    from src.models.building import Building
    
    scenarios = [
        ('data/scenarios/scenario1_basic.json', 'data/results/scenario1/structure.png', 'Scenario 1'),
        ('data/scenarios/scenario2_three_floors.json', 'data/results/scenario2/structure.png', 'Scenario 2'),
        ('data/scenarios/scenario3_school.json', 'data/results/scenario3/structure.png', 'Scenario 3')
    ]
    
    for scenario_file, output_file, name in scenarios:
        print(f"\nGenerating structure for {name}...")
        building = Building.from_json(scenario_file)
        plot_building_structure(building, save_path=output_file)
    
    print("\n✓ All building structures generated!")


if __name__ == '__main__':
    plot_all_scenarios_structure()

