"""
Genetic Algorithm for building sweep optimization
"""

import random
import numpy as np
from typing import Dict, List, Tuple
from ..models.building import Building
from ..models.responder import ResponderTeam
from ..models.graph import BuildingGraph
from ..algorithms.simulator import Simulator


class GeneticOptimizer:
    """Genetic algorithm for optimizing room assignments"""
    
    def __init__(self, building: Building, n_responders: int = 2,
                 initial_positions: List[str] = None,
                 capabilities: dict = None,
                 population_size: int = 50,
                 generations: int = 100,
                 mutation_rate: float = 0.1,
                 crossover_rate: float = 0.7):
        """
        Initialize genetic optimizer
        
        Args:
            building: Building instance
            n_responders: Number of responders
            initial_positions: Initial positions for responders
            capabilities: Responder capabilities
            population_size: Size of population
            generations: Number of generations to evolve
            mutation_rate: Probability of mutation
            crossover_rate: Probability of crossover
        """
        self.building = building
        self.n_responders = n_responders
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        
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
        
        self.room_ids = list(building.rooms.keys())
        self.best_solution = None
        self.best_fitness = float('inf')
        self.fitness_history = []
        
    def optimize(self) -> Dict[int, List[str]]:
        """
        Run genetic algorithm optimization
        
        Returns:
            Best assignment found
        """
        # Initialize population
        population = self._initialize_population()
        
        for generation in range(self.generations):
            # Evaluate fitness
            fitness_scores = [self._evaluate_fitness(ind) for ind in population]
            
            # Track best
            min_fitness_idx = np.argmin(fitness_scores)
            if fitness_scores[min_fitness_idx] < self.best_fitness:
                self.best_fitness = fitness_scores[min_fitness_idx]
                self.best_solution = population[min_fitness_idx].copy()
                
            self.fitness_history.append(self.best_fitness)
            
            # Selection
            selected = self._selection(population, fitness_scores)
            
            # Crossover and mutation
            next_population = []
            for i in range(0, len(selected), 2):
                parent1 = selected[i]
                parent2 = selected[i+1] if i+1 < len(selected) else selected[0]
                
                if random.random() < self.crossover_rate:
                    child1, child2 = self._crossover(parent1, parent2)
                else:
                    child1, child2 = parent1.copy(), parent2.copy()
                    
                if random.random() < self.mutation_rate:
                    child1 = self._mutate(child1)
                if random.random() < self.mutation_rate:
                    child2 = self._mutate(child2)
                    
                next_population.extend([child1, child2])
                
            population = next_population[:self.population_size]
            
        # Convert best solution to assignment dictionary
        return self._chromosome_to_assignment(self.best_solution)
    
    def _initialize_population(self) -> List[List[int]]:
        """
        Initialize population with random chromosomes
        
        Chromosome encoding: list of room indices with responder separators
        Example: [r1, r2, -1, r3, r4, -1] means responder 1 checks r1,r2 and responder 2 checks r3,r4
        """
        population = []
        
        for _ in range(self.population_size):
            # Random permutation of rooms
            chromosome = list(range(len(self.room_ids)))
            random.shuffle(chromosome)
            population.append(chromosome)
            
        return population
    
    def _chromosome_to_assignment(self, chromosome: List[int]) -> Dict[int, List[str]]:
        """Convert chromosome to assignment dictionary"""
        assignment = {i+1: [] for i in range(self.n_responders)}
        
        # Divide rooms among responders
        rooms_per_responder = len(chromosome) // self.n_responders
        
        for i, room_idx in enumerate(chromosome):
            responder_id = min(i // rooms_per_responder, self.n_responders - 1) + 1
            assignment[responder_id].append(self.room_ids[room_idx])
            
        return assignment
    
    def _evaluate_fitness(self, chromosome: List[int]) -> float:
        """
        Evaluate fitness of a chromosome (lower is better)
        
        Args:
            chromosome: Chromosome to evaluate
            
        Returns:
            Fitness score (total sweep time)
        """
        assignment = self._chromosome_to_assignment(chromosome)
        
        # Quick simulation
        try:
            results = Simulator.run_quick(self.building, self.team, assignment)
            fitness = results['total_time']
            
            # Penalty for unbalanced load
            times = [path['total_time'] for path in results['responder_paths']]
            load_imbalance = np.std(times)
            fitness += load_imbalance * 2  # Penalty factor
            
            return fitness
        except:
            return float('inf')
    
    def _selection(self, population: List[List[int]], 
                   fitness_scores: List[float]) -> List[List[int]]:
        """
        Tournament selection
        
        Args:
            population: Current population
            fitness_scores: Fitness scores
            
        Returns:
            Selected individuals
        """
        selected = []
        tournament_size = 3
        
        for _ in range(len(population)):
            # Random tournament
            contestants_idx = random.sample(range(len(population)), tournament_size)
            contestants_fitness = [fitness_scores[i] for i in contestants_idx]
            winner_idx = contestants_idx[np.argmin(contestants_fitness)]
            selected.append(population[winner_idx].copy())
            
        return selected
    
    def _crossover(self, parent1: List[int], 
                   parent2: List[int]) -> Tuple[List[int], List[int]]:
        """
        Order crossover (OX) for permutation chromosomes
        
        Args:
            parent1: First parent
            parent2: Second parent
            
        Returns:
            Two offspring
        """
        size = len(parent1)
        
        # Random crossover points
        cx_point1 = random.randint(0, size - 1)
        cx_point2 = random.randint(cx_point1 + 1, size)
        
        # Create offspring
        child1 = [-1] * size
        child2 = [-1] * size
        
        # Copy segment from parents
        child1[cx_point1:cx_point2] = parent1[cx_point1:cx_point2]
        child2[cx_point1:cx_point2] = parent2[cx_point1:cx_point2]
        
        # Fill remaining positions
        self._fill_child(child1, parent2, cx_point2)
        self._fill_child(child2, parent1, cx_point2)
        
        return child1, child2
    
    def _fill_child(self, child: List[int], parent: List[int], start_pos: int):
        """Helper function for crossover"""
        size = len(child)
        child_set = set(child) - {-1}
        
        pos = start_pos
        for gene in parent[start_pos:] + parent[:start_pos]:
            if gene not in child_set:
                child[pos % size] = gene
                child_set.add(gene)
                pos += 1
                
    def _mutate(self, chromosome: List[int]) -> List[int]:
        """
        Swap mutation
        
        Args:
            chromosome: Chromosome to mutate
            
        Returns:
            Mutated chromosome
        """
        mutant = chromosome.copy()
        
        # Swap two random positions
        idx1, idx2 = random.sample(range(len(mutant)), 2)
        mutant[idx1], mutant[idx2] = mutant[idx2], mutant[idx1]
        
        return mutant
    
    def get_team(self) -> ResponderTeam:
        """Get the responder team"""
        return self.team
    
    def get_fitness_history(self) -> List[float]:
        """Get fitness history over generations"""
        return self.fitness_history

