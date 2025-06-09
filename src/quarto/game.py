from .board import Board
from .piece import Piece
from itertools import product

class Game:
    def __init__(self):
        self.board = Board()
        self.available_pieces = self._create_pieces()
        self.selected_piece = None
        self.current_player = 0  # 0 or 1
        
    def _create_pieces(self):
        pieces = []
        # Create all 16 possible combinations of piece attributes
        for height, solidity, shape, color in product([True, False], repeat=4):
            pieces.append(Piece(height, solidity, shape, color))
        return pieces
    
    def select_piece(self, piece_index):
        if not 0 <= piece_index < len(self.available_pieces):
            raise ValueError("Invalid piece index")
        self.selected_piece = self.available_pieces.pop(piece_index)
        
    def place_selected_piece(self, row, col):
        if self.selected_piece is None:
            raise ValueError("No piece selected")
        self.board.place_piece(self.selected_piece, row, col)
        self.selected_piece = None
        self.current_player = 1 - self.current_player  # Switch players
        
    def check_win(self):
        # Check all rows, columns, and diagonals
        for i in range(4):
            # Check rows
            if self._check_line([self.board.get_piece(i, j) for j in range(4)]):
                return True
            # Check columns
            if self._check_line([self.board.get_piece(j, i) for j in range(4)]):
                return True
                
        # Check diagonals
        if self._check_line([self.board.get_piece(i, i) for i in range(4)]):
            return True
        if self._check_line([self.board.get_piece(i, 3-i) for i in range(4)]):
            return True
            
        return False
        
    def _check_line(self, pieces):
        if None in pieces:
            return False
        # Check each attribute
        for attr in ['height', 'solidity', 'shape', 'color']:
            if all(getattr(p, attr) for p in pieces) or \
               not any(getattr(p, attr) for p in pieces):
                return True
        return False
        
    def is_game_over(self):
        return self.check_win() or self.board.is_full()