"""
Top-down sweep strategy for multi-floor buildings
Responders go to top floor first, then sweep downwards
"""

import numpy as np
from typing import Dict, List
import networkx as nx
from ..models.responder import ResponderTeam


class TopDownOptimizer:
    """Optimize sweep strategy starting from top floor"""
    
    def __init__(self, building, n_responders: int = 2,
                 initial_positions: List[str] = None,
                 capabilities: dict = None):
        self.building = building
        self.n_responders = n_responders
        
        # Create responder team
        if initial_positions is None:
            exits = list(building.exits.keys())
            if len(exits) >= n_responders:
                initial_positions = exits[:n_responders]
            else:
                initial_positions = exits * (n_responders // len(exits) + 1)
                initial_positions = initial_positions[:n_responders]
        
        self.team = ResponderTeam(n_responders, initial_positions, capabilities)
    
    def optimize(self) -> Dict[int, List[str]]:
        """
        Optimize with top-down strategy
        
        Returns:
            Assignment dictionary
        """
        if self.building.n_floors == 1:
            # Single floor: use balanced strategy
            return self._optimize_single_floor()
        else:
            # Multi-floor: top-down strategy
            return self._optimize_top_down()
    
    def _optimize_single_floor(self) -> Dict[int, List[str]]:
        """Balanced strategy for single floor"""
        assignment = {r.id: [] for r in self.team}
        rooms = list(self.building.rooms.values())
        
        # Sort by priority then position
        rooms.sort(key=lambda r: (-r.priority, r.position[1], r.position[0]))
        
        # Distribute evenly
        for i, room in enumerate(rooms):
            responder_id = (i % self.n_responders) + 1
            assignment[responder_id].append(room.id)
        
        return assignment
    
    def _optimize_top_down(self) -> Dict[int, List[str]]:
        """
        Top-down sweep strategy for multi-floor buildings
        
        Strategy:
        1. Group rooms by floor
        2. Start from top floor
        3. Each responder gets rooms from top to bottom
        4. Within each floor, balance load
        """
        assignment = {r.id: [] for r in self.team}
        
        # Group rooms by floor (top to bottom)
        floors_desc = sorted(range(1, self.building.n_floors + 1), reverse=True)
        
        # Collect all rooms by floor
        rooms_by_floor = {}
        for floor in floors_desc:
            floor_rooms = [r for r in self.building.rooms.values() if r.floor == floor]
            # Sort by priority within floor
            floor_rooms.sort(key=lambda r: (-r.priority, r.position[1], r.position[0]))
            rooms_by_floor[floor] = floor_rooms
        
        # Distribute rooms top-down, round-robin among responders
        responder_idx = 0
        for floor in floors_desc:
            for room in rooms_by_floor[floor]:
                responder_id = (responder_idx % self.n_responders) + 1
                assignment[responder_id].append(room.id)
                responder_idx += 1
        
        return assignment
    
    def get_team(self):
        """Get responder team"""
        return self.team
    
    def get_strategy_name(self):
        """Get strategy name"""
        return "top_down" if self.building.n_floors > 1 else "balanced"

