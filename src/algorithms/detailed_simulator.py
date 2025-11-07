"""
Enhanced simulator using detailed graph with door and corridor nodes
"""

import numpy as np
import networkx as nx
from typing import Dict, List


class DetailedSimulator:
    """Simulator that follows realistic paths through doors and corridors"""
    
    def __init__(self, building_with_doors, team, assignment):
        self.building = building_with_doors
        self.team = team
        self.assignment = assignment
        
        # Build detailed graph
        self.graph = building_with_doors.build_detailed_graph()
        
    def run(self) -> Dict:
        """Run simulation with detailed path tracking"""
        # Reset
        self.building.reset_clearance()
        self.team.reset_all()
        
        # Execute each responder's path
        for responder in self.team:
            self._execute_detailed_path(responder, self.assignment[responder.id])
        
        # Collect results
        results = self._collect_results()
        return results
    
    def _execute_detailed_path(self, responder, room_ids: List[str]):
        """Execute path with detailed routing through doors and corridors"""
        current_location = responder.position
        
        for room_id in room_ids:
            # Find detailed path: current → door → room center
            door_id = f"{room_id}_door"
            
            # Path 1: Current location to door
            if door_id in self.graph:
                try:
                    path_to_door = nx.shortest_path(self.graph, current_location, door_id, weight='weight')
                    distance_to_door = nx.shortest_path_length(self.graph, current_location, door_id, weight='weight')
                except:
                    # Fallback to direct connection
                    path_to_door = [current_location, room_id]
                    distance_to_door = 5
            else:
                path_to_door = [current_location, room_id]
                distance_to_door = 5
            
            # Move through each node in path
            for i in range(len(path_to_door) - 1):
                from_node = path_to_door[i]
                to_node = path_to_door[i + 1]
                
                if self.graph.has_edge(from_node, to_node):
                    edge_dist = self.graph[from_node][to_node]['weight']
                else:
                    edge_dist = 1
                
                # Add to responder's detailed path
                responder.path.append(to_node)
                responder.timeline.append({
                    'time': responder.current_time,
                    'action': 'passing',
                    'location': to_node,
                    'node_type': self.graph.nodes[to_node].get('type', 'unknown')
                })
                
                # Update time
                responder.current_time += edge_dist / responder.walk_speed
            
            # Now at door, move to room center
            if door_id in self.graph and room_id in self.graph:
                if self.graph.has_edge(door_id, room_id):
                    dist_to_center = self.graph[door_id][room_id]['weight']
                    responder.current_time += dist_to_center / responder.walk_speed
            
            # At room center now
            responder.position = room_id
            responder.timeline.append({
                'time': responder.current_time,
                'action': 'arrive_room',
                'location': room_id
            })
            
            # Check room
            room = self.building.rooms[room_id]
            check_time = room.calculate_check_time(responder.base_check_time, responder.check_rate)
            responder.current_time += check_time
            
            room.cleared = True
            room.cleared_at = responder.current_time
            room.cleared_by = responder.id
            responder.rooms_checked.append(room_id)
            
            responder.timeline.append({
                'time': responder.current_time,
                'action': 'check_complete',
                'location': room_id,
                'check_time': check_time
            })
            
            # Update current location to door (ready to leave)
            current_location = door_id
    
    def _collect_results(self) -> Dict:
        """Collect results with detailed paths"""
        responder_paths = []
        for responder in self.team:
            # Simplify path for visualization (only keep room nodes and exits)
            simplified_path = []
            for loc in responder.path:
                node_data = self.graph.nodes.get(loc, {})
                node_type = node_data.get('type', '')
                if node_type in ['room', 'exit'] or loc == responder.initial_position:
                    simplified_path.append(loc)
            
            # Get detailed path with ALL nodes for accurate visualization
            detailed_path = []
            detailed_positions = []
            for loc in responder.path:
                if loc in self.graph:
                    node_data = self.graph.nodes[loc]
                    detailed_path.append(loc)
                    detailed_positions.append(node_data['position'])
            
            responder_paths.append({
                'responder_id': responder.id,
                'path': simplified_path,  # For display
                'detailed_path': detailed_path,  # For accurate routing
                'detailed_positions': detailed_positions,  # For drawing
                'timeline': responder.timeline,
                'total_time': responder.current_time,
                'rooms_checked': responder.rooms_checked,
                'total_distance': responder.current_time * responder.walk_speed  # Approximate
            })
        
        # Room clearance
        room_clearance = {}
        for room_id, room in self.building.rooms.items():
            room_clearance[room_id] = {
                'cleared': room.cleared,
                'cleared_at': room.cleared_at,
                'cleared_by': room.cleared_by
            }
        
        # Metrics
        total_time = self.team.get_max_time()
        all_cleared = all(room.cleared for room in self.building.rooms.values())
        
        clearance_times = [room.cleared_at for room in self.building.rooms.values() 
                          if room.cleared_at is not None]
        avg_clearance_time = np.mean(clearance_times) if clearance_times else 0
        
        responder_times = [r.current_time for r in self.team]
        load_balance = 1.0 - (np.std(responder_times) / np.mean(responder_times)) if responder_times else 1.0
        
        results = {
            'success': all_cleared,
            'total_time': total_time,
            'responder_paths': responder_paths,
            'room_clearance': room_clearance,
            'metrics': {
                'all_rooms_cleared': all_cleared,
                'average_clearance_time': avg_clearance_time,
                'load_balance': load_balance,
                'redundancy_coverage': 0.0,
                'total_distance_traveled': sum(p['total_distance'] for p in responder_paths),
                'n_responders': len(self.team),
                'n_rooms': len(self.building.rooms)
            }
        }
        
        return results
    
    @staticmethod
    def run_quick(building_with_doors, team, assignment) -> Dict:
        """Quick run"""
        simulator = DetailedSimulator(building_with_doors, team, assignment)
        return simulator.run()

