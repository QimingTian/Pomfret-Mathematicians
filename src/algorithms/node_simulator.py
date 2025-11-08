"""
Simulator using node-based building for multi-floor path finding
"""

import numpy as np
import networkx as nx
from typing import Dict, List


class NodeSimulator:
    """Simulator that uses node-based building graph"""
    
    def __init__(self, building, node_building, team, assignment):
        self.building = building
        self.node_building = node_building
        self.team = team
        self.assignment = assignment
    
    def run(self) -> Dict:
        """Run simulation with node-based paths"""
        # Reset
        self.building.reset_clearance()
        self.team.reset_all()
        
        # Execute each responder's path
        for responder in self.team:
            self._execute_node_path(responder, self.assignment[responder.id])
        
        # Collect results
        results = self._collect_results()
        return results
    
    def _execute_node_path(self, responder, room_ids: List[str]):
        """Execute path using node-based graph"""
        current_location = responder.position
        
        for room_id in room_ids:
            # Get shortest path through nodes
            path_nodes, path_positions = self.node_building.get_shortest_path(current_location, room_id)
            
            if not path_nodes:
                print(f"Warning: No path from {current_location} to {room_id}")
                continue
            
            # Travel through all nodes
            total_distance = 0
            for i in range(len(path_nodes) - 1):
                from_node = path_nodes[i]
                to_node = path_nodes[i + 1]
                
                if self.node_building.graph.has_edge(from_node, to_node):
                    edge_weight = self.node_building.graph[from_node][to_node]['weight']
                    total_distance += edge_weight
                    
                    # Check if this is a stair segment (between floors)
                    from_data = self.node_building.nodes.get(from_node, {})
                    to_data = self.node_building.nodes.get(to_node, {})
                    
                    if from_data.get('type') == 'stair' and to_data.get('type') == 'stair':
                        # Going up/down stairs
                        if to_data['floor'] > from_data['floor']:
                            # Going up
                            responder.current_time += edge_weight / responder.stair_up_speed
                        else:
                            # Going down
                            responder.current_time += edge_weight / responder.stair_down_speed
                    else:
                        # Normal walking
                        responder.current_time += edge_weight / responder.walk_speed
                    
                    responder.timeline.append({
                        'time': responder.current_time,
                        'action': 'passing',
                        'location': to_node,
                        'node_type': to_data.get('type', 'unknown')
                    })
            
            # Arrived at room center
            responder.position = f"{room_id}_center"
            responder.timeline.append({
                'time': responder.current_time,
                'action': 'arrive',
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
            
            current_location = room_id
        
        # Save detailed path
        responder.path = path_nodes if 'path_nodes' in dir(responder) else responder.path
        responder.detailed_path_nodes = []
        responder.detailed_path_positions = []
        
        # Reconstruct full path for visualization
        full_path_nodes = []
        full_path_positions = []
        start = responder.initial_position
        
        for room_id in responder.rooms_checked:
            path_nodes, path_positions = self.node_building.get_shortest_path(start, room_id)
            if path_nodes:
                full_path_nodes.extend(path_nodes)
                full_path_positions.extend(path_positions)
                start = room_id
        
        responder.detailed_path_nodes = full_path_nodes
        responder.detailed_path_positions = full_path_positions
    
    def _collect_results(self) -> Dict:
        """Collect results"""
        responder_paths = []
        for responder in self.team:
            responder_paths.append({
                'responder_id': responder.id,
                'path': responder.path if isinstance(responder.path, list) else [responder.path],
                'detailed_path_nodes': getattr(responder, 'detailed_path_nodes', []),
                'detailed_path_positions': getattr(responder, 'detailed_path_positions', []),
                'timeline': responder.timeline,
                'total_time': responder.current_time,
                'rooms_checked': responder.rooms_checked,
                'total_distance': responder.current_time * responder.walk_speed
            })
        
        room_clearance = {}
        for room_id, room in self.building.rooms.items():
            room_clearance[room_id] = {
                'cleared': room.cleared,
                'cleared_at': room.cleared_at,
                'cleared_by': room.cleared_by
            }
        
        total_time = self.team.get_max_time()
        all_cleared = all(room.cleared for room in self.building.rooms.values())
        
        clearance_times = [room.cleared_at for room in self.building.rooms.values() 
                          if room.cleared_at is not None]
        avg_clearance_time = np.mean(clearance_times) if clearance_times else 0
        
        responder_times = [r.current_time for r in self.team]
        load_balance = 1.0 - (np.std(responder_times) / np.mean(responder_times)) if responder_times and np.mean(responder_times) > 0 else 1.0
        
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
    def run_quick(building, node_building, team, assignment) -> Dict:
        """Quick run"""
        simulator = NodeSimulator(building, node_building, team, assignment)
        return simulator.run()

