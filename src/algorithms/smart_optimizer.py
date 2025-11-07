"""
Smart Optimizer - Automatically selects the best strategy based on building characteristics
"""

from typing import Dict, List
from ..models.building import Building
from ..models.responder import ResponderTeam
from .greedy import GreedyOptimizer


class SmartOptimizer:
    """
    Intelligently selects optimization strategy based on building characteristics
    """
    
    def __init__(self, building: Building, n_responders: int = 2,
                 initial_positions: List[str] = None,
                 capabilities: dict = None):
        """
        Initialize smart optimizer
        
        Args:
            building: Building instance
            n_responders: Number of responders
            initial_positions: Initial positions for responders
            capabilities: Responder capabilities
        """
        self.building = building
        self.n_responders = n_responders
        self.initial_positions = initial_positions
        self.capabilities = capabilities
        
        # Analyze building and select strategy
        self.selected_strategy = self._select_strategy()
        
        # Create optimizer with selected strategy
        self.optimizer = GreedyOptimizer(
            building,
            n_responders,
            initial_positions,
            capabilities,
            strategy=self.selected_strategy
        )
        
    def _select_strategy(self) -> str:
        """
        Analyze building characteristics and select best strategy
        
        Returns:
            Strategy name: 'nearest', 'priority', or 'balanced'
        """
        rooms = list(self.building.rooms.values())
        
        # Count high priority rooms
        high_priority_rooms = [r for r in rooms if r.priority >= 2]
        high_priority_ratio = len(high_priority_rooms) / len(rooms) if rooms else 0
        
        # Count very high priority rooms (critical)
        critical_rooms = [r for r in rooms if r.priority >= 3]
        critical_ratio = len(critical_rooms) / len(rooms) if rooms else 0
        
        # Check for high complexity rooms
        complex_rooms = [r for r in rooms if r.check_complexity > 1.5]
        complex_ratio = len(complex_rooms) / len(rooms) if rooms else 0
        
        # Decision logic
        reasons = []
        
        # Strategy 1: Priority-first
        # Use when there are significant high-priority or critical rooms
        if critical_ratio > 0.2:  # More than 20% critical rooms
            reasons.append(f"{critical_ratio*100:.0f}% of rooms are critical priority (priority ≥ 3)")
            strategy = "priority"
        elif high_priority_ratio > 0.3:  # More than 30% high priority
            reasons.append(f"{high_priority_ratio*100:.0f}% of rooms have high priority (priority ≥ 2)")
            strategy = "priority"
        elif len(critical_rooms) > 0:  # Any critical room exists
            reasons.append(f"Building contains {len(critical_rooms)} critical priority room(s)")
            strategy = "priority"
        
        # Strategy 2: Balanced (default for uniform buildings)
        else:
            if high_priority_ratio == 0:
                reasons.append("All rooms have equal priority")
            else:
                reasons.append(f"Only {high_priority_ratio*100:.0f}% high priority rooms - not enough to prioritize")
            
            if len(rooms) > 10:
                reasons.append(f"Large building ({len(rooms)} rooms) benefits from load balancing")
            
            strategy = "balanced"
        
        # Store analysis results
        self.analysis = {
            'strategy': strategy,
            'reasons': reasons,
            'stats': {
                'total_rooms': len(rooms),
                'high_priority_rooms': len(high_priority_rooms),
                'critical_rooms': len(critical_rooms),
                'complex_rooms': len(complex_rooms),
                'high_priority_ratio': high_priority_ratio,
                'critical_ratio': critical_ratio,
                'complex_ratio': complex_ratio
            }
        }
        
        return strategy
    
    def optimize(self) -> Dict[int, List[str]]:
        """
        Run optimization with selected strategy
        
        Returns:
            Room assignment dictionary
        """
        return self.optimizer.optimize()
    
    def get_team(self) -> ResponderTeam:
        """Get the responder team"""
        return self.optimizer.get_team()
    
    def get_analysis(self) -> Dict:
        """
        Get strategy selection analysis
        
        Returns:
            Dictionary with strategy and reasoning
        """
        return self.analysis
    
    def print_analysis(self):
        """Print strategy selection analysis"""
        print("\n" + "="*70)
        print("SMART OPTIMIZER - STRATEGY SELECTION")
        print("="*70)
        
        print(f"\nBuilding: {self.building.name}")
        print(f"Rooms: {self.analysis['stats']['total_rooms']}")
        print(f"High Priority Rooms: {self.analysis['stats']['high_priority_rooms']}")
        print(f"Critical Priority Rooms: {self.analysis['stats']['critical_rooms']}")
        
        print(f"\n✓ Selected Strategy: {self.selected_strategy.upper()}")
        
        print("\nReasoning:")
        for i, reason in enumerate(self.analysis['reasons'], 1):
            print(f"  {i}. {reason}")
        
        print("="*70 + "\n")

