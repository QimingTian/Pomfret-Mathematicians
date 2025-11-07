"""
Optimizer for detailed building model with doors
"""

import numpy as np
from typing import Dict, List
import networkx as nx
from ..models.responder import ResponderTeam


class DetailedOptimizer:
    """Optimizer that works with BuildingWithDoors"""
    
    def __init__(self, building_with_doors, n_responders: int = 2,
                 initial_positions: List[str] = None,
                 capabilities: dict = None,
                 strategy: str = 'balanced'):
        self.building = building_with_doors
        self.n_responders = n_responders
        self.strategy = strategy
        
        # Build detailed graph
        self.graph = building_with_doors.build_detailed_graph()
        
        # Create responder team
        if initial_positions is None:
            exits = list(building_with_doors.exits.keys())
            if len(exits) >= n_responders:
                initial_positions = exits[:n_responders]
            else:
                initial_positions = exits * (n_responders // len(exits) + 1)
                initial_positions = initial_positions[:n_responders]
        
        self.team = ResponderTeam(n_responders, initial_positions, capabilities)
        
    def optimize(self) -> Dict[int, List[str]]:
        """Optimize room assignment"""
        if self.strategy == 'balanced':
            return self._optimize_balanced()
        elif self.strategy == 'priority':
            return self._optimize_priority()
        else:
            return self._optimize_balanced()
    
    def _optimize_balanced(self) -> Dict[int, List[str]]:
        """Balanced load optimization"""
        assignment = {r.id: [] for r in self.team}
        unchecked_rooms = set(self.building.rooms.keys())
        
        estimated_times = {r.id: 0.0 for r in self.team}
        positions = {r.id: r.initial_position for r in self.team}
        
        while unchecked_rooms:
            # Find responder with minimum estimated time
            min_responder_id = min(estimated_times, key=estimated_times.get)
            current_pos = positions[min_responder_id]
            
            # Find nearest unchecked room
            best_room = None
            best_distance = np.inf
            
            for room_id in unchecked_rooms:
                try:
                    distance = nx.shortest_path_length(self.graph, current_pos, room_id, weight='weight')
                    if distance < best_distance:
                        best_distance = distance
                        best_room = room_id
                except:
                    continue
            
            if best_room is None:
                break
            
            # Assign room
            assignment[min_responder_id].append(best_room)
            positions[min_responder_id] = best_room
            unchecked_rooms.remove(best_room)
            
            # Update estimated time
            room = self.building.rooms[best_room]
            responder = self.team.get_responder(min_responder_id)
            travel_time = best_distance / responder.walk_speed
            check_time = room.calculate_check_time(responder.base_check_time, responder.check_rate)
            estimated_times[min_responder_id] += travel_time + check_time
        
        return assignment
    
    def _optimize_priority(self) -> Dict[int, List[str]]:
        """Priority-based optimization"""
        assignment = {r.id: [] for r in self.team}
        
        # Sort rooms by priority
        rooms = sorted(self.building.rooms.values(),
                      key=lambda r: (-r.priority, r.position[1], r.position[0]))
        
        # Round-robin assignment
        for i, room in enumerate(rooms):
            responder_id = (i % self.n_responders) + 1
            assignment[responder_id].append(room.id)
        
        # Optimize order within each responder's assignment
        for responder in self.team:
            if assignment[responder.id]:
                assignment[responder.id] = self._optimize_path_order(
                    responder.initial_position,
                    assignment[responder.id]
                )
        
        return assignment
    
    def _optimize_path_order(self, start_position: str, room_ids: List[str]) -> List[str]:
        """Optimize room visiting order using nearest neighbor"""
        if len(room_ids) <= 1:
            return room_ids
        
        unvisited = set(room_ids)
        ordered = []
        current = start_position
        
        while unvisited:
            nearest = None
            nearest_dist = np.inf
            
            for room_id in unvisited:
                try:
                    dist = nx.shortest_path_length(self.graph, current, room_id, weight='weight')
                    if dist < nearest_dist:
                        nearest_dist = dist
                        nearest = room_id
                except:
                    continue
            
            if nearest is None:
                ordered.extend(list(unvisited))
                break
            
            ordered.append(nearest)
            unvisited.remove(nearest)
            current = nearest
        
        return ordered
    
    def get_team(self):
        """Get responder team"""
        return self.team

