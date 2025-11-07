"""
Greedy optimization algorithm for building sweep
"""

import numpy as np
from typing import Dict, List
from ..models.building import Building
from ..models.responder import ResponderTeam
from ..models.graph import BuildingGraph


class GreedyOptimizer:
    """Greedy algorithm for room assignment"""
    
    def __init__(self, building: Building, n_responders: int = 2,
                 initial_positions: List[str] = None,
                 capabilities: dict = None,
                 strategy: str = 'nearest'):
        """
        Initialize greedy optimizer
        
        Args:
            building: Building instance
            n_responders: Number of responders
            initial_positions: Initial positions for responders
            capabilities: Responder capabilities
            strategy: Greedy strategy ('nearest', 'priority', 'balanced')
        """
        self.building = building
        self.n_responders = n_responders
        self.strategy = strategy
        
        # Create responder team
        if initial_positions is None:
            exits = list(building.exits.keys())
            if len(exits) >= n_responders:
                initial_positions = exits[:n_responders]
            else:
                initial_positions = exits * (n_responders // len(exits) + 1)
                initial_positions = initial_positions[:n_responders]
                
        self.team = ResponderTeam(n_responders, initial_positions, capabilities)
        self.graph = BuildingGraph(building)
        
    def optimize(self) -> Dict[int, List[str]]:
        """
        Run greedy optimization
        
        Returns:
            Dictionary mapping responder_id -> list of room IDs
        """
        if self.strategy == 'nearest':
            return self._greedy_nearest()
        elif self.strategy == 'priority':
            return self._greedy_priority()
        elif self.strategy == 'balanced':
            return self._greedy_balanced()
        else:
            return self._greedy_nearest()
            
    def _greedy_nearest(self) -> Dict[int, List[str]]:
        """
        Nearest-first greedy strategy
        Each responder takes the nearest unchecked room
        """
        assignment = {r.id: [] for r in self.team}
        unchecked_rooms = set(self.building.rooms.keys())
        
        # Current positions of responders
        positions = {r.id: r.initial_position for r in self.team}
        
        while unchecked_rooms:
            # Find best (responder, room) pair
            best_responder = None
            best_room = None
            best_distance = np.inf
            
            for responder in self.team:
                current_pos = positions[responder.id]
                
                for room_id in unchecked_rooms:
                    _, distance = self.graph.shortest_path(current_pos, room_id)
                    
                    if distance < best_distance:
                        best_distance = distance
                        best_responder = responder.id
                        best_room = room_id
                        
            if best_room is None:
                break
                
            # Assign room to responder
            assignment[best_responder].append(best_room)
            positions[best_responder] = best_room
            unchecked_rooms.remove(best_room)
            
        return assignment
    
    def _greedy_priority(self) -> Dict[int, List[str]]:
        """
        Priority-first greedy strategy
        High priority rooms are checked first
        """
        assignment = {r.id: [] for r in self.team}
        
        # Sort rooms by priority (descending) then by position
        rooms = sorted(
            self.building.rooms.values(),
            key=lambda r: (-r.priority, r.position[1], r.position[0])
        )
        
        # Round-robin assignment initially
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
    
    def _greedy_balanced(self) -> Dict[int, List[str]]:
        """
        Load-balanced greedy strategy
        Try to balance the workload among responders
        """
        assignment = {r.id: [] for r in self.team}
        unchecked_rooms = set(self.building.rooms.keys())
        
        # Track estimated time for each responder
        estimated_times = {r.id: 0.0 for r in self.team}
        positions = {r.id: r.initial_position for r in self.team}
        
        while unchecked_rooms:
            # Find the responder with minimum estimated time
            min_responder_id = min(estimated_times, key=estimated_times.get)
            current_pos = positions[min_responder_id]
            
            # Find nearest room to this responder
            best_room = None
            best_distance = np.inf
            
            for room_id in unchecked_rooms:
                _, distance = self.graph.shortest_path(current_pos, room_id)
                if distance < best_distance:
                    best_distance = distance
                    best_room = room_id
                    
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
            check_time = room.calculate_check_time(
                responder.base_check_time,
                responder.check_rate
            )
            estimated_times[min_responder_id] += travel_time + check_time
            
        return assignment
    
    def _optimize_path_order(self, start_position: str, room_ids: List[str]) -> List[str]:
        """
        Optimize order of rooms using nearest neighbor heuristic
        
        Args:
            start_position: Starting position
            room_ids: List of room IDs to visit
            
        Returns:
            Optimized order of room IDs
        """
        if len(room_ids) <= 1:
            return room_ids
            
        unvisited = set(room_ids)
        ordered = []
        current = start_position
        
        while unvisited:
            # Find nearest unvisited room
            nearest = None
            nearest_dist = np.inf
            
            for room_id in unvisited:
                _, dist = self.graph.shortest_path(current, room_id)
                if dist < nearest_dist:
                    nearest_dist = dist
                    nearest = room_id
                    
            if nearest is None:
                # Add remaining rooms in any order
                ordered.extend(list(unvisited))
                break
                
            ordered.append(nearest)
            unvisited.remove(nearest)
            current = nearest
            
        return ordered
    
    def get_team(self) -> ResponderTeam:
        """Get the responder team"""
        return self.team

