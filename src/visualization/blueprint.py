"""
Professional architectural blueprint visualization
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import os


class BlueprintDrawer:
    """Draw professional architectural blueprints"""
    
    def __init__(self, building, floor_num=1):
        self.building = building
        self.floor_num = floor_num
        self.wall_thickness = 0.2  # meters
        self.door_width = 1.0      # meters
        
    def draw_blueprint(self, save_path=None, show=False):
        """Generate professional blueprint"""
        # Create figure with blueprint style
        fig, ax = plt.subplots(figsize=(16, 12))
        
        # Blueprint background
        ax.set_facecolor('#F8F9FA')  # Light gray background
        fig.patch.set_facecolor('white')
        
        # Get floor data
        floor_rooms = {rid: r for rid, r in self.building.rooms.items() 
                      if r.floor == self.floor_num}
        floor_exits = {eid: e for eid, e in self.building.exits.items() 
                      if e.get('floor', 1) == self.floor_num}
        floor_corridors = {cid: c for cid, c in self.building.corridors.items() 
                          if c.get('floor', 1) == self.floor_num}
        
        if not floor_rooms:
            ax.text(0.5, 0.5, f'Floor {self.floor_num}\nNo rooms', 
                   ha='center', va='center', fontsize=16, transform=ax.transAxes)
            return
        
        # Draw corridors first (as floor area)
        for corridor_id, corridor in floor_corridors.items():
            self._draw_corridor(ax, corridor)
        
        # Draw rooms with walls and doors
        for room_id, room in floor_rooms.items():
            self._draw_room_blueprint(ax, room)
        
        # Draw exits
        for exit_id, exit_data in floor_exits.items():
            self._draw_exit_blueprint(ax, exit_data, exit_id)
        
        # Draw stairs on this floor
        for stair_id, stair_data in self.building.stairs.items():
            if self.floor_num in stair_data.get('connects', []):
                self._draw_stair_blueprint(ax, stair_data, stair_id)
        
        # Add dimension lines
        self._add_dimensions(ax, floor_rooms)
        
        # Add grid
        ax.grid(True, alpha=0.2, linestyle='--', linewidth=0.5, color='gray')
        
        # Set professional labels
        ax.set_xlabel('Distance (meters)', fontsize=11, fontweight='bold')
        ax.set_ylabel('Distance (meters)', fontsize=11, fontweight='bold')
        
        # Title block (like real blueprints)
        title_text = f'{self.building.name}\nFloor {self.floor_num} Plan'
        if self.building.n_floors > 1:
            title_text += f'\n({len(floor_rooms)} Rooms)'
        
        ax.text(0.02, 0.98, title_text,
               transform=ax.transAxes,
               fontsize=14,
               fontweight='bold',
               verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='white', 
                        edgecolor='black', linewidth=2, alpha=0.9))
        
        # Scale indicator
        scale_text = 'SCALE: 1:100\nUNITS: METERS'
        ax.text(0.98, 0.02, scale_text,
               transform=ax.transAxes,
               fontsize=9,
               horizontalalignment='right',
               verticalalignment='bottom',
               bbox=dict(boxstyle='round', facecolor='white', 
                        edgecolor='black', linewidth=1.5, alpha=0.9))
        
        # Legend
        self._add_legend(ax)
        
        ax.set_aspect('equal')
        
        # Auto-adjust limits
        all_x = [room.position[0] for room in floor_rooms.values()]
        all_y = [room.position[1] for room in floor_rooms.values()]
        padding = 8
        ax.set_xlim(min(all_x) - padding, max(all_x) + padding)
        ax.set_ylim(min(all_y) - padding, max(all_y) + padding)
        
        plt.tight_layout()
        
        if save_path:
            os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else '.', exist_ok=True)
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
            print(f"  ✓ Blueprint saved: {save_path}")
        
        if show:
            plt.show()
        else:
            plt.close()
    
    def _draw_corridor(self, ax, corridor):
        """Draw corridor as floor area"""
        start = np.array(corridor['start'])
        end = np.array(corridor['end'])
        width = corridor.get('width', 2)
        
        # Calculate perpendicular direction
        direction = end - start
        length = np.linalg.norm(direction)
        if length > 0:
            direction = direction / length
            perpendicular = np.array([-direction[1], direction[0]])
            
            # Create corridor rectangle
            corners = [
                start - perpendicular * width/2,
                start + perpendicular * width/2,
                end + perpendicular * width/2,
                end - perpendicular * width/2
            ]
            
            # Draw corridor floor
            poly = patches.Polygon(corners, 
                                 facecolor='#E8E8E8', 
                                 edgecolor='#666666',
                                 linewidth=1.5,
                                 linestyle='--',
                                 alpha=0.5,
                                 zorder=1)
            ax.add_patch(poly)
            
            # Label
            mid = (start + end) / 2
            ax.text(mid[0], mid[1], corridor['id'],
                   ha='center', va='center',
                   fontsize=9, fontstyle='italic',
                   color='#666666',
                   bbox=dict(boxstyle='round', facecolor='white', 
                            edgecolor='none', alpha=0.7),
                   zorder=2)
    
    def _draw_room_blueprint(self, ax, room):
        """Draw room with walls, door toward corridor, and annotations"""
        x, y = room.position
        # Use FIXED display size for uniform layout (actual area shown in label)
        size = 4.0  # All rooms displayed as 4x4 squares
        
        # Determine door position based on corridor location
        door_side = self._determine_door_side(room)
        
        # Room walls (thicker lines)
        wall_color = '#2C3E50'
        
        # Outer walls
        outer_rect = patches.Rectangle(
            (x - size/2, y - size/2), size, size,
            linewidth=3,
            edgecolor=wall_color,
            facecolor='white',
            zorder=3
        )
        ax.add_patch(outer_rect)
        
        # Inner walls (wall thickness)
        inner_rect = patches.Rectangle(
            (x - size/2 + self.wall_thickness, 
             y - size/2 + self.wall_thickness),
            size - 2*self.wall_thickness,
            size - 2*self.wall_thickness,
            linewidth=0,
            facecolor=self._get_room_color(room),
            alpha=0.3,
            zorder=3
        )
        ax.add_patch(inner_rect)
        
        # Draw door based on determined side
        self._draw_door(ax, x, y, size, door_side)
        
        # Room label
        ax.text(x, y + size/6, room.id,
               ha='center', va='center',
               fontsize=11, fontweight='bold',
               color='#2C3E50',
               zorder=5)
        
        # Room type
        ax.text(x, y, room.type.replace('_', ' ').title(),
               ha='center', va='center',
               fontsize=8,
               color='#555555',
               zorder=5)
        
        # Room area
        ax.text(x, y - size/6, f'{room.area} m²',
               ha='center', va='center',
               fontsize=8,
               color='#555555',
               bbox=dict(boxstyle='round', facecolor='white', 
                        edgecolor='none', alpha=0.7),
               zorder=5)
        
        # Priority indicator
        if room.priority >= 2:
            priority_text = '⚠' if room.priority == 2 else '⚠⚠'
            ax.text(x + size/2 - 0.5, y + size/2 - 0.5, priority_text,
                   ha='center', va='center',
                   fontsize=12, color='red',
                   zorder=6)
    
    def _draw_exit_blueprint(self, ax, exit_data, exit_id):
        """Draw exit with simple text label"""
        x, y = exit_data['position']
        
        # Simple EXIT label
        ax.text(x, y, f'EXIT\n{exit_id}',
               ha='center', va='center',
               fontsize=11, fontweight='bold',
               color='#27AE60',
               bbox=dict(boxstyle='round,pad=0.5', facecolor='white', 
                        edgecolor='#27AE60', linewidth=2, alpha=0.9),
               zorder=10)
    
    def _draw_stair_blueprint(self, ax, stair_data, stair_id):
        """Draw stairwell"""
        x, y = stair_data['position']
        
        # Stairwell box (2x2 meters)
        stair_rect = patches.Rectangle(
            (x - 1, y - 1), 2, 2,
            linewidth=2.5,
            edgecolor='#8E44AD',
            facecolor='#D7BDE2',
            alpha=0.7,
            zorder=8
        )
        ax.add_patch(stair_rect)
        
        # Stair lines (diagonal lines to represent steps)
        n_steps = 6
        for i in range(n_steps):
            y_step = y - 0.8 + i * 1.6 / n_steps
            ax.plot([x - 0.8, x + 0.8], [y_step, y_step],
                   color='#8E44AD', linewidth=1.5, alpha=0.8, zorder=9)
        
        # Label
        connects_str = '-'.join(map(str, stair_data['connects']))
        ax.text(x, y + 0.3, stair_id,
               ha='center', va='center',
               fontsize=8, fontweight='bold',
               color='#8E44AD',
               zorder=10)
        ax.text(x, y - 0.3, f'F{connects_str}',
               ha='center', va='center',
               fontsize=7,
               color='#8E44AD',
               zorder=10)
    
    def _determine_door_side(self, room):
        """Determine which side the door should be on (toward corridor)"""
        # Get corridors on this floor
        floor_corridors = {cid: c for cid, c in self.building.corridors.items() 
                          if c.get('floor', 1) == room.floor}
        
        if not floor_corridors:
            return 'right'  # Default
        
        # Find nearest corridor
        min_dist = float('inf')
        best_side = 'right'
        
        x, y = room.position
        
        for corridor in floor_corridors.values():
            c_start = np.array(corridor['start'])
            c_end = np.array(corridor['end'])
            c_mid = (c_start + c_end) / 2
            
            # Determine if corridor is horizontal or vertical
            if abs(c_end[0] - c_start[0]) < 1:  # Vertical corridor
                corridor_x = c_start[0]
                if abs(corridor_x - x) < min_dist:
                    min_dist = abs(corridor_x - x)
                    best_side = 'right' if corridor_x > x else 'left'
            else:  # Horizontal corridor
                corridor_y = c_start[1]
                if abs(corridor_y - y) < min_dist:
                    min_dist = abs(corridor_y - y)
                    best_side = 'bottom' if corridor_y < y else 'top'
        
        return best_side
    
    def _draw_door(self, ax, x, y, size, door_side):
        """Draw door on specified side"""
        if door_side == 'right':
            door_x = x + size/2
            door_y = y - self.door_width/2
            ax.plot([door_x, door_x], [door_y, door_y + self.door_width],
                   color='white', linewidth=5, zorder=4, solid_capstyle='butt')
            door_arc = patches.Arc(
                (door_x, door_y), self.door_width * 1.5, self.door_width * 1.5,
                angle=90, theta1=0, theta2=90,
                color='#3498DB', linewidth=1.5, linestyle='--', zorder=4)
        elif door_side == 'left':
            door_x = x - size/2
            door_y = y - self.door_width/2
            ax.plot([door_x, door_x], [door_y, door_y + self.door_width],
                   color='white', linewidth=5, zorder=4, solid_capstyle='butt')
            door_arc = patches.Arc(
                (door_x, door_y + self.door_width), self.door_width * 1.5, self.door_width * 1.5,
                angle=270, theta1=0, theta2=90,
                color='#3498DB', linewidth=1.5, linestyle='--', zorder=4)
        elif door_side == 'bottom':
            door_x = x - self.door_width/2
            door_y = y - size/2
            ax.plot([door_x, door_x + self.door_width], [door_y, door_y],
                   color='white', linewidth=5, zorder=4, solid_capstyle='butt')
            door_arc = patches.Arc(
                (door_x, door_y), self.door_width * 1.5, self.door_width * 1.5,
                angle=0, theta1=0, theta2=90,
                color='#3498DB', linewidth=1.5, linestyle='--', zorder=4)
        else:  # top
            door_x = x - self.door_width/2
            door_y = y + size/2
            ax.plot([door_x, door_x + self.door_width], [door_y, door_y],
                   color='white', linewidth=5, zorder=4, solid_capstyle='butt')
            door_arc = patches.Arc(
                (door_x + self.door_width, door_y), self.door_width * 1.5, self.door_width * 1.5,
                angle=180, theta1=0, theta2=90,
                color='#3498DB', linewidth=1.5, linestyle='--', zorder=4)
        
        ax.add_patch(door_arc)
    
    def _get_room_color(self, room):
        """Get room fill color based on priority"""
        if room.priority >= 3:
            return '#E74C3C'  # Red
        elif room.priority >= 2:
            return '#F39C12'  # Orange
        else:
            return '#3498DB'  # Blue
    
    def _add_dimensions(self, ax, floor_rooms):
        """Add dimension lines between rooms"""
        # Just add a few key dimensions
        if not floor_rooms:
            return
        
        # Get overall building dimensions
        all_x = [room.position[0] for room in floor_rooms.values()]
        all_y = [room.position[1] for room in floor_rooms.values()]
        
        if not all_x or not all_y:
            return
        
        min_x, max_x = min(all_x) - 5, max(all_x) + 5
        min_y, max_y = min(all_y) - 5, max(all_y) + 5
        
        # Overall width dimension
        y_pos = max_y + 3
        ax.plot([min_x, max_x], [y_pos, y_pos], 
               'k-', linewidth=1, zorder=1)
        ax.plot([min_x, min_x], [y_pos - 0.3, y_pos + 0.3], 
               'k-', linewidth=1, zorder=1)
        ax.plot([max_x, max_x], [y_pos - 0.3, y_pos + 0.3], 
               'k-', linewidth=1, zorder=1)
        
        width = max_x - min_x
        ax.text((min_x + max_x)/2, y_pos + 0.8, 
               f'{width:.1f}m',
               ha='center', va='bottom',
               fontsize=8, fontweight='bold',
               bbox=dict(boxstyle='round', facecolor='white', 
                        edgecolor='black', linewidth=0.5))
        
        # Overall height dimension
        x_pos = max_x + 3
        ax.plot([x_pos, x_pos], [min_y, max_y], 
               'k-', linewidth=1, zorder=1)
        ax.plot([x_pos - 0.3, x_pos + 0.3], [min_y, min_y], 
               'k-', linewidth=1, zorder=1)
        ax.plot([x_pos - 0.3, x_pos + 0.3], [max_y, max_y], 
               'k-', linewidth=1, zorder=1)
        
        height = max_y - min_y
        ax.text(x_pos + 0.8, (min_y + max_y)/2, 
               f'{height:.1f}m',
               ha='left', va='center',
               fontsize=8, fontweight='bold',
               rotation=90,
               bbox=dict(boxstyle='round', facecolor='white', 
                        edgecolor='black', linewidth=0.5))
    
    def _add_legend(self, ax):
        """Add professional legend"""
        legend_elements = [
            patches.Patch(facecolor='#3498DB', alpha=0.3, edgecolor='#2C3E50', 
                         linewidth=2, label='Normal Priority Room'),
            patches.Patch(facecolor='#F39C12', alpha=0.3, edgecolor='#2C3E50', 
                         linewidth=2, label='High Priority Room'),
            patches.Patch(facecolor='#E74C3C', alpha=0.3, edgecolor='#2C3E50', 
                         linewidth=2, label='Critical Priority'),
            patches.Patch(facecolor='#D5F4E6', edgecolor='#27AE60', 
                         linewidth=2, label='Exit'),
            patches.Patch(facecolor='#E8E8E8', edgecolor='#666666', 
                         linewidth=1.5, linestyle='--', alpha=0.5, label='Corridor')
        ]
        ax.legend(handles=legend_elements, loc='lower right', 
                 fontsize=9, framealpha=0.95, edgecolor='black')


def generate_all_blueprints():
    """Generate blueprints for all scenarios"""
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
        
        for floor in range(1, building.n_floors + 1):
            drawer = BlueprintDrawer(building, floor)
            
            if building.n_floors == 1:
                save_path = os.path.join(output_dir, 'blueprint.png')
            else:
                save_path = os.path.join(output_dir, f'blueprint_floor_{floor}.png')
            
            drawer.draw_blueprint(save_path=save_path)
    
    print("\n✓ All blueprints generated!")


if __name__ == '__main__':
    generate_all_blueprints()

