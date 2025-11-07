"""
Enhanced building model with door nodes for realistic path planning
"""

import json
import numpy as np
from typing import List, Dict, Tuple, Optional
from .building import Room, Building as BaseBuilding


class BuildingWithDoors(BaseBuilding):
    """Enhanced building model with explicit door nodes"""
    
    def __init__(self, name: str = "Building", n_floors: int = 1):
        super().__init__(name, n_floors)
        self.doors: Dict[str, Dict] = {}  # Door nodes
        
    def add_room(self, room: Room):
        """Add room and automatically create door node"""
        super().add_room(room)
        
        # Create door node
        door_id = f"{room.id}_door"
        
        # Door position (will be calculated based on corridor)
        self.doors[door_id] = {
            'id': door_id,
            'room_id': room.id,
            'position': None,  # Will be set when adding connections
            'floor': room.floor
        }
    
    def finalize_doors(self):
        """Calculate door positions based on corridors and room positions"""
        for door_id, door_data in self.doors.items():
            room_id = door_data['room_id']
            room = self.rooms[room_id]
            
            # Find nearest corridor
            nearest_corridor = None
            min_dist = float('inf')
            
            for corridor_id, corridor in self.corridors.items():
                if corridor.get('floor', 1) != room.floor:
                    continue
                    
                c_start = np.array(corridor['start'])
                c_end = np.array(corridor['end'])
                c_mid = (c_start + c_end) / 2
                
                dist = np.linalg.norm(np.array(room.position) - c_mid)
                if dist < min_dist:
                    min_dist = dist
                    nearest_corridor = corridor
            
            if nearest_corridor:
                # Calculate door position (between room center and corridor)
                room_pos = np.array(room.position)
                c_start = np.array(nearest_corridor['start'])
                c_end = np.array(nearest_corridor['end'])
                
                # Determine if corridor is vertical or horizontal
                if abs(c_end[0] - c_start[0]) < 1:  # Vertical corridor
                    corridor_x = c_start[0]
                    # Door is on the edge of room toward corridor
                    room_size = np.sqrt(room.area)
                    if corridor_x > room_pos[0]:  # Corridor on right
                        door_pos = (room_pos[0] + room_size/2, room_pos[1])
                    else:  # Corridor on left
                        door_pos = (room_pos[0] - room_size/2, room_pos[1])
                else:  # Horizontal corridor
                    corridor_y = c_start[1]
                    room_size = np.sqrt(room.area)
                    if corridor_y > room_pos[1]:  # Corridor above
                        door_pos = (room_pos[0], room_pos[1] + room_size/2)
                    else:  # Corridor below
                        door_pos = (room_pos[0], room_pos[1] - room_size/2)
                
                door_data['position'] = door_pos
    
    def build_detailed_graph(self):
        """Build graph with corridor nodes and door nodes"""
        import networkx as nx
        
        graph = nx.Graph()
        
        # Add room center nodes
        for room_id, room in self.rooms.items():
            graph.add_node(room_id, type='room', position=room.position, floor=room.floor)
        
        # Add door nodes
        for door_id, door_data in self.doors.items():
            if door_data['position']:
                graph.add_node(door_id, type='door', position=door_data['position'], 
                             floor=door_data['floor'])
                
                # Connect door to room center
                room_id = door_data['room_id']
                room = self.rooms[room_id]
                room_size = np.sqrt(room.area)
                dist = room_size / 2  # Half room size
                graph.add_edge(room_id, door_id, weight=dist)
        
        # Add corridor nodes (multiple points along corridor)
        for corridor_id, corridor in self.corridors.items():
            c_start = np.array(corridor['start'])
            c_end = np.array(corridor['end'])
            c_length = np.linalg.norm(c_end - c_start)
            
            # Create nodes along corridor (every 2 meters)
            n_nodes = max(int(c_length / 2), 2)
            for i in range(n_nodes + 1):
                t = i / n_nodes
                pos = c_start + t * (c_end - c_start)
                node_id = f"{corridor_id}_n{i}"
                graph.add_node(node_id, type='corridor', position=tuple(pos), 
                             floor=corridor.get('floor', 1))
                
                # Connect to previous node
                if i > 0:
                    prev_node = f"{corridor_id}_n{i-1}"
                    dist = c_length / n_nodes
                    graph.add_edge(prev_node, node_id, weight=dist)
        
        # Connect doors to nearest corridor nodes
        for door_id, door_data in self.doors.items():
            if not door_data['position']:
                continue
                
            door_pos = np.array(door_data['position'])
            
            # Find nearest corridor node
            min_dist = float('inf')
            nearest_corridor_node = None
            
            for node, data in graph.nodes(data=True):
                if data.get('type') == 'corridor' and data.get('floor') == door_data['floor']:
                    node_pos = np.array(data['position'])
                    dist = np.linalg.norm(door_pos - node_pos)
                    if dist < min_dist:
                        min_dist = dist
                        nearest_corridor_node = node
            
            if nearest_corridor_node:
                graph.add_edge(door_id, nearest_corridor_node, weight=min_dist)
        
        # Connect exits to corridor nodes
        for exit_id, exit_data in self.exits.items():
            graph.add_node(exit_id, type='exit', position=exit_data['position'], 
                         floor=exit_data.get('floor', 1))
            
            exit_pos = np.array(exit_data['position'])
            
            # Find nearest corridor node
            min_dist = float('inf')
            nearest_corridor_node = None
            
            for node, data in graph.nodes(data=True):
                if data.get('type') == 'corridor' and data.get('floor') == exit_data.get('floor', 1):
                    node_pos = np.array(data['position'])
                    dist = np.linalg.norm(exit_pos - node_pos)
                    if dist < min_dist:
                        min_dist = dist
                        nearest_corridor_node = node
            
            if nearest_corridor_node:
                graph.add_edge(exit_id, nearest_corridor_node, weight=min_dist)
        
        return graph
    
    @classmethod
    def from_json(cls, filepath: str) -> 'BuildingWithDoors':
        """Load building from JSON and create detailed graph"""
        # Use parent class method to load basic structure
        basic_building = BaseBuilding.from_json(filepath)
        
        # Convert to BuildingWithDoors
        building = cls(basic_building.name, basic_building.n_floors)
        building.rooms = basic_building.rooms
        building.corridors = basic_building.corridors
        building.exits = basic_building.exits
        building.stairs = basic_building.stairs
        
        # Create door nodes for all rooms
        for room_id, room in building.rooms.items():
            door_id = f"{room_id}_door"
            building.doors[door_id] = {
                'id': door_id,
                'room_id': room_id,
                'position': None,
                'floor': room.floor
            }
        
        # Calculate door positions
        building.finalize_doors()
        
        return building

