import random
from copy import deepcopy
import math
from time import time
import numpy as np
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import logging

class Node:
    def __init__(self, game_state, parent=None):
        self.game_state = game_state
        self.parent = parent
        self.children = []
        self.wins = 0
        self.visits = 0
        self.untried_moves = self._get_possible_moves()
        
    def _get_possible_moves(self):
        moves = []
        for row in range(4):
            for col in range(4):
                try:
                    game_copy = deepcopy(self.game_state)
                    game_copy.place_selected_piece(row, col)
                    moves.append((row, col))
                except ValueError:
                    continue
        return moves

class Individual:
    def __init__(self, strategy_genes=None):
        if strategy_genes is None:
            # Initialize random genes for piece selection and placement
            self.strategy_genes = np.random.random(32)  # 16 for piece selection, 16 for placement
        else:
            self.strategy_genes = strategy_genes
        self.fitness = 0

    def mutate(self, mutation_rate=0.1):
        """Mutate the genes with given probability"""
        for i in range(len(self.strategy_genes)):
            if random.random() < mutation_rate:
                self.strategy_genes[i] = random.random()

def crossover(parent1, parent2):
    """Perform uniform crossover between two parents"""
    child_genes = []
    for g1, g2 in zip(parent1.strategy_genes, parent2.strategy_genes):
        if random.random() < 0.5:
            child_genes.append(g1)
        else:
            child_genes.append(g2)
    return Individual(np.array(child_genes))

class AIPlayer:
    def __init__(self, strategy='simple'):
        self.strategy = strategy
        self.simulation_time = 1  # seconds to run MCTS
        self.population_size = 50
        self.generations = 20
        self.tournament_size = 5
        self.population = [Individual() for _ in range(self.population_size)]
        self.best_individual = None
        self.logger = logging.getLogger('quarto_debug')
        
        self.logger.debug(f"Initializing AI player with strategy: {strategy}")
        if strategy == 'evolutionary':
            self._evolve_strategy()

    def select_piece(self, game):
        self.logger.debug(f"\nAI selecting piece using {self.strategy} strategy")
        if self.strategy == 'simple':
            piece_idx = self._simple_select_piece(game)
        elif self.strategy == 'mcts':
            piece_idx = self._mcts_select_piece(game)
        elif self.strategy == 'evolutionary':
            piece_idx = self._evolutionary_select_piece(game)
        else:
            piece_idx = self._minimax_select_piece(game)
            
        selected_piece = game.available_pieces[piece_idx]
        self.logger.debug(f"AI selected piece: {selected_piece}")
        return piece_idx

    def make_move(self, game):
        self.logger.debug(f"\nAI making move using {self.strategy} strategy")
        if self.strategy == 'simple':
            move = self._simple_make_move(game)
        elif self.strategy == 'mcts':
            move = self._mcts_make_move(game)
        elif self.strategy == 'evolutionary':
            move = self._evolutionary_make_move(game)
        else:
            move = self._minimax_make_move(game)
            
        self.logger.debug(f"AI chose position: {move}")
        return move

    def _simple_select_piece(self, game):
        """Simple strategy: randomly select an available piece"""
        return random.randint(0, len(game.available_pieces) - 1)
    
    def _simple_make_move(self, game):
        """Simple strategy: place piece in first available position"""
        for row in range(4):
            for col in range(4):
                try:
                    game_copy = deepcopy(game)
                    game_copy.place_selected_piece(row, col)
                    return row, col
                except ValueError:
                    continue
        return None
        
    def _minimax_select_piece(self, game, depth=2):
        self.logger.debug("Starting minimax piece selection...")
        best_score = float('-inf')
        best_piece = 0
        
        for i in range(len(game.available_pieces)):
            game_copy = deepcopy(game)
            game_copy.select_piece(i)
            score = self._minimax(game_copy, depth, False)
            self.logger.debug(f"Piece {i} ({game.available_pieces[i]}) score: {score}")
            if score > best_score:
                best_score = score
                best_piece = i
                
        self.logger.debug(f"Minimax selected piece {best_piece} with score {best_score}")
        return best_piece
    
    def _minimax_make_move(self, game, depth=2):
        self.logger.debug("Starting minimax move selection...")
        best_score = float('-inf')
        best_move = None
        
        for row in range(4):
            for col in range(4):
                try:
                    game_copy = deepcopy(game)
                    game_copy.place_selected_piece(row, col)
                    score = self._minimax(game_copy, depth, False)
                    self.logger.debug(f"Position ({row}, {col}) score: {score}")
                    if score > best_score:
                        best_score = score
                        best_move = (row, col)
                except ValueError:
                    continue
                    
        self.logger.debug(f"Minimax selected move {best_move} with score {best_score}")
        return best_move
    
    def _minimax(self, game, depth, is_maximizing):
        """Minimax algorithm implementation"""
        if depth == 0 or game.is_game_over():
            return self._evaluate_position(game)
            
        if is_maximizing:
            max_score = float('-inf')
            for row in range(4):
                for col in range(4):
                    try:
                        game_copy = deepcopy(game)
                        game_copy.place_selected_piece(row, col)
                        score = self._minimax(game_copy, depth - 1, False)
                        max_score = max(max_score, score)
                    except ValueError:
                        continue
            return max_score
        else:
            min_score = float('inf')
            for row in range(4):
                for col in range(4):
                    try:
                        game_copy = deepcopy(game)
                        game_copy.place_selected_piece(row, col)
                        score = self._minimax(game_copy, depth - 1, True)
                        min_score = min(min_score, score)
                    except ValueError:
                        continue
            return min_score
    
    def _evaluate_position(self, game):
        """Evaluate the current game position"""
        if game.check_win():
            return 1 if game.current_player == 0 else -1
        return 0
    
    def _mcts_select_piece(self, game):
        """MCTS strategy for selecting a piece using parallel processing"""
        available_pieces = list(range(len(game.available_pieces)))
        if not available_pieces:
            return None

        max_workers = min(32, (os.cpu_count() or 1) * 2)
        piece_results = {piece: 0 for piece in available_pieces}
        simulations_per_piece = 10
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for piece in available_pieces:
                for _ in range(simulations_per_piece):
                    futures.append(
                        executor.submit(
                            self._parallel_piece_simulation,
                            deepcopy(game),
                            piece
                        )
                    )
            
            for future in as_completed(futures):
                piece, result = future.result()
                if result == 1:  # Victoria para la IA
                    piece_results[piece] += 1

        return max(piece_results.items(), key=lambda x: x[1])[0]

    def _parallel_piece_simulation(self, game, piece):
        """Ejecuta una simulación paralela para la selección de pieza"""
        game.select_piece(piece)
        result = self._simulate_random_game(game)
        return piece, result

    def _mcts_make_move(self, game):
        self.logger.debug("Starting MCTS move selection...")
        root = Node(deepcopy(game))
        end_time = time() + self.simulation_time
        max_workers = min(32, (os.cpu_count() or 1) * 2)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            while time() < end_time:
                futures = []
                for _ in range(max_workers):
                    futures.append(executor.submit(self._parallel_mcts_iteration, root))
                
                for future in as_completed(futures):
                    if time() >= end_time:
                        break

        # Select the move with the highest number of visits
        if root.children:
            best_child = max(root.children, key=lambda c: c.visits)
            self.logger.debug(f"MCTS stats - Total simulations: {root.visits}")
            for child in root.children:
                win_rate = child.wins / child.visits if child.visits > 0 else 0
                self.logger.debug(f"Move option - Visits: {child.visits}, Win rate: {win_rate:.2f}")

            for row in range(4):
                for col in range(4):
                    try:
                        game_copy = deepcopy(game)
                        game_copy.place_selected_piece(row, col)
                        if game_copy.board == best_child.game_state.board:
                            return row, col
                    except ValueError:
                        continue
        
        self.logger.debug("MCTS fallback to simple strategy")
        return self._simple_make_move(game)

    def _parallel_mcts_iteration(self, root):
        """Ejecuta una iteración de MCTS en paralelo"""
        node = self._select(root)
        if node.untried_moves:
            child = self._expand(node)
            result = self._simulate(child)
            self._backpropagate(child, result)
        return True

    def _select(self, node):
        """Select a leaf node using UCT formula"""
        while node.children and not node.untried_moves:
            node = max(node.children, key=lambda n: 
                n.wins/n.visits + math.sqrt(2*math.log(n.parent.visits)/n.visits))
        return node

    def _expand(self, node):
        """Expand the tree by creating a new child node"""
        if not node.untried_moves:
            return node
        move = random.choice(node.untried_moves)
        node.untried_moves.remove(move)
        
        new_state = deepcopy(node.game_state)
        row, col = move
        new_state.place_selected_piece(row, col)
        
        child = Node(new_state, parent=node)
        node.children.append(child)
        return child

    def _simulate(self, node):
        """Run a random simulation from the node"""
        return self._simulate_random_game(deepcopy(node.game_state))

    def _simulate_random_game(self, game):
        """Play random moves until game is over"""
        while True:
            # Check if game is won before making any moves
            if game.check_win():
                return 1 if game.current_player == 1 else -1
            
            if game.board.is_full():
                return 0
                
            moves = []
            for row in range(4):
                for col in range(4):
                    try:
                        game_copy = deepcopy(game)
                        game_copy.place_selected_piece(row, col)
                        moves.append((row, col))
                    except ValueError:
                        continue
            
            if not moves:
                break
                
            row, col = random.choice(moves)
            game.place_selected_piece(row, col)
            
            if len(game.available_pieces) > 0:
                piece = random.randint(0, len(game.available_pieces) - 1)
                game.select_piece(piece)
        
        return 0

    def _backpropagate(self, node, result):
        """Backpropagate the result up the tree"""
        while node:
            node.visits += 1
            node.wins += result
            node = node.parent

    def _evolve_strategy(self):
        """Evolve the population through multiple generations"""
        for generation in range(self.generations):
            # Evaluate fitness for each individual
            for individual in self.population:
                individual.fitness = self._evaluate_individual(individual)
            
            # Selection and breeding
            new_population = []
            while len(new_population) < self.population_size:
                parent1 = self._tournament_select()
                parent2 = self._tournament_select()
                child = crossover(parent1, parent2)
                child.mutate()
                new_population.append(child)
                
            self.population = new_population
            self.best_individual = max(self.population, key=lambda x: x.fitness)

    def _tournament_select(self):
        """Select an individual using tournament selection"""
        tournament = random.sample(self.population, self.tournament_size)
        return max(tournament, key=lambda x: x.fitness)

    def _evaluate_individual(self, individual):
        """Evaluate an individual by playing games"""
        wins = 0
        games = 5  # Number of games to evaluate fitness
        
        for _ in range(games):
            game = deepcopy(self._create_new_game())
            result = self._play_game_with_strategy(game, individual)
            if result == 1:
                wins += 1
                
        return wins / games

    def _evolutionary_select_piece(self, game):
        """Use evolved strategy to select a piece"""
        if not self.best_individual:
            return self._simple_select_piece(game)
            
        available_pieces = list(range(len(game.available_pieces)))
        if not available_pieces:
            return None
            
        # Use the first 16 genes for piece selection
        piece_preferences = self.best_individual.strategy_genes[:16]
        piece_scores = []
        
        for piece in available_pieces:
            piece_score = piece_preferences[piece]
            # Add heuristic information
            game_copy = deepcopy(game)
            game_copy.select_piece(piece)
            if self._leads_to_win(game_copy):
                piece_score += 1.0
                
            piece_scores.append((piece_score, piece))
            
        return max(piece_scores, key=lambda x: x[0])[1]

    def _evolutionary_make_move(self, game):
        """Use evolved strategy to make a move"""
        if not self.best_individual:
            return self._simple_make_move(game)
            
        # Use the last 16 genes for move placement (4x4 board)
        placement_preferences = self.best_individual.strategy_genes[16:].reshape(4, 4)
        best_score = float('-inf')
        best_move = None
        
        for row in range(4):
            for col in range(4):
                try:
                    game_copy = deepcopy(game)
                    game_copy.place_selected_piece(row, col)
                    
                    score = placement_preferences[row][col]
                    # Add heuristic information
                    if game_copy.check_win():
                        score += 1.0
                    elif self._creates_winning_opportunity(game_copy):
                        score -= 0.5
                        
                    if score > best_score:
                        best_score = score
                        best_move = (row, col)
                except ValueError:
                    continue
                    
        return best_move

    def _leads_to_win(self, game):
        """Check if the current state leads to an immediate win"""
        for row in range(4):
            for col in range(4):
                try:
                    game_copy = deepcopy(game)
                    game_copy.place_selected_piece(row, col)
                    if game_copy.check_win():
                        return True
                except ValueError:
                    continue
        return False

    def _creates_winning_opportunity(self, game):
        """Check if the move creates a winning opportunity for the opponent"""
        if len(game.available_pieces) == 0:
            return False
            
        for piece in range(len(game.available_pieces)):
            game_copy = deepcopy(game)
            game_copy.select_piece(piece)
            if self._leads_to_win(game_copy):
                return True
        return False

    def _create_new_game(self):
        """Create a new game instance for evaluation"""
        from .game import Game
        return Game()

    def _play_game_with_strategy(self, game, individual):
        """Play a game using the evolved strategy from an individual"""
        while not game.is_game_over():
            try:
                # Use evolved strategy for piece selection
                if len(game.available_pieces) > 0:
                    piece_idx = self._evolutionary_select_piece(game)
                    if piece_idx is not None:
                        game.select_piece(piece_idx)
                
                # Use evolved strategy for move placement
                if game.selected_piece is not None:
                    move = self._evolutionary_make_move(game)
                    if move is not None:
                        row, col = move
                        game.place_selected_piece(row, col)
                        
                        if game.check_win():
                            return 1  # Win
                    else:
                        return 0  # Draw
                
            except ValueError:
                continue
                
        return 0  # Draw if game ends without winning