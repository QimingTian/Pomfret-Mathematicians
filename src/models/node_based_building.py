"""
Node-based building model for accurate path visualization
Creates explicit nodes at: doors, room centers, corridor points
"""

import numpy as np
import networkx as nx
from typing import Dict, List, Tuple
from .building import Building, Room


class NodeBasedBuilding:
    """Building with explicit navigation nodes"""
    
    def __init__(self, building: Building):
        """
        Create node-based building from regular building
        
        Args:
            building: Regular Building instance
        """
        self.building = building
        self.nodes = {}  # All navigation nodes
        self.graph = nx.Graph()
        
        self._create_all_nodes()
        self._connect_nodes()
    
    def _create_all_nodes(self):
        """Create all navigation nodes"""
        # 1. Room center nodes
        for room_id, room in self.building.rooms.items():
            self.nodes[f"{room_id}_center"] = {
                'type': 'room_center',
                'position': room.position,
                'floor': room.floor,
                'room_id': room_id
            }
            self.graph.add_node(f"{room_id}_center", **self.nodes[f"{room_id}_center"])
        
        # 2. Door nodes (at room edges toward corridor)
        for room_id, room in self.building.rooms.items():
            door_pos = self._calculate_door_position(room)
            door_id = f"{room_id}_door"
            
            self.nodes[door_id] = {
                'type': 'door',
                'position': door_pos,
                'floor': room.floor,
                'room_id': room_id
            }
            self.graph.add_node(door_id, **self.nodes[door_id])
            
            # Connect door to room center
            room_size = 4.0  # Fixed display size
            dist = room_size / 2
            self.graph.add_edge(f"{room_id}_center", door_id, weight=dist)
        
        # 3. Corridor nodes (dense points along corridor)
        for corridor_id, corridor in self.building.corridors.items():
            start = np.array(corridor['start'])
            end = np.array(corridor['end'])
            length = np.linalg.norm(end - start)
            
            # Create nodes every 1 meter
            n_nodes = int(length) + 1
            for i in range(n_nodes):
                t = i / max(n_nodes - 1, 1)
                pos = start + t * (end - start)
                node_id = f"{corridor_id}_p{i}"
                
                self.nodes[node_id] = {
                    'type': 'corridor',
                    'position': tuple(pos),
                    'floor': corridor.get('floor', 1)
                }
                self.graph.add_node(node_id, **self.nodes[node_id])
                
                # Connect to previous corridor node
                if i > 0:
                    prev_node = f"{corridor_id}_p{i-1}"
                    dist = length / max(n_nodes - 1, 1)
                    self.graph.add_edge(prev_node, node_id, weight=dist)
        
        # 4. Exit nodes
        for exit_id, exit_data in self.building.exits.items():
            self.nodes[exit_id] = {
                'type': 'exit',
                'position': exit_data['position'],
                'floor': exit_data.get('floor', 1)
            }
            self.graph.add_node(exit_id, **self.nodes[exit_id])
        
        # 5. Stair nodes (one node per floor per stairwell)
        for stair_id, stair_data in self.building.stairs.items():
            connects = stair_data.get('connects', [])
            for floor in connects:
                node_id = f"{stair_id}_F{floor}"
                self.nodes[node_id] = {
                    'type': 'stair',
                    'position': stair_data['position'],
                    'floor': floor,
                    'stair_id': stair_id
                }
                self.graph.add_node(node_id, **self.nodes[node_id])
            
            # IMPORTANT: Connect stairs vertically between floors
            for i in range(len(connects) - 1):
                floor_below = connects[i]
                floor_above = connects[i + 1]
                node_below = f"{stair_id}_F{floor_below}"
                node_above = f"{stair_id}_F{floor_above}"
                
                # Vertical connection (4 meters per floor)
                self.graph.add_edge(node_below, node_above, weight=4.0)
    
    def _calculate_door_position(self, room: Room) -> Tuple[float, float]:
        """Calculate door position (on room edge toward corridor)"""
        room_pos = np.array(room.position)
        room_size = 4.0  # Fixed display size
        
        # Find nearest corridor
        nearest_corridor = None
        min_dist = float('inf')
        
        for corridor_id, corridor in self.building.corridors.items():
            if corridor.get('floor', 1) != room.floor:
                continue
            
            c_start = np.array(corridor['start'])
            c_end = np.array(corridor['end'])
            c_mid = (c_start + c_end) / 2
            
            dist = np.linalg.norm(room_pos - c_mid)
            if dist < min_dist:
                min_dist = dist
                nearest_corridor = corridor
        
        if nearest_corridor:
            c_start = np.array(nearest_corridor['start'])
            c_end = np.array(nearest_corridor['end'])
            
            # Determine corridor orientation
            if abs(c_end[0] - c_start[0]) < 1:  # Vertical corridor
                corridor_x = c_start[0]
                if corridor_x > room_pos[0]:  # Corridor on right
                    return (room_pos[0] + room_size/2, room_pos[1])
                else:  # Corridor on left
                    return (room_pos[0] - room_size/2, room_pos[1])
            else:  # Horizontal corridor
                corridor_y = c_start[1]
                if corridor_y > room_pos[1]:  # Corridor above
                    return (room_pos[0], room_pos[1] + room_size/2)
                else:  # Corridor below
                    return (room_pos[0], room_pos[1] - room_size/2)
        
        # Default: right side
        return (room_pos[0] + room_size/2, room_pos[1])
    
    def _connect_nodes(self):
        """Connect all nodes appropriately"""
        # Connect doors to nearest corridor nodes
        for door_id, door_data in self.nodes.items():
            if door_data['type'] != 'door':
                continue
            
            door_pos = np.array(door_data['position'])
            door_floor = door_data['floor']
            
            # Find nearest corridor node
            min_dist = float('inf')
            nearest_corridor_node = None
            
            for node_id, node_data in self.nodes.items():
                if node_data['type'] == 'corridor' and node_data['floor'] == door_floor:
                    node_pos = np.array(node_data['position'])
                    dist = np.linalg.norm(door_pos - node_pos)
                    
                    if dist < min_dist:
                        min_dist = dist
                        nearest_corridor_node = node_id
            
            if nearest_corridor_node and min_dist < 5:
                self.graph.add_edge(door_id, nearest_corridor_node, weight=min_dist)
        
        # Connect exits to nearest corridor nodes
        for exit_id, exit_data in self.nodes.items():
            if exit_data['type'] != 'exit':
                continue
            
            exit_pos = np.array(exit_data['position'])
            exit_floor = exit_data['floor']
            
            # Find nearest corridor node
            min_dist = float('inf')
            nearest_corridor_node = None
            
            for node_id, node_data in self.nodes.items():
                if node_data['type'] == 'corridor' and node_data['floor'] == exit_floor:
                    node_pos = np.array(node_data['position'])
                    dist = np.linalg.norm(exit_pos - node_pos)
                    
                    if dist < min_dist:
                        min_dist = dist
                        nearest_corridor_node = node_id
            
            if nearest_corridor_node:
                self.graph.add_edge(exit_id, nearest_corridor_node, weight=min_dist)
        
        # Connect each stair node to corridor nodes on its floor
        for stair_node_id, stair_node_data in self.nodes.items():
            if stair_node_data['type'] != 'stair':
                continue
            
            stair_pos = np.array(stair_node_data['position'])
            stair_floor = stair_node_data['floor']
            
            # Find nearest corridor node on same floor
            min_dist = float('inf')
            nearest_corridor_node = None
            
            for node_id, node_data in self.nodes.items():
                if node_data['type'] == 'corridor' and node_data['floor'] == stair_floor:
                    node_pos = np.array(node_data['position'])
                    dist = np.linalg.norm(stair_pos - node_pos)
                    
                    if dist < min_dist:
                        min_dist = dist
                        nearest_corridor_node = node_id
            
            if nearest_corridor_node and min_dist < 10:  # Within reasonable distance
                self.graph.add_edge(stair_node_id, nearest_corridor_node, weight=min_dist)
    
    def get_shortest_path(self, start: str, end: str) -> Tuple[List[str], List[Tuple[float, float]]]:
        """
        Get shortest path between two locations
        
        Args:
            start: Start location (room_id or exit_id)
            end: End location (room_id)
        
        Returns:
            Tuple of (node_list, position_list)
        """
        # Convert room IDs to center nodes
        start_node = f"{start}_center" if start in self.building.rooms else start
        end_node = f"{end}_center" if end in self.building.rooms else end
        
        try:
            path = nx.shortest_path(self.graph, start_node, end_node, weight='weight')
            positions = [self.nodes[node]['position'] for node in path]
            return path, positions
        except:
            return [], []
    
    def get_all_nodes_on_floor(self, floor: int) -> Dict:
        """Get all nodes on a specific floor"""
        floor_nodes = {}
        for node_id, node_data in self.nodes.items():
            if node_data['floor'] == floor:
                floor_nodes[node_id] = node_data
        return floor_nodes

