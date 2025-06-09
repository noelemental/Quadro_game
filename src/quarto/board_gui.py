import tkinter as tk
from tkinter import ttk, messagebox

class StartForm:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Quarto - Select Game Mode")
        self.window.geometry("400x500")
        
        # Center window on screen
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - 400) // 2
        y = (screen_height - 500) // 2
        self.window.geometry(f"400x500+{x}+{y}")
        
        # Main frame with padding
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, 
                              text="Welcome to Quarto!", 
                              font=('TkDefaultFont', 24, 'bold'))
        title_label.pack(pady=(0, 30))
        
        # Description
        desc_label = ttk.Label(main_frame,
                             text="Select your opponent:",
                             font=('TkDefaultFont', 12))
        desc_label.pack(pady=(0, 20))
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.BOTH, expand=True)
        
        # Style for mode buttons
        style = ttk.Style()
        style.configure('Mode.TButton', font=('TkDefaultFont', 11))
        
        self.selected_mode = None
        self.modes = [
            ("Simple AI", 'simple'),
            ("Minimax AI", 'minimax'),
            ("MCTS AI", 'mcts'),
           # ("Evolutionary AI", 'evolutionary')
        ]
        
        # Create mode buttons
        for i, (label, mode) in enumerate(self.modes):
            btn = ttk.Button(buttons_frame, 
                           text=label,
                           style='Mode.TButton',
                           command=lambda m=mode: self._on_mode_selected(m))
            btn.pack(fill=tk.X, pady=10, padx=40)
        
        # Exit button
        exit_btn = ttk.Button(main_frame, 
                            text="Exit",
                            command=self.window.destroy)
        exit_btn.pack(pady=(20, 0))
        
    def _on_mode_selected(self, mode):
        self.selected_mode = mode
        self.window.quit()
        
    def show(self):
        self.window.mainloop()
        selected = self.selected_mode
        self.window.destroy()
        return selected

class BoardGUI:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Quarto Game")
        self.window.geometry("900x600")
        
        # Center window on screen
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - 900) // 2
        y = (screen_height - 600) // 2
        self.window.geometry(f"900x600+{x}+{y}")
        
        # Make window not resizable
        self.window.resizable(False, False)
        
        # Main frame
        self.main_frame = ttk.Frame(self.window, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Game info frame
        self.info_frame = ttk.Frame(self.main_frame)
        self.info_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.turn_label = ttk.Label(self.info_frame, 
                                  text="Current Turn: Human", 
                                  font=('TkDefaultFont', 12, 'bold'))
        self.turn_label.pack(side=tk.LEFT)
        
        # Board frame
        self.board_frame = ttk.Frame(self.main_frame)
        self.board_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        self.canvas = tk.Canvas(self.board_frame, width=480, height=480, bg='white')
        self.canvas.pack()
        
        # Available pieces section
        self.pieces_frame = ttk.LabelFrame(self.main_frame, text="Available Pieces")
        self.pieces_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Create a container for the pieces area
        self.pieces_container = ttk.Frame(self.pieces_frame)
        self.pieces_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create scrollable canvas for pieces
        self.pieces_scrollbar = ttk.Scrollbar(self.pieces_container)
        self.pieces_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.pieces_canvas = tk.Canvas(
            self.pieces_container,
            width=360,
            highlightthickness=0,
            yscrollcommand=self.pieces_scrollbar.set
        )
        self.pieces_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Configure scrollbar
        self.pieces_scrollbar.configure(command=self.pieces_canvas.yview)

        # Create frame for pieces grid
        self.pieces_grid = ttk.Frame(self.pieces_canvas)
        self.pieces_canvas.create_window(
            (0, 0),
            window=self.pieces_grid,
            anchor='nw',
            width=360
        )

        # Configure grid columns
        self.pieces_grid.grid_columnconfigure(0, weight=1, uniform='col')
        self.pieces_grid.grid_columnconfigure(1, weight=1, uniform='col')

        # Bind events for proper scrolling
        self.pieces_grid.bind('<Configure>', 
            lambda e: self.pieces_canvas.configure(scrollregion=self.pieces_canvas.bbox('all'))
        )
        self.pieces_canvas.bind('<Configure>', 
            lambda e: self.pieces_canvas.itemconfig(
                self.pieces_canvas.find_withtag('all')[0],
                width=e.width
            )
        )
        self.pieces_canvas.bind_all('<MouseWheel>', 
            lambda e: self.pieces_canvas.yview_scroll(-1 * (e.delta // 120), 'units')
        )

        # List to store piece buttons
        self.piece_buttons = []
        self.pieces_enabled = True  # Track if piece selection is enabled

        # Draw the board grid
        for i in range(5):
            # Vertical lines
            self.canvas.create_line(i * 120, 0, i * 120, 480, width=2)
            # Horizontal lines
            self.canvas.create_line(0, i * 120, 480, i * 120, width=2)
        
        self.cells = {}  # Store piece displays
        
        # Bind click events
        self.canvas.bind('<Button-1>', self._on_board_click)
        
        # Selected piece label
        self.selected_piece_label = ttk.Label(self.info_frame, text="Selected Piece: None", 
                                            font=('TkDefaultFont', 12))
        self.selected_piece_label.pack(side=tk.RIGHT)
        
        # Quit button
        quit_btn = ttk.Button(self.info_frame, 
                            text="Quit Game",
                            command=self.window.destroy)
        quit_btn.pack(side=tk.RIGHT, padx=10)

    def _on_board_click(self, event):
        # Convert click coordinates to board position
        col = event.x // 120
        row = event.y // 120
        if 0 <= row < 4 and 0 <= col < 4:
            # This will be handled by the game logic
            pass
            
    def update_board(self, game):
        # Check if window still exists
        try:
            if not self.window.winfo_exists():
                return
                
            # Clear previous pieces
            for widget in self.cells.values():
                if widget.winfo_exists():
                    widget.destroy()
            self.cells.clear()
            
            # Update turn label
            current_player = "Human" if game.current_player == 0 else "AI"
            self.turn_label.config(text=f"Current Turn: {current_player}")
            
            # Display current pieces on board
            for row in range(4):
                for col in range(4):
                    piece = game.board.get_piece(row, col)
                    if piece is not None:
                        self._draw_piece(piece, row, col)
            
            # Update available pieces
            self._update_available_pieces(game)
            
            # Update selected piece
            if game.selected_piece:
                self.selected_piece_label.config(text=f"Selected Piece: {str(game.selected_piece)}")
            else:
                self.selected_piece_label.config(text="Selected Piece: None")
            
            self.window.update()
        except tk.TclError:
            # Window was destroyed
            return

    def _draw_piece(self, piece, row, col):
        frame = ttk.Frame(self.canvas)
        self.cells[(row, col)] = frame
        
        # Create piece visualization using concatenated symbols
        size = "▲" if piece.height else "▼"
        color = "⚫" if piece.color else "⚪"
        fill = "■" if piece.solidity else "□"
        shape = "◼" if piece.shape else "🔵"
        
        piece_display = f"{size}{color}{fill}{shape}"
        
        # Create label with the concatenated symbols
        label = ttk.Label(frame, 
                         text=piece_display,
                         font=('TkDefaultFont', 16, 'bold'))
        label.pack(expand=True, pady=5)
        
        # Place in the grid
        self.canvas.create_window(
            col * 120 + 60,
            row * 120 + 60,
            window=frame,
            width=100,
            height=100
        )
    
    def _update_available_pieces(self, game):
        try:
            if not self.window.winfo_exists():
                return
                
            # Clear previous pieces
            for button in self.piece_buttons:
                if button.winfo_exists():
                    button.destroy()
            self.piece_buttons.clear()
            
            # Clear and reconfigure the scrollable frame
            for widget in self.pieces_grid.winfo_children():
                widget.destroy()
            
            # Configure the style for piece buttons
            style = ttk.Style()
            style.configure('Piece.TButton', 
                          font=('TkDefaultFont', 12),
                          padding=10)
            
            # Add available pieces as buttons in a 2-column grid
            for i, piece in enumerate(game.available_pieces):
                # Create frame for the button to ensure proper sizing
                frame = ttk.Frame(self.pieces_grid)
                frame.grid(row=i // 2, column=i % 2, pady=5, padx=5, sticky='nsew')
                frame.grid_columnconfigure(0, weight=1)
                
                # Create button with piece symbols and description
                symbols = self._get_piece_display(piece)
                description = str(piece)
                btn = ttk.Button(frame, 
                               text=f"{symbols}\n{description}",
                               style='Piece.TButton',
                               width=15,
                               state='normal' if self.pieces_enabled else 'disabled')
                btn.pack(expand=True, fill=tk.BOTH)
                
                # Store the index for the lambda
                idx = i
                btn.config(command=lambda i=idx: self._on_piece_selected(i))
                self.piece_buttons.append(btn)
            
            # Configure grid columns to be equal width
            self.pieces_grid.update_idletasks()
            
        except tk.TclError:
            # Window was destroyed
            return

    def enable_piece_selection(self):
        """Enable piece selection buttons"""
        self.pieces_enabled = True
        for btn in self.piece_buttons:
            try:
                if btn.winfo_exists():
                    btn.configure(state='normal')
            except tk.TclError:
                continue

    def disable_piece_selection(self):
        """Disable piece selection buttons"""
        self.pieces_enabled = False
        for btn in self.piece_buttons:
            try:
                if btn.winfo_exists():
                    btn.configure(state='disabled')
            except tk.TclError:
                continue

    def _on_piece_selected(self, index):
        """Handle piece selection and generate event with piece index"""
        self.window.event_generate('<<PieceSelected>>', when='tail', state=index)

    def _get_piece_display(self, piece):
        if piece is None:
            return "·"
        
        size = "▲" if piece.height else "▼"
        color = "⚫" if piece.color else "⚪"
        fill = "■" if piece.solidity else "□"
        shape = "◼" if piece.shape else "●"
        
        return f"{size}{color}{fill}{shape}"
    
    def show_game_over(self, winner):
        try:
            if self.window.winfo_exists():
                messagebox.showinfo("Game Over", f"Game Over - {winner} wins!")
        except tk.TclError:
            pass
    
    def show_draw(self):
        try:
            if self.window.winfo_exists():
                messagebox.showinfo("Game Over", "Game Over - It's a draw!")
        except tk.TclError:
            pass