#!/usr/bin/env python3
"""
Generate clean blueprints - structure and paths
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import json

from src.models.building import Building
from src.algorithms.smart_optimizer import SmartOptimizer
from src.algorithms.simulator import Simulator


class BlueprintGenerator:
    """Generate professional blueprints"""
    
    def __init__(self, building, floor_num=1):
        self.building = building
        self.floor_num = floor_num
        self.wall_thickness = 0.2
        self.door_width = 1.0
        
    def draw_structure(self, save_path):
        """Draw structure only"""
        fig, ax = plt.subplots(figsize=(16, 12))
        ax.set_facecolor('#F8F9FA')
        
        self._draw_building(ax)
        self._finalize_plot(ax, "Floor Plan - Structure Only")
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        print(f"  ✓ Structure: {save_path}")
    
    def draw_with_paths(self, results, save_path):
        """Draw structure with paths"""
        fig, ax = plt.subplots(figsize=(16, 12))
        ax.set_facecolor('#F8F9FA')
        
        self._draw_building(ax)
        self._draw_paths(ax, results)
        self._finalize_plot(ax, f"Floor Plan with Sweep Paths (Total: {results['total_time']:.1f}s)")
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        print(f"  ✓ With paths: {save_path}")
    
    def _draw_building(self, ax):
        """Draw complete building structure"""
        floor_rooms = {rid: r for rid, r in self.building.rooms.items() 
                      if r.floor == self.floor_num}
        floor_exits = {eid: e for eid, e in self.building.exits.items() 
                      if e.get('floor', 1) == self.floor_num}
        floor_corridors = {cid: c for cid, c in self.building.corridors.items() 
                          if c.get('floor', 1) == self.floor_num}
        
        # Draw corridors
        for corridor in floor_corridors.values():
            self._draw_corridor(ax, corridor)
        
        # Draw rooms with walls and doors
        for room in floor_rooms.values():
            self._draw_room(ax, room)
        
        # Draw exits
        for exit_id, exit_data in floor_exits.items():
            self._draw_exit(ax, exit_data, exit_id)
    
    def _draw_corridor(self, ax, corridor):
        """Draw corridor"""
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
            
            poly = patches.Polygon(corners, 
                                 facecolor='#E8E8E8', 
                                 edgecolor='#666666',
                                 linewidth=1.5,
                                 linestyle='--',
                                 alpha=0.5,
                                 zorder=1)
            ax.add_patch(poly)
    
    def _draw_room(self, ax, room):
        """Draw room with walls and door"""
        x, y = room.position
        size = np.sqrt(room.area)
        
        # Walls
        wall_color = '#2C3E50'
        outer_rect = patches.Rectangle(
            (x - size/2, y - size/2), size, size,
            linewidth=3,
            edgecolor=wall_color,
            facecolor='white',
            zorder=3
        )
        ax.add_patch(outer_rect)
        
        # Room fill
        color = self._get_room_color(room)
        inner_rect = patches.Rectangle(
            (x - size/2 + self.wall_thickness, 
             y - size/2 + self.wall_thickness),
            size - 2*self.wall_thickness,
            size - 2*self.wall_thickness,
            linewidth=0,
            facecolor=color,
            alpha=0.25,
            zorder=3
        )
        ax.add_patch(inner_rect)
        
        # Door toward corridor
        door_side = self._find_door_side(room)
        self._draw_door(ax, x, y, size, door_side)
        
        # Labels
        ax.text(x, y, room.id,
               ha='center', va='center',
               fontsize=10, fontweight='bold',
               color='#2C3E50',
               zorder=5)
        
        ax.text(x, y - size/3, f'{room.area}m²',
               ha='center', va='center',
               fontsize=7, color='#666',
               zorder=5)
    
    def _find_door_side(self, room):
        """Find which side door should be on"""
        corridors = {cid: c for cid, c in self.building.corridors.items() 
                    if c.get('floor', 1) == room.floor}
        
        if not corridors:
            return 'right'
        
        x, y = room.position
        corridor = list(corridors.values())[0]
        c_start = np.array(corridor['start'])
        c_end = np.array(corridor['end'])
        
        # Vertical corridor
        if abs(c_end[0] - c_start[0]) < 1:
            corridor_x = c_start[0]
            return 'right' if corridor_x > x else 'left'
        else:  # Horizontal corridor
            corridor_y = c_start[1]
            return 'bottom' if corridor_y < y else 'top'
    
    def _draw_door(self, ax, x, y, size, door_side):
        """Draw door on specified side"""
        if door_side == 'right':
            door_x, door_y = x + size/2, y
            ax.plot([door_x, door_x], [door_y - self.door_width/2, door_y + self.door_width/2],
                   color='white', linewidth=5, zorder=4)
            arc = patches.Arc((door_x, door_y - self.door_width/2), 
                            self.door_width * 1.5, self.door_width * 1.5,
                            angle=90, theta1=0, theta2=90,
                            color='#3498DB', linewidth=1.5, linestyle='--', zorder=4)
        elif door_side == 'left':
            door_x, door_y = x - size/2, y
            ax.plot([door_x, door_x], [door_y - self.door_width/2, door_y + self.door_width/2],
                   color='white', linewidth=5, zorder=4)
            arc = patches.Arc((door_x, door_y + self.door_width/2), 
                            self.door_width * 1.5, self.door_width * 1.5,
                            angle=270, theta1=0, theta2=90,
                            color='#3498DB', linewidth=1.5, linestyle='--', zorder=4)
        elif door_side == 'bottom':
            door_x, door_y = x, y - size/2
            ax.plot([door_x - self.door_width/2, door_x + self.door_width/2], [door_y, door_y],
                   color='white', linewidth=5, zorder=4)
            arc = patches.Arc((door_x, door_y), 
                            self.door_width * 1.5, self.door_width * 1.5,
                            angle=0, theta1=0, theta2=90,
                            color='#3498DB', linewidth=1.5, linestyle='--', zorder=4)
        else:  # top
            door_x, door_y = x, y + size/2
            ax.plot([door_x - self.door_width/2, door_x + self.door_width/2], [door_y, door_y],
                   color='white', linewidth=5, zorder=4)
            arc = patches.Arc((door_x + self.door_width, door_y), 
                            self.door_width * 1.5, self.door_width * 1.5,
                            angle=180, theta1=0, theta2=90,
                            color='#3498DB', linewidth=1.5, linestyle='--', zorder=4)
        
        ax.add_patch(arc)
    
    def _draw_exit(self, ax, exit_data, exit_id):
        """Draw exit"""
        x, y = exit_data['position']
        rect = patches.FancyBboxPatch(
            (x - 2, y - 1), 4, 2,
            boxstyle="round,pad=0.1",
            linewidth=2.5,
            edgecolor='#27AE60',
            facecolor='#D5F4E6',
            zorder=10
        )
        ax.add_patch(rect)
        
        ax.text(x, y, 'EXIT',
               ha='center', va='center',
               fontsize=10, fontweight='bold',
               color='#27AE60',
               zorder=11)
    
    def _draw_paths(self, ax, results):
        """Draw responder paths"""
        colors = plt.cm.Set3(np.linspace(0, 1, 12))
        
        for i, path_data in enumerate(results['responder_paths']):
            responder_id = path_data['responder_id']
            path = path_data['path']
            
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
                color = colors[i % len(colors)]
                
                ax.plot(xs, ys, '-', color=color, linewidth=4, 
                       alpha=0.8, zorder=20,
                       label=f'Responder {responder_id}: {path_data["total_time"]:.1f}s')
                
                ax.plot(xs, ys, 'o', color=color, markersize=12, 
                       markeredgecolor='white', markeredgewidth=2.5,
                       alpha=0.95, zorder=21)
                
                # Number the stops
                for j, (px, py) in enumerate(positions):
                    ax.text(px, py, str(j), 
                           ha='center', va='center',
                           fontsize=9, fontweight='bold',
                           color='white',
                           zorder=22)
        
        ax.legend(loc='lower right', fontsize=10, framealpha=0.95, 
                 edgecolor='black', title='Sweep Paths', title_fontsize=11)
    
    def _get_room_color(self, room):
        """Get room color"""
        if room.priority >= 3:
            return '#E74C3C'
        elif room.priority >= 2:
            return '#F39C12'
        else:
            return '#3498DB'
    
    def _finalize_plot(self, ax, title_suffix):
        """Finalize plot settings"""
        ax.set_xlabel('Distance (meters)', fontsize=11, fontweight='bold')
        ax.set_ylabel('Distance (meters)', fontsize=11, fontweight='bold')
        
        title_text = f'{self.building.name}\nFloor {self.floor_num} - {title_suffix}'
        ax.text(0.02, 0.98, title_text,
               transform=ax.transAxes,
               fontsize=13,
               fontweight='bold',
               verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='white', 
                        edgecolor='black', linewidth=2, alpha=0.95),
               zorder=50)
        
        ax.grid(True, alpha=0.2, linestyle='--', linewidth=0.5, color='gray')
        ax.set_aspect('equal')
        
        # Get bounds
        floor_rooms = {rid: r for rid, r in self.building.rooms.items() 
                      if r.floor == self.floor_num}
        if floor_rooms:
            all_x = [room.position[0] for room in floor_rooms.values()]
            all_y = [room.position[1] for room in floor_rooms.values()]
            padding = 3
            ax.set_xlim(min(all_x) - padding, max(all_x) + padding)
            ax.set_ylim(min(all_y) - padding, max(all_y) + padding)
        
        plt.tight_layout()


def run_scenario(scenario_file, output_dir):
    """Generate blueprints for one scenario"""
    building = Building.from_json(scenario_file)
    
    with open(scenario_file) as f:
        data = json.load(f)
    n_responders = data['responders']['count']
    
    print(f"\n{building.name} ({building.n_floors} floor(s), {len(building.rooms)} rooms)")
    
    # Run optimization
    optimizer = SmartOptimizer(building, n_responders=n_responders)
    assignment = optimizer.optimize()
    team = optimizer.get_team()
    results = Simulator.run_quick(building, team, assignment)
    
    print(f"  Strategy: {optimizer.selected_strategy.upper()}, Time: {results['total_time']:.1f}s")
    
    # Generate blueprints for each floor
    os.makedirs(output_dir, exist_ok=True)
    
    for floor in range(1, building.n_floors + 1):
        generator = BlueprintGenerator(building, floor)
        
        if building.n_floors == 1:
            structure_path = os.path.join(output_dir, '1_structure.png')
            paths_path = os.path.join(output_dir, '2_paths.png')
        else:
            structure_path = os.path.join(output_dir, f'1_structure_floor_{floor}.png')
            paths_path = os.path.join(output_dir, f'2_paths_floor_{floor}.png')
        
        generator.draw_structure(structure_path)
        generator.draw_with_paths(results, paths_path)


def main():
    print("="*60)
    print("GENERATING BLUEPRINTS")
    print("="*60)
    
    scenarios = [
        ('data/scenarios/scenario1_basic.json', 'data/results/scenario1'),
        ('data/scenarios/scenario2_three_floors.json', 'data/results/scenario2'),
        ('data/scenarios/scenario3_school.json', 'data/results/scenario3')
    ]
    
    for scenario_file, output_dir in scenarios:
        run_scenario(scenario_file, output_dir)
    
    print("\n" + "="*60)
    print("COMPLETE!")
    print("="*60)


if __name__ == '__main__':
    main()

