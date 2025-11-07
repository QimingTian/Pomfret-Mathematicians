"""
Blueprint with responder paths overlay
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import os
from .blueprint import BlueprintDrawer


class BlueprintWithPaths(BlueprintDrawer):
    """Draw blueprint with responder paths"""
    
    def __init__(self, building, floor_num, results):
        super().__init__(building, floor_num)
        self.results = results
        self.colors = plt.cm.Set3(np.linspace(0, 1, 12))
    
    def draw_with_paths(self, save_path=None, show=False):
        """Draw blueprint with paths overlay"""
        # Create figure
        fig, ax = plt.subplots(figsize=(16, 12))
        
        # Blueprint background
        ax.set_facecolor('#F8F9FA')
        fig.patch.set_facecolor('white')
        
        # Get floor data
        floor_rooms = {rid: r for rid, r in self.building.rooms.items() 
                      if r.floor == self.floor_num}
        floor_exits = {eid: e for eid, e in self.building.exits.items() 
                      if e.get('floor', 1) == self.floor_num}
        floor_corridors = {cid: c for cid, c in self.building.corridors.items() 
                          if c.get('floor', 1) == self.floor_num}
        
        # Draw corridors
        for corridor_id, corridor in floor_corridors.items():
            self._draw_corridor(ax, corridor)
        
        # Draw rooms
        for room_id, room in floor_rooms.items():
            self._draw_room_blueprint(ax, room)
        
        # Draw exits
        for exit_id, exit_data in floor_exits.items():
            self._draw_exit_blueprint(ax, exit_data, exit_id)
        
        # === NEW: Draw responder paths ===
        self._draw_responder_paths(ax, floor_rooms, floor_exits)
        
        # Add grid
        ax.grid(True, alpha=0.2, linestyle='--', linewidth=0.5, color='gray')
        
        # Labels
        ax.set_xlabel('Distance (meters)', fontsize=11, fontweight='bold')
        ax.set_ylabel('Distance (meters)', fontsize=11, fontweight='bold')
        
        # Title
        title_text = f'{self.building.name}\nFloor {self.floor_num} - Sweep Paths'
        title_text += f'\nTotal Time: {self.results["total_time"]:.1f}s'
        
        ax.text(0.02, 0.98, title_text,
               transform=ax.transAxes,
               fontsize=13,
               fontweight='bold',
               verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='white', 
                        edgecolor='black', linewidth=2, alpha=0.95))
        
        # Path legend
        self._add_path_legend(ax)
        
        ax.set_aspect('equal')
        
        # Auto-adjust limits
        all_x = [room.position[0] for room in floor_rooms.values()]
        all_y = [room.position[1] for room in floor_rooms.values()]
        padding = 3
        if all_x and all_y:
            ax.set_xlim(min(all_x) - padding, max(all_x) + padding)
            ax.set_ylim(min(all_y) - padding, max(all_y) + padding)
        
        plt.tight_layout()
        
        if save_path:
            os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else '.', exist_ok=True)
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
            print(f"  ✓ Path blueprint saved: {save_path}")
        
        if show:
            plt.show()
        else:
            plt.close()
    
    def _draw_responder_paths(self, ax, floor_rooms, floor_exits):
        """Draw responder paths on top of blueprint"""
        for i, path_data in enumerate(self.results['responder_paths']):
            responder_id = path_data['responder_id']
            path = path_data['path']
            
            # Get positions for path nodes
            positions = []
            for loc_id in path:
                if loc_id in self.building.rooms:
                    room = self.building.rooms[loc_id]
                    if room.floor == self.floor_num:
                        positions.append(room.position)
                elif loc_id in self.building.exits:
                    exit_data = self.building.exits[loc_id]
                    if exit_data.get('floor', 1) == self.floor_num:
                        positions.append(exit_data['position'])
                elif loc_id in self.building.corridors:
                    corridor = self.building.corridors[loc_id]
                    if corridor.get('floor', 1) == self.floor_num:
                        start = np.array(corridor['start'])
                        end = np.array(corridor['end'])
                        positions.append(tuple((start + end) / 2))
            
            if len(positions) >= 2:
                xs, ys = zip(*positions)
                color = self.colors[i % len(self.colors)]
                
                # Draw path line (thicker, on top)
                ax.plot(xs, ys, '-', color=color, linewidth=3.5, 
                       alpha=0.8, zorder=20,
                       label=f'Responder {responder_id} ({path_data["total_time"]:.1f}s)')
                
                # Draw markers at each position
                ax.plot(xs, ys, 'o', color=color, markersize=10, 
                       markeredgecolor='white', markeredgewidth=2,
                       alpha=0.9, zorder=21)
                
                # Add numbered markers
                for j, (x, y) in enumerate(positions):
                    ax.text(x, y, str(j), 
                           ha='center', va='center',
                           fontsize=8, fontweight='bold',
                           color='white',
                           zorder=22)
                
                # Add arrows to show direction
                for j in range(len(positions)-1):
                    dx = xs[j+1] - xs[j]
                    dy = ys[j+1] - ys[j]
                    length = np.sqrt(dx**2 + dy**2)
                    if length > 0.5:  # Only add arrow if segment is long enough
                        mid_x = (xs[j] + xs[j+1]) / 2
                        mid_y = (ys[j] + ys[j+1]) / 2
                        ax.arrow(mid_x - dx*0.15, mid_y - dy*0.15, 
                               dx*0.3, dy*0.3,
                               head_width=0.4, head_length=0.3,
                               fc=color, ec=color, alpha=0.7,
                               zorder=20)
    
    def _add_path_legend(self, ax):
        """Add legend for paths"""
        # Get unique responders on this floor
        responders_on_floor = set()
        for path_data in self.results['responder_paths']:
            for loc_id in path_data['path']:
                if loc_id in self.building.rooms:
                    if self.building.rooms[loc_id].floor == self.floor_num:
                        responders_on_floor.add(path_data['responder_id'])
                        break
        
        ax.legend(loc='lower right', fontsize=9, framealpha=0.95, 
                 edgecolor='black', title='Responder Paths')


def generate_paths_on_blueprints():
    """Generate path visualizations on blueprints for all scenarios"""
    import sys
    sys.path.insert(0, '.')
    from src.models.building import Building
    from src.algorithms.smart_optimizer import SmartOptimizer
    from src.algorithms.simulator import Simulator
    import json
    
    scenarios = [
        ('data/scenarios/scenario1_basic.json', 'data/results/scenario1'),
        ('data/scenarios/scenario2_three_floors.json', 'data/results/scenario2'),
        ('data/scenarios/scenario3_school.json', 'data/results/scenario3')
    ]
    
    for scenario_file, output_dir in scenarios:
        # Load and run
        building = Building.from_json(scenario_file)
        with open(scenario_file) as f:
            data = json.load(f)
        n_responders = data['responders']['count']
        
        print(f"\n{building.name}:")
        
        optimizer = SmartOptimizer(building, n_responders=n_responders)
        assignment = optimizer.optimize()
        team = optimizer.get_team()
        results = Simulator.run_quick(building, team, assignment)
        
        # Generate path blueprints for each floor
        for floor in range(1, building.n_floors + 1):
            drawer = BlueprintWithPaths(building, floor, results)
            if building.n_floors == 1:
                save_path = os.path.join(output_dir, '2_paths.png')
            else:
                save_path = os.path.join(output_dir, f'2_paths_floor_{floor}.png')
            drawer.draw_with_paths(save_path=save_path)
    
    print("\n✓ All path blueprints generated!")


if __name__ == '__main__':
    generate_paths_on_blueprints()

