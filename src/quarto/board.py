class Board:
    def __init__(self):
        self.size = 4
        self.board = [[None for _ in range(self.size)] for _ in range(self.size)]
        
    def place_piece(self, piece, row, col):
        if not (0 <= row < self.size and 0 <= col < self.size):
            raise ValueError("Invalid position")
        if self.board[row][col] is not None:
            raise ValueError("Position already occupied")
        self.board[row][col] = piece
        
    def get_piece(self, row, col):
        if not (0 <= row < self.size and 0 <= col < self.size):
            raise ValueError("Invalid position")
        return self.board[row][col]
    
    def is_full(self):
        return all(all(cell is not None for cell in row) for row in self.board)
    
    def check_win(self):
        # Check rows, columns, and diagonals for winning combinations
        # Will be implemented with the winning logic
        pass