import pygame
from game.grid_game import GridWorldGame
from game.ui import show_main_menu, show_end_screen

def main():
    while True:
        
        layout_path = show_main_menu()
        
        
        game = GridWorldGame(layout_path)
        
        # Main gameplay loop
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                elif event.type == pygame.KEYDOWN:
                    game.step_from_input(event.key)

            game.render()

            
            if game.outcome:
                running = False

        
        show_end_screen(game.outcome, game.score)

if __name__ == "__main__":
    main()