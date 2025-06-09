from .game import Game
from .ai_player import AIPlayer
from .board_gui import BoardGUI, StartForm
from tkinter import messagebox
import logging

def setup_debug_logger():
    logger = logging.getLogger('quarto_debug')
    logger.setLevel(logging.DEBUG)
    
    # Create console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    ch.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(ch)
    return logger

def main():
    # Setup debug logger
    debug_logger = setup_debug_logger()
    
    # Show start form and get selected mode
    start_form = StartForm()
    selected_mode = start_form.show()
    
    # Exit if no mode was selected
    if not selected_mode:
        return
    
    debug_logger.debug(f"Game started with AI mode: {selected_mode}")
    
    # Create game instances
    game = Game()
    ai_player = AIPlayer(strategy=selected_mode)
    board_gui = BoardGUI()
    
    # Initial board update to show available pieces
    board_gui.update_board(game)

    def on_piece_selected(event):
        try:
            # Only allow piece selection if no piece is currently selected
            if game.selected_piece is not None:
                debug_logger.debug("Piece already selected - ignoring selection")
                return

            index = event.state
            selected_piece = game.available_pieces[index]
            debug_logger.debug(f"\nHuman selected piece for AI: {selected_piece}")
            
            # When human selects a piece, it's always for the AI
            game.select_piece(index)
            board_gui.update_board(game)
            
            # AI immediately places the piece
            row, col = ai_player.make_move(game)
            debug_logger.debug(f"AI placed piece at position: ({row}, {col})")
            game.place_selected_piece(row, col)
            board_gui.update_board(game)
            
            if game.check_win():
                debug_logger.debug("Game Over - AI wins!")
                board_gui.show_game_over("AI")
                return
            elif game.board.is_full():
                debug_logger.debug("Game Over - Draw!")
                board_gui.show_draw()
                return
            
            # AI selects a piece for the human
            piece_idx = ai_player.select_piece(game)
            selected_piece = game.available_pieces[piece_idx]
            debug_logger.debug(f"AI selected piece for Human: {selected_piece}")
            game.select_piece(piece_idx)
            board_gui.update_board(game)
            # Disable piece selection until human places their piece
            board_gui.disable_piece_selection()
            messagebox.showinfo("AI's Turn", "AI has placed its piece and selected a piece for you.\nNow place this piece on the board.")
            
        except ValueError as e:
            debug_logger.error(f"Error: {str(e)}")
            messagebox.showerror("Error", str(e))
    
    def on_board_click(row, col):
        if game.selected_piece is None:
            debug_logger.debug("No piece selected yet")
            return
            
        try:
            debug_logger.debug(f"\nHuman placing piece at position: ({row}, {col})")
            # Human places their piece
            game.place_selected_piece(row, col)
            board_gui.update_board(game)
            
            if game.check_win():
                debug_logger.debug("Game Over - Human wins!")
                board_gui.show_game_over("Human")
                return
            elif game.board.is_full():
                debug_logger.debug("Game Over - Draw!")
                board_gui.show_draw()
                return
                
            debug_logger.debug("Human's turn complete - enabling piece selection for AI")
            # Now enable piece selection for AI
            board_gui.enable_piece_selection()
            messagebox.showinfo("Your Turn", "Now select a piece for the AI to place.")
                
        except ValueError as e:
            debug_logger.error(f"Error: {str(e)}")
            messagebox.showerror("Error", str(e))
    
    # Connect GUI events
    board_gui.canvas.bind('<Button-1>', lambda e: on_board_click(e.y // 120, e.x // 120))
    board_gui.window.bind('<<PieceSelected>>', on_piece_selected)
    
    # Show initial instruction
    debug_logger.debug("Game initialized - waiting for first move")
    # Start the game by having AI select first piece for human
    piece_idx = ai_player.select_piece(game)
    selected_piece = game.available_pieces[piece_idx]
    debug_logger.debug(f"AI selected initial piece for Human: {selected_piece}")
    game.select_piece(piece_idx)
    board_gui.update_board(game)
    board_gui.disable_piece_selection()  # Disable piece selection until first piece is placed
    messagebox.showinfo("Game Start", "Place your piece on the board.")
    
    board_gui.window.mainloop()

if __name__ == "__main__":
    main()