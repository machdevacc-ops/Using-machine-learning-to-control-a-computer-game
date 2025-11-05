import pygame
import os
import sys
from game.layout_loader import load_scores

def show_main_menu():
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("Select Map")
    font = pygame.font.SysFont(None, 36)
    fontLarge = pygame.font.SysFont(None, 72)

    layout_dir = "level_layouts"
    maps = [f for f in os.listdir(layout_dir) if f.endswith(".txt")]
    if not maps:
        print("No map files found.")
        pygame.quit()
        sys.exit()

    selected = 0
    clock = pygame.time.Clock()

    scores = load_scores()
    selected = 0
    clock = pygame.time.Clock()

    while True:
        title = fontLarge.render("the Kings Cleaner", True, (255, 255, 255))
        title_rect = title.get_rect(center=(screen.get_width() // 2, 40))
        screen.blit(title, title_rect)

        info = font.render("You have been selected to clean the Kings dungeon", True, (255, 255, 255))
        info_rect = info.get_rect(center=(screen.get_width() // 2 , 80))
        screen.blit(info, info_rect)

        info2 = font.render("collect trash and kill any remaining slimes", True, (255, 255, 255))
        info2_rect = info2.get_rect(center=(screen.get_width() // 2, 120))
        screen.blit(info2, info2_rect)

        info3 = font.render("make sure to avoid poisonous clouds and slimes movements", True, (255, 255, 255))
        info3_rect = info3.get_rect(center=(screen.get_width() // 2, 160))
        screen.blit(info3, info3_rect)

        info4 = font.render("once cleaned exit via staircase", True, (255, 255, 255))
        info4_rect = info4.get_rect(center=(screen.get_width() // 2, 200))
        screen.blit(info4, info4_rect)

        info5 = font.render("WASD to move, spacebar to attack", True, (255, 255, 255))
        info5_rect = info5.get_rect(center=(screen.get_width() // 2, 240))
        screen.blit(info5, info5_rect)



        instruction = font.render("Choose a Map, use W/A to select, space to confirm", True, (255, 255, 255))
        instruction_rect = instruction.get_rect(center=(screen.get_width() // 2, 280))
        screen.blit(instruction, instruction_rect)



        for i, map_name in enumerate(maps):
            color = (255, 255, 0) if i == selected else (200, 200, 200)
            text = font.render(map_name, True, color)
            screen.blit(text, (100, 320 + i * 40))

            # Draw high score next to it
            score = scores.get(map_name, 0)
            score_text = font.render(f"Best score: {score}", True, (180, 180, 180))
            screen.blit(score_text, (600, 320 + i * 40))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_w:
                    selected = (selected - 1) % len(maps)
                elif event.key == pygame.K_s:
                    selected = (selected + 1) % len(maps)
                elif event.key == pygame.K_SPACE:
                    selected_map = os.path.join(layout_dir, maps[selected])
                    return selected_map

        clock.tick(30)

def show_end_screen(outcome, score):
    screen = pygame.display.set_mode((1280, 720))
    font = pygame.font.SysFont(None, 48)
    clock = pygame.time.Clock()

    if outcome == "victory":
        message_text = "You Win!"
    elif outcome == "killed_by_enemy":
        message_text = "You were killed by a slime!"
    elif outcome == "stepped_on_poison":
        message_text = "You stepped on poison!"
    else:
        message_text = "Game Over"

    message = font.render(message_text, True, (255, 255, 255))
    score_text = font.render(f"Score: {score}", True, (200, 200, 0))
    prompt = font.render("Press any key to return to menu.", True, (180, 180, 180))
    message_rect = message.get_rect(center=(screen.get_width() // 2,120))
    score_rect = score_text.get_rect(center=(screen.get_width() // 2,180))
    prompt_rect = prompt.get_rect(center=(screen.get_width() // 2,260))

    while True:
        screen.fill((0, 0, 0))
        screen.blit(message, message_rect)
        screen.blit(score_text, score_rect)
        screen.blit(prompt, prompt_rect)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                return

        clock.tick(30)