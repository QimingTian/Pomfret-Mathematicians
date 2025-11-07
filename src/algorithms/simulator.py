"""
Simulation engine for building sweep
"""

import numpy as np
from typing import Dict, List
from ..models.building import Building
from ..models.responder import ResponderTeam
from ..models.graph import BuildingGraph


class Simulator:
    """Simulates the building sweep process"""
    
    def __init__(self, building: Building, team: ResponderTeam, 
                 assignment: Dict[int, List[str]]):
        """
        Initialize simulator
        
        Args:
            building: Building instance
            team: ResponderTeam instance
            assignment: Dictionary mapping responder_id -> list of room IDs
        """
        self.building = building
        self.team = team
        self.assignment = assignment
        self.graph = BuildingGraph(building)
        
    def run(self) -> Dict:
        """
        Run the simulation
        
        Returns:
            Dictionary containing simulation results
        """
        # Reset building and team
        self.building.reset_clearance()
        self.team.reset_all()
        
        # Execute each responder's assignment
        for responder in self.team:
            self._execute_path(responder, self.assignment[responder.id])
            
        # Collect results
        results = self._collect_results()
        return results
    
    def _execute_path(self, responder, room_ids: List[str]):
        """
        Execute a responder's path through assigned rooms
        
        Args:
            responder: Responder instance
            room_ids: List of room IDs to check
        """
        current_location = responder.position
        
        for room_id in room_ids:
            # Find path to room
            path, distance = self.graph.shortest_path(current_location, room_id)
            
            if distance == np.inf:
                print(f"Warning: No path from {current_location} to {room_id}")
                continue
                
            # Move to room
            responder.move_to(room_id, distance)
            
            # Check room
            room = self.building.rooms[room_id]
            responder.check_room(room)
            
            current_location = room_id
            
    def _collect_results(self) -> Dict:
        """Collect simulation results"""
        # Get responder paths
        responder_paths = []
        for responder in self.team:
            responder_paths.append({
                'responder_id': responder.id,
                'path': responder.path,
                'timeline': responder.timeline,
                'total_time': responder.current_time,
                'rooms_checked': responder.rooms_checked,
                'total_distance': responder.get_total_distance()
            })
            
        # Get room clearance info
        room_clearance = {}
        for room_id, room in self.building.rooms.items():
            room_clearance[room_id] = {
                'cleared': room.cleared,
                'cleared_at': room.cleared_at,
                'cleared_by': room.cleared_by
            }
            
        # Calculate metrics
        total_time = self.team.get_max_time()
        all_cleared = all(room.cleared for room in self.building.rooms.values())
        
        clearance_times = [room.cleared_at for room in self.building.rooms.values() 
                          if room.cleared_at is not None]
        avg_clearance_time = np.mean(clearance_times) if clearance_times else 0
        
        responder_times = [r.current_time for r in self.team]
        load_balance = 1.0 - (np.std(responder_times) / np.mean(responder_times)) if responder_times else 1.0
        
        # Check redundancy
        room_check_counts = {}
        for responder in self.team:
            for room_id in responder.rooms_checked:
                room_check_counts[room_id] = room_check_counts.get(room_id, 0) + 1
        redundancy_coverage = sum(1 for count in room_check_counts.values() if count > 1) / len(self.building.rooms)
        
        results = {
            'success': all_cleared,
            'total_time': total_time,
            'responder_paths': responder_paths,
            'room_clearance': room_clearance,
            'metrics': {
                'all_rooms_cleared': all_cleared,
                'average_clearance_time': avg_clearance_time,
                'load_balance': load_balance,
                'redundancy_coverage': redundancy_coverage,
                'total_distance_traveled': self.team.get_total_distance(),
                'n_responders': len(self.team),
                'n_rooms': len(self.building.rooms)
            }
        }
        
        return results
    
    @staticmethod
    def run_quick(building: Building, team: ResponderTeam, 
                  assignment: Dict[int, List[str]]) -> Dict:
        """
        Quick static method to run simulation
        
        Args:
            building: Building instance
            team: ResponderTeam instance
            assignment: Room assignment dictionary
            
        Returns:
            Simulation results
        """
        simulator = Simulator(building, team, assignment)
        return simulator.run()

