"""
Graph representation of building for path planning
"""

import networkx as nx
import numpy as np
from typing import List, Dict, Tuple, Optional


class BuildingGraph:
    """Graph representation of building for efficient path finding"""
    
    def __init__(self, building):
        """
        Create graph from building
        
        Args:
            building: Building instance
        """
        self.building = building
        self.graph = nx.Graph()
        self._build_graph()
        
    def _build_graph(self):
        """Build NetworkX graph from building structure"""
        # Add room nodes
        for room_id, room in self.building.rooms.items():
            self.graph.add_node(
                room_id,
                node_type='room',
                position=room.position,
                floor=room.floor,
                area=room.area,
                priority=room.priority
            )
            
        # Add exit nodes
        for exit_id, exit_data in self.building.exits.items():
            self.graph.add_node(
                exit_id,
                node_type='exit',
                position=exit_data['position'],
                floor=exit_data['floor']
            )
            
        # Add corridor nodes
        for corridor_id, corridor_data in self.building.corridors.items():
            # Use corridor center as position
            start = np.array(corridor_data['start'])
            end = np.array(corridor_data['end'])
            center = (start + end) / 2
            self.graph.add_node(
                corridor_id,
                node_type='corridor',
                position=tuple(center),
                floor=corridor_data['floor']
            )
            
        # Add stair nodes
        for stair_id, stair_data in self.building.stairs.items():
            for floor in stair_data['connects']:
                node_id = f"{stair_id}_F{floor}"
                self.graph.add_node(
                    node_id,
                    node_type='stair',
                    position=stair_data['position'],
                    floor=floor,
                    stair_id=stair_id
                )
                
        # Add edges from connections
        for conn in self.building.connections:
            if conn['from'] in self.graph and conn['to'] in self.graph:
                self.graph.add_edge(
                    conn['from'],
                    conn['to'],
                    weight=conn['distance']
                )
                
    def shortest_path(self, source: str, target: str) -> Tuple[List[str], float]:
        """
        Find shortest path between two nodes
        
        Args:
            source: Source node ID
            target: Target node ID
            
        Returns:
            Tuple of (path, distance)
        """
        try:
            path = nx.shortest_path(self.graph, source, target, weight='weight')
            distance = nx.shortest_path_length(self.graph, source, target, weight='weight')
            return path, distance
        except nx.NetworkXNoPath:
            return [], np.inf
            
    def shortest_paths_from_node(self, source: str) -> Dict[str, Tuple[List[str], float]]:
        """
        Find shortest paths from source to all other nodes
        
        Args:
            source: Source node ID
            
        Returns:
            Dictionary mapping target -> (path, distance)
        """
        try:
            paths = nx.single_source_dijkstra_path(self.graph, source, weight='weight')
            lengths = nx.single_source_dijkstra_path_length(self.graph, source, weight='weight')
            return {target: (paths[target], lengths[target]) for target in paths}
        except:
            return {}
            
    def get_room_nodes(self) -> List[str]:
        """Get list of all room node IDs"""
        return [node for node, data in self.graph.nodes(data=True)
                if data.get('node_type') == 'room']
                
    def get_exit_nodes(self) -> List[str]:
        """Get list of all exit node IDs"""
        return [node for node, data in self.graph.nodes(data=True)
                if data.get('node_type') == 'exit']
                
    def get_nearest_rooms(self, location: str, n: int = 5) -> List[Tuple[str, float]]:
        """
        Get n nearest rooms to a location
        
        Args:
            location: Current location ID
            n: Number of nearest rooms to return
            
        Returns:
            List of (room_id, distance) tuples
        """
        room_nodes = self.get_room_nodes()
        distances = []
        
        for room_id in room_nodes:
            _, distance = self.shortest_path(location, room_id)
            if distance < np.inf:
                distances.append((room_id, distance))
                
        distances.sort(key=lambda x: x[1])
        return distances[:n]
    
    def get_node_position(self, node_id: str) -> Optional[Tuple[float, float]]:
        """Get position of a node"""
        if node_id in self.graph:
            return self.graph.nodes[node_id].get('position')
        return None
    
    def is_same_floor(self, node1: str, node2: str) -> bool:
        """Check if two nodes are on the same floor"""
        if node1 in self.graph and node2 in self.graph:
            floor1 = self.graph.nodes[node1].get('floor', 1)
            floor2 = self.graph.nodes[node2].get('floor', 1)
            return floor1 == floor2
        return False
    
    def __repr__(self):
        return f"BuildingGraph({self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges)"

