import pygame
import sys
import json
import os
from pathlib import Path
from engine.loader import (
    load_cursor, load_textures, generate_background_grid, determine_tree_texture, render_background, enemy_type_mapping, npc_type_mapping, statue_type_mapping, load_grass_textures, draw_player_gems
)
from engine.parser import parse_level_file
from engine.entities import Player, Block, Enemy, Item, Npc, Camera, IntStat, Cursor
import tkinter as tk
from tkinter import filedialog
import random
import datetime

# Ініціалізація Pygame
pygame.init()

# Ініціалізація Pygame Mixer для музики
pygame.mixer.init()

# Отримання розмірів робочої області екрана
display_info = pygame.display.Info()
SCREEN_WIDTH, SCREEN_HEIGHT = display_info.current_w, display_info.current_h

# Константи екрану
TILE_SIZE = 100
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Slime Quest: Dungeon")
clock = pygame.time.Clock()

# Загружаем курсор
cursor_img = load_cursor()
cursor = Cursor(cursor_img)

# Прячем системный курсор
pygame.mouse.set_visible(False)

# Шляхи до ресурсів
BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
INTERFACE_DIR = ASSETS_DIR / "img" / "interface"
GRASS_DIR = ASSETS_DIR / "img" / "start_loc" / "grass"
LEVELS_DIR = BASE_DIR / "levels"

# --- Глобальні змінні для масштабованих зображень ---
ROTATING_IMAGE_SIZE = (SCREEN_HEIGHT, SCREEN_HEIGHT)  # квадрат, кожна сторона = висота екрана

# Завантаження шрифту
try:
    font = pygame.font.Font("assets/fonts/Hitch-hike.otf", int(SCREEN_HEIGHT * 0.1))
    title_font = pygame.font.Font("assets/fonts/Hitch-hike.otf", int(SCREEN_HEIGHT * 0.145)) 
    menu_font = pygame.font.Font("assets/fonts/Hitch-hike.otf", int(SCREEN_HEIGHT * 0.047))
    settings_font = pygame.font.Font("assets/fonts/Hitch-hike.otf", int(SCREEN_HEIGHT * 0.075))
except FileNotFoundError as e:
    print(f"Помилка завантаження шрифту: {e}")
    sys.exit()
    
# Завантаження зображення стрілки
try:
    arrow_image = pygame.image.load(str(INTERFACE_DIR / "arrow.png"))
except pygame.error as e:
    print(f"Помилка завантаження зображення стрілки: {e}")
    sys.exit()

# --- Функція для оновлення масштабованих зображень при зміні розміру ---
def update_scaled_images():
    global mainmenu_bg, rotating_image, rotating_image_rect
    global pause_menu_image, pause_menu_buttons, settings_menu_image, settings_menu_buttons, arrow_image

    # Оновлення фонового зображення
    try:
        mainmenu_bg = pygame.image.load(str(INTERFACE_DIR / "mainmenu.png")).convert_alpha()
        mainmenu_bg = pygame.transform.smoothscale(mainmenu_bg, (screen.get_width(), screen.get_height()))
    except pygame.error as e:
        print(f"Помилка завантаження фонового зображення: {e}")
        sys.exit()

    # Оновлення зображення частинок
    try:
        side = screen.get_height()
        rotating_image_raw = pygame.image.load(str(INTERFACE_DIR / "mainmaenu_particles.png")).convert_alpha()
        rotating_image = pygame.transform.smoothscale(rotating_image_raw, (side, side))
        rotating_image_rect = rotating_image.get_rect(center=(screen.get_width() * 0.63, screen.get_height() // 2))
    except pygame.error as e:
        print(f"Помилка завантаження зображення для обертання: {e}")
        sys.exit()

    # Оновлення зображення паузи
    try:
        pause_menu_image = pygame.image.load(str(INTERFACE_DIR / "menu.png")).convert_alpha()
        pause_menu_image = pygame.transform.smoothscale(pause_menu_image, (int(SCREEN_WIDTH * 0.25), int(SCREEN_HEIGHT * 0.65)))
    except pygame.error as e:
        print(f"Помилка завантаження зображення паузи: {e}")
        sys.exit()

    # Оновлення зображення кнопок паузи
    try:
        pause_menu_buttons = pygame.image.load(str(INTERFACE_DIR / "button.png")).convert_alpha()
        pause_menu_buttons = pygame.transform.smoothscale(pause_menu_buttons, (int(SCREEN_WIDTH * 0.17), int(SCREEN_HEIGHT * 0.08)))
    except pygame.error as e:
        print(f"Помилка завантаження зображення кнопок: {e}")
        sys.exit()

    # Оновлення зображення меню налаштувань
    try:
        settings_menu_image = pygame.image.load(str(INTERFACE_DIR / "settings_menu.png")).convert_alpha()
        settings_menu_image = pygame.transform.smoothscale(settings_menu_image, (int(SCREEN_WIDTH * 0.775), int(SCREEN_HEIGHT * 0.73)))
    except pygame.error as e:
        print(f"Помилка завантаження зображення меню налаштувань: {e}")
        sys.exit()

    try:
        settings_menu_buttons = pygame.image.load(str(INTERFACE_DIR / "button.png")).convert_alpha()
        settings_menu_buttons = pygame.transform.smoothscale(settings_menu_buttons, (int(SCREEN_WIDTH * 0.18), int(SCREEN_HEIGHT * 0.08)))
    except pygame.error as e:
        print(f"Помилка завантаження зображення кнопок: {e}")
        sys.exit()

    # Оновлення зображення стрілки
    try:
        arrow_image = pygame.image.load(str(INTERFACE_DIR / "arrow.png")).convert_alpha()
        arrow_image = pygame.transform.smoothscale(arrow_image, (int(SCREEN_WIDTH * 0.05), int(SCREEN_HEIGHT * 0.05)))
    except pygame.error as e:
        print(f"Помилка завантаження зображення стрілки: {e}")
        sys.exit()

# --- Завантаження текстур
textures = load_textures()
textures.update(load_grass_textures(GRASS_DIR))

# Завантаження рівня
level_path = LEVELS_DIR / "level0.lvl"
level_data = None  # Рівень буде завантажено після натискання "Нова гра"

# Текстові елементи
menu_items = ["Нова гра", "Збереження", "Налаштування", "Вихід"]
MENU_X = int(SCREEN_WIDTH * 0.07)
menu_positions = [(MENU_X, int(SCREEN_HEIGHT * 0.4)), (MENU_X, int(SCREEN_HEIGHT * 0.52)), (MENU_X, int(SCREEN_HEIGHT * 0.64)), (MENU_X, int(SCREEN_HEIGHT * 0.76))]  # Вирівнювання по лівому краю

# Завантаження зображення паузи
try:
    pause_menu_image = pygame.image.load(str(INTERFACE_DIR / "menu.png"))
    pause_menu_buttons = pygame.image.load(str(INTERFACE_DIR / "button.png"))
except pygame.error as e:
    print(f"Помилка завантаження зображення паузи: {e}")
    sys.exit()

pause_menu_rect = pause_menu_image.get_rect(topleft=(SCREEN_WIDTH * 0.37, SCREEN_HEIGHT * 0.18))  # Центрування зображення

# Розташування кнопок на зображенні паузи
button_positions = {
    "continue": (int(SCREEN_WIDTH * 0.41), int(SCREEN_HEIGHT * 0.4)),
    "saves": (int(SCREEN_WIDTH * 0.41), int(SCREEN_HEIGHT * 0.5)),
    "settings": (int(SCREEN_WIDTH * 0.41), int(SCREEN_HEIGHT * 0.6)),
    "exit": (int(SCREEN_WIDTH * 0.41), int(SCREEN_HEIGHT * 0.7)),
}

# Розташування кнопок на зображенні налаштувань
settings_button_positions = {
    "back": (int(SCREEN_WIDTH * 0.12), int(SCREEN_HEIGHT * 0.75)),
    "default": (int(SCREEN_WIDTH * 0.31), int(SCREEN_HEIGHT * 0.75)),
    "save_back": (int(SCREEN_WIDTH * 0.51), int(SCREEN_HEIGHT * 0.75)),
    "save": (int(SCREEN_WIDTH * 0.7), int(SCREEN_HEIGHT * 0.75))
}

# Завантаження зображення для меню налаштувань
try:
    settings_menu_image = pygame.image.load(str(INTERFACE_DIR / "settings_menu.png"))
    settings_menu_buttons = pygame.image.load(str(INTERFACE_DIR / "button.png"))
except pygame.error as e:
    print(f"Помилка завантаження зображення меню налаштувань: {e}")
    sys.exit()

settings_menu_rect = settings_menu_image.get_rect(topleft=(SCREEN_WIDTH * 0.112, SCREEN_HEIGHT * 0.12)) 
def render_button_text(screen, menu_font, button_name, button_pos, button_image, button_text_mapping):
    """
    Renders button text and blits it onto the screen.
    :param screen: Pygame screen surface.
    :param menu_font: Font used for rendering button text.
    :param button_name: Name of the button.
    :param button_pos: Position of the button.
    :param button_image: Button image surface.
    :param button_text_mapping: Dictionary mapping button names to their text.
    """
    button_text = menu_font.render(button_text_mapping[button_name], True, (255, 255, 255))  # Білий текст
    button_text_rect = button_text.get_rect(center=(button_pos[0] + button_image.get_width() // 2,
                                                    button_pos[1] + button_image.get_height() // 2))
    screen.blit(button_text, button_text_rect)

def render_pause_menu(screen, pause_menu_image, pause_menu_buttons, button_positions, title_font, menu_font):
    """
    Малює вікно паузи та кнопки на екрані.
    """
    # Відображення зображення паузи поверх гри
    screen.blit(pause_menu_image, pause_menu_rect)

    # Додавання тексту "Пауза" зверху
    pause_text = title_font.render("Пауза", True, (255, 255, 255))
    pause_text_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, int(SCREEN_HEIGHT * 0.29)))
    screen.blit(pause_text, pause_text_rect)

    # Відображення кнопок паузи
    for button_name, button_pos in button_positions.items():
        screen.blit(pause_menu_buttons, button_pos)
        render_button_text(screen, menu_font, button_name, button_pos, pause_menu_buttons, {
            "continue": "Продовжити",
            "saves": "Збереження",
            "settings": "Налаштування",
            "exit": "Вихід"
        })

# Змінна для поточної гучності (0.0 ... 1.0)
current_volume = 1
pygame.mixer.music.set_volume(current_volume)

def render_volume_slider(screen, current_volume, settings_font):
    """
    Малює повзунок гучності поверх меню налаштувань в одному рядку з написом.
    """
    slider_x = int(SCREEN_WIDTH * 0.26)
    slider_y = int(SCREEN_HEIGHT * 0.36)
    slider_width = int(SCREEN_WIDTH * 0.22)
    slider_height = 10

    # Малюємо лінію повзунка
    pygame.draw.rect(screen, (180, 180, 180), (slider_x, slider_y, slider_width, slider_height))
    # Положення "ручки" повзунка залежить від поточної гучності
    handle_x = slider_x + int(current_volume * slider_width)
    handle_y = slider_y + slider_height // 2
    pygame.draw.circle(screen, (255, 255, 255), (handle_x, handle_y), 15)

    # Текст "Гучність: XX%" після повзунка
    text = settings_font.render(f"{int(current_volume * 100)}%", True, (255, 255, 255))
    text_rect = text.get_rect()
    text_rect.centery = slider_y + slider_height // 2
    text_x = int(SCREEN_WIDTH * 0.5)
    screen.blit(text, (text_x, text_rect.top))

    # Підпис "Гучність:" перед повзунком
    label = settings_font.render("Гучність:", True, (255, 255, 255))
    label_rect = label.get_rect()
    label_rect.centery = slider_y + slider_height // 2
    label_x = int(SCREEN_WIDTH * 0.13)
    screen.blit(label, (label_x, label_rect.top))

def render_settings_menu(screen, settings_menu_image, settings_menu_buttons, settings_button_positions, title_font, settings_font, menu_font):
    global current_volume

    # Відображення зображення налаштувань поверх гри
    screen.blit(settings_menu_image, settings_menu_rect)

    # Додавання тексту "Налаштування" зверху
    settings_text = title_font.render("Налаштування", True, (255, 255, 255))  # Білий текст
    settings_text_rect = settings_text.get_rect(center=(SCREEN_WIDTH // 2, int(SCREEN_HEIGHT * 0.23)))
    screen.blit(settings_text, settings_text_rect)

    # Відображення кнопок налаштувань
    for button_name, button_pos in settings_button_positions.items():
        screen.blit(settings_menu_buttons, button_pos)
        render_button_text(screen, menu_font, button_name, button_pos, settings_menu_buttons, {
            "back": "Закрити",
            "default": "Скинути налаштування",
            "save_back": "Зберегти та закрити",
            "save": "Зберегти"
        })
    render_volume_slider(screen, current_volume, settings_font)

    # --- Чекбокси ---
    # Координати чекбоксів
    checkbox_x = int(SCREEN_WIDTH * 0.42)
    checkbox_y_start = int(SCREEN_HEIGHT * 0.45)
    checkbox_spacing = int(SCREEN_HEIGHT * 0.09)

    # Текстові підписи для чекбоксів
    hints_label = settings_font.render("Підказки", True, (255, 255, 255))
    windowed_label = settings_font.render("Повноекранний режим", True, (255, 255, 255))
    level_select_label = settings_font.render("Вибір рівнів", True, (255, 255, 255))

    # Відображення підписів
    screen.blit(hints_label, (int(SCREEN_WIDTH * 0.13), int(SCREEN_HEIGHT * 0.41)))
    screen.blit(windowed_label, (int(SCREEN_WIDTH * 0.13), int(SCREEN_HEIGHT * 0.5)))
    screen.blit(level_select_label, (int(SCREEN_WIDTH * 0.13), int(SCREEN_HEIGHT * 0.59)))

    # Чекбокс "Підказки"
    hints_rect = pygame.Rect(checkbox_x, checkbox_y_start, 30, 30)
    pygame.draw.rect(screen, (255, 255, 255), hints_rect, 2)
    if settings.get("hints", True):
        pygame.draw.line(screen, (255, 255, 255), (hints_rect.left+5, hints_rect.top+15), (hints_rect.left+15, hints_rect.bottom-5), 3)
        pygame.draw.line(screen, (255, 255, 255), (hints_rect.left+15, hints_rect.bottom-5), (hints_rect.right-5, hints_rect.top+5), 3)

    # Чекбокс "Віконний режим"
    windowed_rect = pygame.Rect(checkbox_x, checkbox_y_start + checkbox_spacing, 30, 30)
    pygame.draw.rect(screen, (255, 255, 255), windowed_rect, 2)
    if settings.get("fullscreen", False):
        pygame.draw.line(screen, (255, 255, 255), (windowed_rect.left+5, windowed_rect.top+15), (windowed_rect.left+15, windowed_rect.bottom-5), 3)
        pygame.draw.line(screen, (255, 255, 255), (windowed_rect.left+15, windowed_rect.bottom-5), (windowed_rect.right-5, windowed_rect.top+5), 3)

    # Чекбокс "Вибір рівнів"
    level_select_rect = pygame.Rect(checkbox_x, checkbox_y_start + 2 * checkbox_spacing, 30, 30)
    pygame.draw.rect(screen, (255, 255, 255), level_select_rect, 2)
    if settings.get("level_select", False):
        pygame.draw.line(screen, (255, 255, 255), (level_select_rect.left+5, level_select_rect.top+15), (level_select_rect.left+15, level_select_rect.bottom-5), 3)
        pygame.draw.line(screen, (255, 255, 255), (level_select_rect.left+15, level_select_rect.bottom-5), (level_select_rect.right-5, level_select_rect.top+5), 3)
        
# Функція для збереження налаштувань у файл
def save_settings_to_file(settings_dict):
    """
    Зберігає налаштування у файл settings.json у поточній директорії.
    """
    path = os.path.join(os.getcwd(), "settings.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(settings_dict, f, indent=4, ensure_ascii=False)
    print("Налаштування збережено у settings.json")

# Функція для завантаження налаштувань з файлу
def load_settings_from_file():
    """
    Завантажує налаштування з файлу settings.json, якщо він існує.
    """
    path = os.path.join(os.getcwd(), "settings.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            try:
                loaded = json.load(f)
                print("Налаштування завантажено з settings.json")
                return loaded
            except Exception as e:
                print(f"Помилка читання settings.json: {e}")
    return None

# Стандартні налаштування як окремий словник
DEFAULT_SETTINGS = {
    "volume": 100,
    "fullscreen": False,
    "hints": True,
    "level_select": False
}

# Налаштування користувача
settings = dict(DEFAULT_SETTINGS)

# Завантаження налаштувань з settings.json, якщо файл існує
loaded_settings = load_settings_from_file()
if loaded_settings:
    settings.update(loaded_settings)

# Застосування налаштувань
current_volume = settings.get("volume", 100) / 100
pygame.mixer.music.set_volume(current_volume)
# Якщо потрібно застосувати fullscreen:
if settings.get("fullscreen"):
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
else:
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
    
def play_music(music_file, loop=False):
    """
    Відтворює музичний файл.
    :param music_file: Шлях до музичного файлу.
    :param loop: True для зациклення, False для відтворення один раз.
    """
    try:
        pygame.mixer.music.load(music_file)
        if loop:
            pygame.mixer.music.play(-1)  # -1 для зациклення
        else:
            pygame.mixer.music.play(0)  # 0 для відтворення один раз
    except pygame.error as e:
        print(f"Помилка відтворення музики: {e}")    
    
def toggle_pause(is_paused):
    """
    Перемикає стан паузи.
    """
    return not is_paused
    
def stop_music():
    """
    Зупиняє відтворення музики.
    """
    pygame.mixer.music.stop() 

# Функція для встановлення стандартних налаштувань
def set_default_settings():
    """
    Встановлює стандартні налаштування:
    - Гучність 100
    - Підказки увімкнено
    - Віконний режим та Вибір рівнів вимкнено
    """
    settings.clear()
    settings.update(DEFAULT_SETTINGS)
    globals()["current_volume"] = settings["volume"] / 100
    pygame.mixer.music.set_volume(globals()["current_volume"])
    # Примусове перемальовування меню налаштувань
    render_settings_menu(screen, settings_menu_image, settings_menu_buttons, settings_button_positions, title_font, settings_font, menu_font)
    cursor.draw(screen)
    pygame.display.flip()
    
def create_player(player_start, textures):
    """
    Фабрична функція для створення Player з урахуванням TILE_SIZE та словника текстур.
    :param player_start: (x, y) координати гравця у клітинках
    :param textures: словник текстур
    :return: Player instance
    """
    # Передаємо gem_textures (всі gemXX з textures) у Player
    gem_textures = {k: v for k, v in textures.items() if k.startswith("gem")}
    return Player(
        (player_start[0] * TILE_SIZE, player_start[1] * TILE_SIZE),
        {
            "player_left": textures["player_left"],
            "player_right": textures["player_right"],
            "player_back_left": textures.get("player_back_left", textures["player_left"]),
            "player_back_right": textures.get("player_back_right", textures["player_right"])
        },
        gem_textures=gem_textures  # <-- Додаємо це!
    )

def select_level_file():
    """
    Відкриває діалог вибору файлу рівня та повертає шлях до вибраного .lvl-файлу або None.
    """
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        initialdir=str(LEVELS_DIR),
        title="Оберіть файл рівня",
        filetypes=[("Level files", "*.lvl")]
    )
    root.destroy()
    if file_path:
        return file_path
    return None

# --- Ініціалізація фонового зображення ---
try:
    mainmenu_bg = pygame.image.load(str(INTERFACE_DIR / "mainmenu.png")).convert_alpha()
    mainmenu_bg = pygame.transform.smoothscale(mainmenu_bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
except pygame.error as e:
    print(f"Помилка завантаження фонового зображення: {e}")
    sys.exit()

SAVE_SLOTS = 3  # Number of save slots
SAVES_DIR = BASE_DIR / "Saves"  # Use 'Saves' with capital S
os.makedirs(SAVES_DIR, exist_ok=True)

def get_save_path(slot):
    return SAVES_DIR / f"save{slot}.json"

def serialize_game_state():
    """Serialize current game state for saving."""
    if player is None or not hasattr(player, "rect"):
        raise RuntimeError("Не можна зберегти гру: гра не запущена або гравець не ініціалізований!")
    # Завжди зберігайте current level_path як відносний до LEVELS_DIR, якщо це можливо
    try:
        rel_path = level_path.relative_to(LEVELS_DIR)
        level_path_str = str(rel_path)
        is_relative = True
    except ValueError:
        level_path_str = str(level_path.resolve())
        is_relative = False
    # Зберігайте лише мінімальний стан, не зберігайте блоки/предмети/ворогів/статуї/нпс
    return {
        "level_path": level_path_str,
        "level_path_relative": is_relative,
        "player": {
            "x": player.rect.x,
            "y": player.rect.y,
            "health": getattr(player, "health", 10),
            "protection": getattr(player, "protection", 0),
            "atk": getattr(player, "atk", 1),
            "speed": getattr(player, "speed", 1),
            "luck": getattr(player, "luck", 0),
        },
        "stats": {
            "showing_stats": showing_stats
        },
        # --- Нове: розширені ігрові дані ---
        "completed_levels": list(completed_levels),
        "defeated_enemies": list(defeated_enemies),
        "opened_chests": list(opened_chests),
        "collected_gems": list(collected_gems),
        "upgraded_statues": list(upgraded_statues),
    }

def deserialize_game_state(state):
    """Restore game state from loaded data."""
    global level_path, player, camera, background_grid, showing_stats, blocks, enemies, items, statues, npcs
    global completed_levels, defeated_enemies, opened_chests, collected_gems, upgraded_statues
    # Відновлення level_path з використанням відносної інформації, якщо це можливо
    if state.get("level_path_relative"):
        level_path = (LEVELS_DIR / state["level_path"]).resolve()
    else:
        level_path = Path(state["level_path"])
    # Завжди повторно аналізуйте файл рівня, щоб отримати нову карту та об'єкти
    level_data = parse_level_file(level_path)
    player_data = state["player"]
    player = create_player((player_data["x"] // TILE_SIZE, player_data["y"] // TILE_SIZE), textures)
    player.rect.x = player_data["x"]
    player.rect.y = player_data["y"]
    player.health = player_data.get("health", 10)
    player.protection = player_data.get("protection", 0)
    player.atk = player_data.get("atk", 1)
    player.speed = player_data.get("speed", 1)
    player.luck = player_data.get("luck", 0)
    showing_stats = state.get("stats", {}).get("showing_stats", False)
    camera = Camera(level_data['width'] * TILE_SIZE, level_data['height'] * TILE_SIZE)
    background_grid = generate_background_grid(textures, level_data, level_path.name)
    # Відновлення всіх об'єктів з level_data (не з збереження)
    blocks_set = {(block['x'], block['y']) for block in level_data['blocks']}
    blocks = [
        Block(
            block['x'] * TILE_SIZE,
            block['y'] * TILE_SIZE,
            block['is_solid'],
            determine_tree_texture(block['x'], block['y'], blocks_set, textures) if level_path.name == "level0.lvl" else determine_block_texture(block['x'], block['y'], blocks_set)
        )
        for block in level_data['blocks']
    ]
    enemy_textures = {
        "zombie_left": textures["zombie_left"],
        "zombie_right": textures["zombie_right"],
        "zombie_back_left": textures["zombie_back_left"],
        "zombie_back_right": textures["zombie_back_right"],
        "skeleton_left": textures["skeleton_left"],
        "skeleton_right": textures["skeleton_right"],
        "skeleton_back_left": textures["skeleton_back_left"],
        "skeleton_back_right": textures["skeleton_back_right"],
        "boss_left": textures["boss_left"],
        "boss_right": textures["boss_right"],
        "boss_back_left": textures["boss_back_left"],
        "boss_back_right": textures["boss_back_right"],
    }
    enemies = [
        Enemy(
            enemy['x'], enemy['y'], enemy_type_mapping.get(enemy['type'], 'zombie_left'), enemy_textures,
            health={
                'zombie': 50,
                'skeleton': 100,
                'boss': 10
            }.get(enemy_type_mapping.get(enemy['type'], 'zombie_left'), 1)
        ) for enemy in level_data['enemies']
    ]
    # --- Увеличиваем хитбокс босса до 300x300 ---
    for enemy in enemies:
        if hasattr(enemy, "type") and "boss" in enemy.type:
            enemy.rect.width = 300
            enemy.rect.height = 300

    items = [
        Item(item['x'] * TILE_SIZE, item['y'] * TILE_SIZE, item.get('is_solid', True), textures['item_frames'])
        for item in level_data['items']
    ]
    statue_type_mapping_local = {f"statue{key}": value for key, value in statue_type_mapping.items()}
    statues = [
        IntStat(
            statue['x'] * TILE_SIZE,
            statue['y'] * TILE_SIZE,
            statue.get('is_solid', True),
            f"statue{statue['type']}",
            textures
        )
        for statue in level_data['statues']
    ]
    npcs = [
        Npc(
            npc['x'] * TILE_SIZE,
            npc['y'] * TILE_SIZE,
            npc_type_mapping.get(npc['type'], 'teleport'),
            {
                'enter': textures['enter'],
                'teleport': textures['teleport']
            }
        )
        for npc in level_data['npc']
    ]
    # Тепер карта та всі об'єкти завжди узгоджені з файлом рівня

    # --- Відновлення розширених ігрових даних після завантаження ---
    completed_levels = set(state.get("completed_levels", []))
    defeated_enemies = set(tuple(e) for e in state.get("defeated_enemies", []))
    opened_chests = set(tuple(c) for c in state.get("opened_chests", []))
    collected_gems = set(tuple(g) for g in state.get("collected_gems", []))
    upgraded_statues = set(tuple(s) for s in state.get("upgraded_statues", []))

# --- Нові глобальні змінні для розширеного збереження ---
completed_levels = set()
defeated_enemies = set()
opened_chests = set()
collected_gems = set()
upgraded_statues = set()

def save_game(slot=1):
    """Save current game state to a slot."""
    try:
        save_data = serialize_game_state()
    except Exception as e:
        print(f"Помилка збереження: {e}")
        return
    save_path = get_save_path(slot)
    save_data["datetime"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Write to a temp file first, then atomically replace
    tmp_path = str(save_path) + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(save_data, f, indent=4, ensure_ascii=False)
    os.replace(tmp_path, save_path)
    print(f"Гра збережена у слоті {slot} ({save_path})")

def clear_saves():
    """Clear all save files in the Saves directory."""
    for slot in range(1, SAVE_SLOTS + 1):
        save_path = get_save_path(slot)
        if save_path.exists():
            try:
                save_path.unlink()
            except Exception as e:
                print(f"Не вдалося видалити {save_path}: {e}")

def get_save_datetime(slot):
    """Return the datetime string of the save slot, or None if not found."""
    save_path = get_save_path(slot)
    if not os.path.exists(save_path):
        return None
    try:
        with open(save_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("datetime")
    except Exception:
        return None

def load_game(slot=1):
    """Load game state from a save slot and restore it."""
    save_path = get_save_path(slot)
    if not os.path.exists(save_path):
        print(f"Save slot {slot} is empty.")
        return False
    try:
        with open(save_path, "r", encoding="utf-8") as f:
            state = json.load(f)
            deserialize_game_state(state)
            print(f"Гра завантажена з слоту {slot} ({save_path})")
            return True
    except Exception as e:
        print(f"Помилка завантаження гри з слоту {slot}: {e}")
        return False

def render_saves_menu(screen, menu_font, setings_menu_image, pause_menu_buttons, slot_count=SAVE_SLOTS, selected_slot=None):
    """
    Render a wide saves menu with slot selection and Save/Load/Back buttons.
    Shows save date/time for each slot.
    """

    # Використовуємо settings_menu_image як фон
    screen.blit(settings_menu_image, settings_menu_rect)
    
    wide_width = int(SCREEN_WIDTH * 0.7)
    wide_height = int(SCREEN_HEIGHT * 0.7)
    wide_x = (SCREEN_WIDTH - wide_width) // 2
    wide_y = (SCREEN_HEIGHT - wide_height) // 2
    
    saves_title = title_font.render("Збереження", True, (255, 255, 255))
    saves_title_rect = saves_title.get_rect(center=(SCREEN_WIDTH // 2, wide_y + int(wide_height * 0.09)))
    screen.blit(saves_title, saves_title_rect)
    slot_rects = []
    btn_w = pause_menu_buttons.get_width()
    btn_h = pause_menu_buttons.get_height()
    slot_area_x = wide_x + int(wide_width * 0.08)
    slot_area_y = wide_y + int(wide_height * 0.18)
    slot_area_w = wide_width - int(wide_width * 0.16)
    slot_spacing = int((wide_height * 0.5) // slot_count)
    slot_has_save = {}
    for i in range(1, slot_count + 1):
        y = slot_area_y + (i - 1) * slot_spacing
        # Slot background
        slot_bg_rect = pygame.Rect(slot_area_x, y, slot_area_w, btn_h + 12)
        pygame.draw.rect(screen, (60, 60, 90), slot_bg_rect, border_radius=12)
        # Slot label
        slot_label = menu_font.render(f"Слот {i}", True, (255, 255, 255))
        slot_label_rect = slot_label.get_rect(midleft=(slot_area_x + 20, y + btn_h // 2 + 6))
        screen.blit(slot_label, slot_label_rect)
        # Date/time
        dt = get_save_datetime(i)
        has_save = dt is not None
        slot_has_save[i] = has_save
        dt_text = menu_font.render(dt if dt else "Порожньо", True, (180, 220, 180) if dt else (120, 120, 120))
        dt_rect = dt_text.get_rect(midleft=(slot_area_x + 170, y + btn_h // 2 + 6))
        screen.blit(dt_text, dt_rect)
        # Select button
        slot_btn_pos = (slot_area_x + slot_area_w - btn_w - 20, y + 6)
        screen.blit(pause_menu_buttons, slot_btn_pos)
        slot_btn_text = menu_font.render("Обрати", True, (255, 255, 255))
        slot_btn_text_rect = slot_btn_text.get_rect(center=(slot_btn_pos[0] + btn_w // 2, slot_btn_pos[1] + btn_h // 2))
        screen.blit(slot_btn_text, slot_btn_text_rect)
        slot_rects.append((i, pygame.Rect(slot_btn_pos, (btn_w, btn_h))))
    # Bottom buttons: only if slot selected
    save_rect = load_rect = back_rect = None
    bottom_y = wide_y + wide_height - btn_h - 24
    # --- Only show "Save" button if in-game (showing_level == True) ---
    if selected_slot is not None:
        btn_x = wide_x + int(wide_width * 0.18)
        if globals().get("showing_level", False) and globals().get("player", None) is not None:
            # Save
            save_btn_pos = (btn_x, bottom_y)
            screen.blit(pause_menu_buttons, save_btn_pos)
            save_text = menu_font.render("Зберегти", True, (255, 255, 255))
            save_text_rect = save_text.get_rect(center=(save_btn_pos[0] + btn_w // 2, save_btn_pos[1] + btn_h // 2))
            screen.blit(save_text, save_text_rect)
            save_rect = pygame.Rect(save_btn_pos, (btn_w, btn_h))
            btn_x += int(wide_width * 0.24)
    # Load (only if slot has save)
    if selected_slot is not None and slot_has_save.get(selected_slot, False):
        load_btn_pos = (btn_x, bottom_y)
        screen.blit(pause_menu_buttons, load_btn_pos)
        load_text = menu_font.render("Завантажити", True, (255, 255, 255))
        load_text_rect = load_text.get_rect(center=(load_btn_pos[0] + btn_w // 2, load_btn_pos[1] + btn_h // 2))
        screen.blit(load_text, load_text_rect)
        load_rect = pygame.Rect(load_btn_pos, (btn_w, btn_h))
        btn_x += int(wide_width * 0.25)
    # Back
    back_btn_pos = (wide_x + int(wide_width * 0.66), bottom_y)
    screen.blit(pause_menu_buttons, back_btn_pos)
    back_text = menu_font.render("Назад", True, (255, 255, 255))
    back_text_rect = back_text.get_rect(center=(back_btn_pos[0] + btn_w // 2, back_btn_pos[1] + btn_h // 2))
    screen.blit(back_text, back_text_rect)
    back_rect = pygame.Rect(back_btn_pos, (btn_w, btn_h))
    return slot_rects, save_rect, load_rect, back_rect

# --- Додаємо змінну для екрану "Ви загинули" ---
showing_game_over = False

def render_game_over(screen, title_font, menu_font):
    """Render the game over screen with a restart button."""
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))
    # Text
    text = title_font.render("Ви загинули", True, (255, 80, 80))
    text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80))
    screen.blit(text, text_rect)
    # Button
    # --- Заміна малювання прямокутника на pause_menu_buttons ---
    btn_w, btn_h = pause_menu_buttons.get_width(), pause_menu_buttons.get_height()
    btn_x = (SCREEN_WIDTH - btn_w) // 2
    btn_y = SCREEN_HEIGHT // 2 + 10
    button_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
    screen.blit(pause_menu_buttons, (btn_x, btn_y))
    btn_text = menu_font.render("Почати спочатку", True, (255, 255, 255))
    btn_text_rect = btn_text.get_rect(center=button_rect.center)
    screen.blit(btn_text, btn_text_rect)
    return button_rect

# --- Додаткові змінні для рівня ---
player = None
blocks = []
enemies = []
items = []
statues = []
npcs = []
camera = None
background_grid = None
pressed_keys = set()
level_data = None 
player_gems_state = {}
statues_state = {}
player_potions = 0  # <--- Количество зелий лечения у игрока

# --- Загрузка иконки зелья лечения ---
try:
    potion_icon = textures["potion"]
    potion_icon = pygame.transform.smoothscale(potion_icon, (50, 50))
except pygame.error as e:
    print(f"Не вдалося завантажити зображення зілля: {e}")
    potion_icon = None

# --- Показывать иконку и количество зелий, если хотя бы одно зелье есть ---
def draw_potion_icon_and_count(screen, icon, count, font, x, y):
    if icon is not None and count > 0:
        screen.blit(icon, (x, y))
        pot_text = font.render(f"x{count}", True, (255, 255, 255))
        pot_text_rect = pot_text.get_rect(midleft=(x + icon.get_width() + 8, y + icon.get_height() // 2))
        screen.blit(pot_text, pot_text_rect)

def save_player_gems_state(player):
    """Зберігає стан гемів гравця у глобальний словник."""
    global player_gems_state
    gem_names = [f"gem{x}{y}" for x in range(1, 6) for y in range(1, 6)]
    player_gems_state = {gem: getattr(player, gem, False) for gem in gem_names}

def restore_player_gems_state(player):
    """Відновлює стан гемів гравця з глобального словника."""
    global player_gems_state
    for gem, value in player_gems_state.items():
        if hasattr(player, gem):
            setattr(player, gem, value)

def save_statues_state(statues):
    """Зберігає стан статуй і характеристики гравця у глобальний словник (ключ: (x, y), значення: type), а також характеристики."""
    global statues_state, player_stats_state
    # Не очищаємо statues_state, якщо statues порожній або None
    if not statues:
        print("[DEBUG] save_statues_state: statues is None or empty, skipping save")
        return
    statues_state = {}
    for statue in statues:
        cell_x = statue.rect.x // TILE_SIZE
        cell_y = statue.rect.y // TILE_SIZE
        statues_state[(cell_x, cell_y)] = getattr(statue, "type", "")
    # Зберігаємо характеристики гравця
    player_stats_state = {
        "health": getattr(player, "health", None),
        "protection": getattr(player, "protection", None),
        "atk": getattr(player, "atk", None),
        "speed": getattr(player, "speed", None),
        "luck": getattr(player, "luck", None),
    }
    print(f"[DEBUG] save_statues_state: {statues_state}")
    print(f"[DEBUG] save_statues_state (player_stats): {player_stats_state}")

def restore_statues_state(statues):
    """Відновлює стан статуй з глобального словника та характеристики гравця."""
    global statues_state, player_stats_state
    print(f"[DEBUG] restore_statues_state: {statues_state}")
    for statue in statues:
        cell_x = statue.rect.x // TILE_SIZE
        cell_y = statue.rect.y // TILE_SIZE
        key = (cell_x, cell_y)
        if key in statues_state:
            statue.type = statues_state[key]
            if hasattr(statue, "texture") and statue.type in textures:
                statue.texture = textures[statue.type]
    # Відновлюємо характеристики гравця, якщо вони збережені
    if "player_stats_state" in globals() and player_stats_state:
        for attr in ["health", "protection", "atk", "speed", "luck"]:
            if player_stats_state.get(attr) is not None:
                setattr(player, attr, player_stats_state[attr])
        print(f"[DEBUG] restore_statues_state (player_stats): {player_stats_state}")

def debug_state():
    print(f"showing_menu={showing_menu}, showing_level={showing_level}, showing_settings={showing_settings}, is_paused={is_paused}, showing_saves={showing_saves}")

running = True
showing_menu = True
showing_level = False
showing_settings = False
showing_saves = False
is_paused = False
showing_stats = False
menu1_played = False
current_music = None
selected_save_slot = None
level_transitioning = False

# --- Додаємо змінну для відстеження переходу на новий рівень після босса ---
boss_defeated_and_portal_used = False

# --- Track current level number for cycling ---
current_level_number = 1  # Start from level1.lvl after cave

# --- Damage popups ---
damage_popups = []

def add_damage_popup(x, y, value, color=(255, 0, 0)):
    """Add a damage popup at (x, y) with value and color."""
    damage_popups.append({
        "x": x,
        "y": y,
        "value": value,
        "color": color,
        "timer": 40,  # frames to show
        "alpha": 255
    })

def update_and_draw_damage_popups(screen, camera):
    """Update and draw all damage popups."""
    global damage_popups
    new_popups = []
    for popup in damage_popups:
        # Move up
        popup["y"] -= 1
        popup["timer"] -= 1
        # Fade out
        if popup["timer"] < 15:
            popup["alpha"] = int(255 * popup["timer"] / 15)
        # Draw
        font_popup = pygame.font.Font("assets/fonts/Hitch-hike.otf", 32)
        text = font_popup.render(str(popup["value"]), True, popup["color"])
        text.set_alpha(popup["alpha"])
        # --- FIX: Use camera.apply_rect on a Rect, not camera.apply on a tuple ---
        popup_rect = pygame.Rect(int(popup["x"]), int(popup["y"]), 1, 1)
        pos = camera.apply_rect(popup_rect).topleft
        screen.blit(text, pos)
        if popup["timer"] > 0:
            new_popups.append(popup)
    damage_popups = new_popups

while running:
    clock.tick(60)
    global rotating_image, rotating_image_rect, rotation_angle

    if showing_menu:
        # Відтворення menu1.wav, якщо ще не відтворювалася
        if not menu1_played:
            stop_music()
            try:
                music_file1 = str(ASSETS_DIR / "audio" / "menu1.wav")
                play_music(music_file1, loop=False)
                current_music = "menu1"
                menu1_played = True  # Встановлюємо прапорець, щоб більше не відтворювати
            except FileNotFoundError:
                print("Файл menu1.wav не знайдено!")

        # Після закінчення menu1.wav починаємо відтворення menu2.wav
        if not pygame.mixer.music.get_busy() and current_music == "menu1":
            stop_music()
            try:
                music_file2 = str(ASSETS_DIR / "audio" / "menu2.wav")
                play_music(music_file2, loop=True)
                current_music = "menu2"
            except FileNotFoundError:
                print("Файл menu2.wav не знайдено!")

        # Відображення статичного фону замість анімації
        screen.blit(mainmenu_bg, (0, 0))

        # Обертання зображення
        if 'rotating_image' not in globals() or 'rotating_image_rect' not in globals():
            update_scaled_images()
        try:
            rotation_angle = (rotation_angle + 1) % 360  # Збільшуємо кут обертання
        except NameError:
            rotation_angle = 0
        rotated_image = pygame.transform.rotate(rotating_image, rotation_angle)
        rotated_rect = rotated_image.get_rect(center=rotating_image_rect.center)
        screen.blit(rotated_image, rotated_rect.topleft)

        # Відображення назви гри
        title_text = title_font.render("Slime Quest: Dungeon", True, (255, 255, 255))  # Білий колір
        title_rect = title_text.get_rect(topleft=(MENU_X, int(SCREEN_HEIGHT * 0.18)))  # 20% від висоти екрана
        screen.blit(title_text, title_rect)

        # Відображення тексту
        text_rects = []
        for i, text in enumerate(menu_items):
            rendered_text = font.render(text, True, (255, 255, 255))
            text_rect = rendered_text.get_rect(topleft=menu_positions[i])
            text_rects.append((text, text_rect))
            screen.blit(rendered_text, text_rect)

        # Отримання позиції миші
        mouse_pos = pygame.mouse.get_pos()

        # Відображення стрілки при наведенні (лише одне зображення)
        arrow_drawn = False  # Флаг для контролю відображення стрілки
        for i, (_, rect) in enumerate(text_rects):
            if rect.collidepoint(mouse_pos) and not arrow_drawn:  # Якщо курсор наведений на текст
                arrow_pos = (rect.left - 100, rect.centery - arrow_image.get_height() // 2)
                screen.blit(arrow_image, arrow_pos)
                arrow_drawn = True  # Встановлюємо флаг, щоб стрілка відображалася лише один раз

        # --- draw cursor before flip ---
        cursor.draw(screen)
        pygame.display.flip()

        # Обробка подій
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                if showing_menu:
                    for text, rect in text_rects:
                        if rect.collidepoint(mouse_pos):
                            print(f"Клік по тексту: {text}")
                            if text == "Вихід":
                                running = False
                            elif text == "Нова гра":
                                showing_menu = False
                                showing_level = True
                                # Reset all game state for a new game
                                level_path = LEVELS_DIR / "level0.lvl"
                                player = None
                                camera = None
                                background_grid = None
                                blocks = []
                                enemies = []
                                items = []
                                statues = []
                                npcs = []
                                pressed_keys.clear()
                                showing_stats = False
                                is_paused = False
                                showing_settings = False
                                showing_saves = False
                                selected_save_slot = None
                                level_data = None
                                boss_defeated_and_portal_used = False  # <--- Reset flag on new game
                                current_level_number = 1  # Reset level cycle
                                debug_state()
                                break
                            elif text == "Збереження":
                                showing_menu = False
                                showing_saves = True
                                selected_save_slot = None
                                # Сбросить все игровые объекты, чтобы не было конфликтов при загрузке из меню
                                player = None
                                camera = None
                                background_grid = None
                                blocks = []
                                enemies = []
                                items = []
                                statues = []
                                npcs = []
                                pressed_keys.clear()
                                showing_stats = False
                                is_paused = False
                                level_data = None
                                # Важно: сразу делаем continue, чтобы цикл while не дошёл до блока showing_level!
                                continue
                            elif text == "Налаштування":
                                showing_menu = False
                                showing_settings = True
                                debug_state()

                elif showing_settings:
                    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                    screen.blit(overlay, (0, 0))
                    render_settings_menu(screen, settings_menu_image, settings_menu_buttons, settings_button_positions, title_font, settings_font, menu_font)
                    cursor.draw(screen)
                    pygame.display.flip()
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            showing_settings = False
                    continue
                elif event.type == pygame.KEYUP:
                    if event.key in pressed_keys:
                        pressed_keys.discard(event.key)
    elif showing_level:
        # Якщо ми тут, значить showing_level == True
        # Відображення рівня
        if player is None or camera is None or background_grid is None:
            print("Ініціалізація рівня")
            level_data = parse_level_file(level_path)

            if level_data['player_start'] is None:
                print("Помилка: Початкова позиція гравця не визначена у файлі рівня.")
                running = False
                break

            player = create_player(level_data['player_start'], textures)
            # --- Відновлюємо стан гемів після створення гравця ---
            restore_player_gems_state(player)
            
            blocks_set = {(block['x'], block['y']) for block in level_data['blocks']}
            # --- Виправлено: використовуємо всі типи дерев для level0.lvl ---
            def determine_tree_texture_fixed(x, y, blocks_set, textures):
                left = (x - 1, y) in blocks_set
                right = (x + 1, y) in blocks_set
                top = (x, y - 1) in blocks_set
                bottom = (x, y + 1) in blocks_set
                if not left and not right and top and bottom: 
                    return textures["tree"]
                if left and right and not top and bottom:
                    return textures["trees_center_top"]
                if left and right and not top and not bottom:
                    return textures["trees_center"]
                if left and right and top and not bottom:
                    return textures["trees_center_top"]
                if not left and right and top and bottom:
                    return textures["trees_center_top"]
                if left and not right and top and bottom:
                    return textures["trees_center_top"]
                if not left and right and top and not bottom:
                    return textures["trees_center_top"]
                if left and not right and top and not bottom:
                    return textures["trees_center_top"]
                return textures["trees_center"]

            blocks = [
                Block(
                    block['x'] * TILE_SIZE,
                    block['y'] * TILE_SIZE,
                    block['is_solid'],
                    determine_tree_texture_fixed(block['x'], block['y'], blocks_set, textures) if level_path.name == "level0.lvl" else determine_block_texture(block['x'], block['y'], blocks_set)
                )
                for block in level_data['blocks']
            ]

            enemy_textures = {
                "zombie_left": textures["zombie_left"],
                "zombie_right": textures["zombie_right"],
                "zombie_back_left": textures["zombie_back_left"],
                "zombie_back_right": textures["zombie_back_right"],
                "skeleton_left": textures["skeleton_left"],
                "skeleton_right": textures["skeleton_right"],
                "skeleton_back_left": textures["skeleton_back_left"],
                "skeleton_back_right": textures["skeleton_back_right"],
                "boss_left": textures["boss_left"],
                "boss_right": textures["boss_right"],
                "boss_back_left": textures["boss_back_left"],
                "boss_back_right": textures["boss_back_right"],
            }
            enemies = [
                Enemy(
                    enemy['x'], enemy['y'], enemy_type_mapping.get(enemy['type'], 'zombie_left'), enemy_textures,
                    health={
                        'zombie': 50,
                        'skeleton': 100,
                        'boss': 10
                    }.get(enemy_type_mapping.get(enemy['type'], 'zombie_left'), 1)
                ) for enemy in level_data['enemies']
            ]
            # --- Увеличиваем хитбокс босса до 300x300 ---
            for enemy in enemies:
                if hasattr(enemy, "type") and "boss" in enemy.type:
                    enemy.rect.width = 300
                    enemy.rect.height = 300
            
            for enemy in enemies:
                if hasattr(enemy, "type") and "zombie" in enemy.type:
                    enemy.rect.width = 100
                    enemy.rect.height = 200
            
            for enemy in enemies:
                if hasattr(enemy, "type") and "skeleton" in enemy.type:
                    enemy.rect.width = 100
                    enemy.rect.height = 200

            items = [
                Item(item['x'] * TILE_SIZE, item['y'] * TILE_SIZE, item.get('is_solid', True), textures['item_frames'])
                for item in level_data['items']
            ]
            statue_type_mapping = {f"{key}": value for key, value in statue_type_mapping.items()}
            
            statues = [
                IntStat(
                    statue['x'] * TILE_SIZE,
                    statue['y'] * TILE_SIZE,
                    statue.get('is_solid', True),
                    f"statue{statue['type']}0",
                    textures
                )
                for statue in level_data['statues']
            ]
            # --- Відновлюємо стан статуй після створення ---
            restore_statues_state(statues)
            
            npcs = [
                Npc(
                    npc['x'] * TILE_SIZE,
                    npc['y'] * TILE_SIZE,
                    npc_type_mapping.get(npc['type'], 'teleport'),
                    {
                        'enter': textures['enter'],
                        'teleport': textures['teleport']
                    }
                )
                for npc in level_data['npc']
            ]
            
            camera = Camera(level_data['width'] * TILE_SIZE, level_data['height'] * TILE_SIZE)

            # --- Patch: Use cave floor for cave levels ---
            level_name = level_path.name
            if level_name != "level0.lvl":
                # For cave levels, force cave floor
                background_grid = generate_background_grid(textures, level_data, "cave")
            else:
                background_grid = generate_background_grid(textures, level_data, level_name)

            # Функція для визначення текстури блоку залежно від оточення
            def determine_block_texture(x, y, blocks_set):
                """
                Визначає текстуру блоку залежно від його оточення.

                :param x: Координата X блоку
                :param y: Координата Y блоку
                :param blocks_set: Набір координат усіх блоків
                :return: Відповідна текстура блоку
                """
                has_left = (x - 1, y) in blocks_set
                has_right = (x + 1, y) in blocks_set
                has_top = (x, y - 1) in blocks_set
                has_bottom = (x, y + 1) in blocks_set

                # Найбільш специфічні умови
                if has_left and has_right and has_top and has_bottom:
                    return textures['wall']
                if has_left and has_right and has_top:
                    return textures['wall_bottom']
                if has_left and has_right and has_bottom:
                    return textures['wall_top']
                if has_top and has_bottom and has_left:
                    return textures['wall_right']
                if has_top and has_bottom and has_right:
                    return textures['wall_left']

                # Менш специфічні умови
                if has_left and has_right:
                    return textures['wall_top_bottom']
                if has_top and has_bottom:
                    return textures['wall_left_right']
                if has_top and has_left:
                    return textures['wall_right_bottom']
                if has_top and has_right:
                    return textures['wall_left_bottom']
                if has_bottom and has_left:
                    return textures['wall_right_top']
                if has_bottom and has_right:
                    return textures['wall_left_top']

                # Найменш специфічні умови
                if has_top:
                    return textures['wall_left_right_bottom']
                if has_bottom:
                    return textures['wall_left_right_top']
                if has_left:
                    return textures['wall_right_top_bottom']
                if has_right:
                    return textures['wall_left_top_bottom']

                # Якщо немає сусідів
                return textures['wall_block']

        render_background(screen, background_grid, camera)

        # Упорядкування об'єктів для малювання за координатою `y`
        render_objects = []

        # Додаємо блоки
        for block in blocks:
            render_objects.append((block.rect.y, block))

        # Додаємо всі статуї як єдине ціле
        for statue in statues:
            render_objects.append((statue.rect.bottom, statue))  # Використовуємо нижню координату статуї

        # Додаємо гравця
        render_objects.append((player.rect.bottom, player))  # Використовуємо нижню координату гравця

        # Додаємо інші об'єкти (предмети, вороги, NPC)
        for item in items:
            render_objects.append((item.rect.y, item))
        for enemy in enemies:
            render_objects.append((enemy.rect.y, enemy))
        for npc in npcs:
            render_objects.append((npc.rect.y, npc))

        # Сортуємо об'єкти за координатою `y`
        render_objects.sort(key=lambda obj: obj[0])

        # Малюємо об'єкти в правильному порядку
        for _, obj in render_objects:
            obj.draw(screen, camera)

        # --- Малюємо геми гравця після гравця ---
        if player is not None:
            draw_player_gems(player, screen)

        # --- Малюємо спливаючі повідомлення про шкоду ---
        update_and_draw_damage_popups(screen, camera)

        #if level_name != "level0.lvl":
        #    dark_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        #    dark_overlay.fill((0, 0, 0, 220))
        #    light_radius = 200
        #    player_center = camera.apply_rect(player.rect).center
        #    light_mask = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        #    pygame.draw.circle(light_mask, (0, 0, 0, 0), player_center, light_radius)
        #    pygame.draw.circle(light_mask, (0, 0, 0, 220), player_center, light_radius + 30)
        #    dark_overlay.blit(light_mask, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
        #    screen.blit(dark_overlay, (0, 0))

        # --- ENEMY DAMAGE TO PLAYER ---
        for enemy in enemies:
            # Получаем позицию врага на экране
            enemy_screen_rect = camera.apply_rect(enemy.rect)
            # Размеры полоски
            bar_width = enemy_screen_rect.width
            bar_height = 8
            bar_x = enemy_screen_rect.x
            bar_y = enemy_screen_rect.y - bar_height - 4  # чуть выше врага
            # Значення здоров'я
            enemy_health = getattr(enemy, "health", 1)
            # Для коректного відображення максимального здоров'я на полосці
            if not hasattr(enemy, "_max_health"):
                enemy._max_health = enemy_health
            enemy_max_health = enemy._max_health
            if enemy_max_health <= 0:
                enemy_max_health = 1
            health_ratio = max(0, min(1, enemy_health / enemy_max_health))
            # Фон полоски
            pygame.draw.rect(screen, (60, 60, 60), (bar_x, bar_y, bar_width, bar_height), border_radius=3)
            # Заповнена частина
            pygame.draw.rect(screen, (200, 40, 40), (bar_x, bar_y, int(bar_width * health_ratio), bar_height), border_radius=3)
            # Рамка
            pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 1, border_radius=3)

        # --- ОТОБРАЖЕНИЕ ЗДОРОВ'Я ИГРОКА ---
        # Нарисовать полоску здоровья і текст в левом верхнем углу, поверх всіх ассетів
        health_bar_x = 30
        health_bar_y = 30
        health_bar_width = 300
        health_bar_height = 32
        # --- Максимальне здоров'я: статичне, не зменшується від ударів ---
        if not hasattr(player, "max_health") or player.max_health is None:
            player.max_health = getattr(player, "health", 100)
        max_health = player.max_health
        current_health = max(0, getattr(player, "health", 0))
        health_ratio = min(1.0, current_health / max_health) if max_health > 0 else 0
        # Фон полоски
        pygame.draw.rect(screen, (60, 60, 60), (health_bar_x, health_bar_y, health_bar_width, health_bar_height), border_radius=8)
        # Заповнена частина
        pygame.draw.rect(screen, (200, 40, 40), (health_bar_x, health_bar_y, int(health_bar_width * health_ratio), health_bar_height), border_radius=8)
        # Рамка
        pygame.draw.rect(screen, (255, 255, 255), (health_bar_x, health_bar_y, health_bar_width, health_bar_height), 2, border_radius=8)
        # Текст: текуще/максимальне здоров'я (без процентов)
        health_text = menu_font.render(f"Здоров'я: {current_health}/{max_health}", True, (255, 255, 255))
        health_text_rect = health_text.get_rect()
        health_text_rect.topleft = (health_bar_x, health_bar_y + health_bar_height + 6)
        screen.blit(health_text, health_text_rect)

        # --- Отображение иконки и количества зелий справа от полоски здоровья ---
        if potion_icon is not None:
            potion_x = health_bar_x + health_bar_width + 24
            potion_y = health_bar_y + (health_bar_height - potion_icon.get_height()) // 2
            screen.blit(potion_icon, (potion_x, potion_y))
            pot_text = menu_font.render(f"x{player_potions}", True, (255, 255, 255))
            pot_text_rect = pot_text.get_rect(midleft=(potion_x + potion_icon.get_width() + 8, potion_y + potion_icon.get_height() // 2))
            screen.blit(pot_text, pot_text_rect)

        # --- Додаємо: якщо здоров'я гравця <= 0, показуємо екран "Ви загинули" ---
        if current_health <= 0:
            showing_game_over = True
            showing_level = False
            cursor.draw(screen)
            pygame.display.flip()
            continue

        # Якщо меню характеристик увімкнено, малюємо його
        if showing_stats:
            screen.blit(pause_menu_image, pause_menu_rect)  # Відображення зображення меню
            stat_text = settings_font.render("Характеристики", True, (255, 255, 255))  # Білий текст
            stat_text_rect = stat_text.get_rect(center=(SCREEN_WIDTH // 2, int(SCREEN_HEIGHT * 0.24)))
            screen.blit(stat_text, stat_text_rect)

            # --- Показываем максимальное здоровье из player.max_health ---
            health_text = menu_font.render(f"Здоров'я: {player.health}/{player.max_health}", True, (255, 255, 255))
            health_text_rect = health_text.get_rect(topleft=(int(SCREEN_WIDTH * 0.4), int(SCREEN_HEIGHT * 0.33)))
            screen.blit(health_text, health_text_rect)
            
            protection_text = menu_font.render(f"Захист: {player.protection}", True, (255, 255, 255))
            protection_text_rect = protection_text.get_rect(topleft=(int(SCREEN_WIDTH * 0.4), int(SCREEN_HEIGHT * 0.43)))
            screen.blit(protection_text, protection_text_rect)
            
            atk_text = menu_font.render(f"Атака: {player.atk}", True, (255, 255, 255))
            atk_text_rect = atk_text.get_rect(topleft=(int(SCREEN_WIDTH * 0.4), int(SCREEN_HEIGHT * 0.53)))
            screen.blit(atk_text, atk_text_rect)
            
            speed_text = menu_font.render(f"Швидкість: {player.speed}", True, (255, 255, 255))
            speed_text_rect = speed_text.get_rect(topleft=(int(SCREEN_WIDTH * 0.4), int(SCREEN_HEIGHT * 0.63)))
            screen.blit(speed_text, speed_text_rect)
            
            luck_text = menu_font.render(f"Удача: {player.luck}", True, (255, 255, 255))
            luck_text_rect = luck_text.get_rect(topleft=(int(SCREEN_WIDTH * 0.4), int(SCREEN_HEIGHT * 0.73)))
            screen.blit(luck_text, luck_text_rect)
 
        # --- Обробка подій рівня ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:

                running = False
            elif event.type == pygame.VIDEORESIZE:
                SCREEN_WIDTH, SCREEN_HEIGHT = event.size
                screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
                update_scaled_images()
                # Update fonts
                font = pygame.font.Font("assets/fonts/Hitch-hike.otf", int(SCREEN_HEIGHT * 0.1))
                title_font = pygame.font.Font("assets/fonts/Hitch-hike.otf", int(SCREEN_HEIGHT * 0.145)) 
                menu_font = pygame.font.Font("assets/fonts/Hitch-hike.otf", int(SCREEN_HEIGHT * 0.047))
                settings_font = pygame.font.Font("assets/fonts/Hitch-hike.otf", int(SCREEN_HEIGHT * 0.075))
                # Update main menu background
                mainmenu_bg = pygame.image.load(str(INTERFACE_DIR / "mainmenu.png")).convert_alpha()
                mainmenu_bg = pygame.transform.smoothscale(mainmenu_bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
                # Update menu/button positions
                MENU_X = int(SCREEN_WIDTH * 0.07)
                menu_positions = [
                    (MENU_X, int(SCREEN_HEIGHT * 0.4)),
                    (MENU_X, int(SCREEN_HEIGHT * 0.52)),
                    (MENU_X, int(SCREEN_HEIGHT * 0.64)),
                    (MENU_X, int(SCREEN_HEIGHT * 0.76))
                ]
                button_positions = {
                    "continue": (int(SCREEN_WIDTH * 0.39), int(SCREEN_HEIGHT * 0.4)),
                    "saves": (int(SCREEN_WIDTH * 0.39), int(SCREEN_HEIGHT * 0.55)),
                    "exit": (int(SCREEN_WIDTH * 0.39), int(SCREEN_HEIGHT * 0.7)),
                }
                settings_button_positions = {
                    "back": (int(SCREEN_WIDTH * 0.05), int(SCREEN_HEIGHT * 0.80)),
                    "default": (int(SCREEN_WIDTH * 0.28), int(SCREEN_HEIGHT * 0.80)),
                    "save_back": (int(SCREEN_WIDTH * 0.51), int(SCREEN_HEIGHT * 0.80)),
                    "save": (int(SCREEN_WIDTH * 0.74), int(SCREEN_HEIGHT * 0.80)),
                }
                # Do NOT break or continue here, let the frame finish!
            # --- Додано: обробка подій меню паузи ---
            if is_paused and not showing_stats and not showing_settings:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos
                    for button_name, button_pos in button_positions.items():
                        button_rect = pause_menu_buttons.get_rect(topleft=button_pos)
                        if button_rect.collidepoint(mouse_pos):
                            print(f"Кнопка '{button_name}' натиснута.")
                            if button_name == "continue":
                                is_paused = False
                            elif button_name == "saves":
                                print("Відкриття меню збережень...")
                                # --- Исправлено: открываем меню сохранений ---
                                showing_saves = True
                                is_paused = False
                                selected_save_slot = None
                                debug_state()
                            elif button_name == "exit":
                                showing_level = False
                                showing_menu = True
                                is_paused = False
                    break  # <-- заменено continue на break
                # ВАЖЛИВО: обробка ESC має бути тут, а не в окремому elif нижче!
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    is_paused = False
                    break  # <-- заменено continue на break

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if showing_stats:
                        showing_stats = False
                        debug_state()
                    elif showing_settings:
                        showing_settings = False
                        is_paused = True
                        debug_state()
                    elif showing_saves:
                        showing_saves = False
                        is_paused = True
                        debug_state()
                    elif is_paused:
                        is_paused = False
                        debug_state()
                    elif not is_paused and not showing_stats and not showing_settings:
                        is_paused = True
                        debug_state()
                elif event.key == pygame.K_c:
                    showing_stats = not showing_stats
                # --- Лечение по кнопке E ---
                elif event.key == pygame.K_e:
                    if (
                        player_potions > 0
                        and hasattr(player, "health")
                        and hasattr(player, "max_health")
                        and player.health < player.max_health
                    ):
                        heal_amount = 25
                        player.health = min(getattr(player, "health", 0) + heal_amount, getattr(player, "max_health", 100))
                        player_potions -= 1
                        add_damage_popup(player.rect.centerx, player.rect.top - 20, f"+{heal_amount}", (0, 255, 0))
            elif event.type == pygame.KEYUP:
                if event.key in pressed_keys:
                    pressed_keys.discard(event.key)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:  # ПКМ
                mouse_pos = event.pos
                print(f"[DEBUG] ПКМ координати кліку: {mouse_pos}")
                clicked_any_statue = False
                for statue in statues:
                    statue_screen_rect = camera.apply_rect(statue.rect)
                    print(f"[DEBUG] Перевірка статуї {statue.type} rect={statue_screen_rect}")
                    if statue_screen_rect.collidepoint(mouse_pos):
                        clicked_any_statue = True
                        print(f"[DEBUG] ПКМ по статуї: {statue.type} at {statue_screen_rect.topleft}")
                        # Виправлено: базова частина типу статуї (наприклад, 'statue40')
                        if len(statue.type) >= 7:
                            base = statue.type[:7]  # 'statue40', 'statue41', ...
                            try:
                                num = int(statue.type[7:])
                            except Exception:
                                num = 0
                        else:
                            base = statue.type
                            num = 0
                        # --- Додаємо блокування після 5 кліку/текстури statue*5 ---
                        if num == 5:
                            print(f"[DEBUG] Досягнуто останньої текстури {statue.type}, подальше оновлення заблоковано.")
                            break  # Не оновлюємо більше текстуру

                        # --- Додаємо приховування гемів при кліках по statueXX ---
                        # Для кожної статуї, приховуємо відповідний гем
                        statue_gem_map = {
                            "statue40": "gem11",
                            "statue41": "gem12",
                            "statue42": "gem13",
                            "statue43": "gem14",
                            "statue44": "gem15",
                            "statue50": "gem21",
                            "statue51": "gem22",
                            "statue52": "gem23",
                            "statue53": "gem24",
                            "statue54": "gem25",
                            "statue60": "gem31",
                            "statue61": "gem32",
                            "statue62": "gem33",
                            "statue63": "gem34",
                            "statue64": "gem35",
                            "statue70": "gem41",
                            "statue71": "gem42",
                            "statue72": "gem43",
                            "statue73": "gem44",
                            "statue74": "gem45",
                            "statue80": "gem51",
                            "statue81": "gem52",
                            "statue82": "gem53",
                            "statue83": "gem54",
                            "statue84": "gem55",
                        }

                        # --- Додаємо умову: перехід statueXX -> statueXX+1 тільки якщо відповідний гем True ---
                        # Наприклад, statue40 -> statue41 тільки якщо gem12 == True
                        next_num = num + 1
                        next_type = f"{base}{next_num}"
                        required_gem = None
                        if base.startswith("statue4") and 0 <= num < 5:
                            required_gem = f"gem1{next_num}"
                        elif base.startswith("statue5") and 0 <= num < 5:
                            required_gem = f"gem2{next_num}"
                        elif base.startswith("statue6") and 0 <= num < 5:
                            required_gem = f"gem3{next_num}"
                        elif base.startswith("statue7") and 0 <= num < 5:
                            required_gem = f"gem4{next_num}"
                        elif base.startswith("statue8") and 0 <= num < 5:
                            required_gem = f"gem5{next_num}"

                        # Якщо намагаємось перейти на наступну статую, перевіряємо відповідний гем
                        if 0 <= num < 5:
                            if required_gem and hasattr(player, required_gem):
                                if not getattr(player, required_gem):
                                    print(f"[DEBUG] Не можна перейти на {next_type}, бо {required_gem} == False")
                                    break  # Не дозволяємо зміну типу
                            
                        gem_to_hide = statue_gem_map.get(statue.type)
                        if gem_to_hide and hasattr(player, gem_to_hide):
                            setattr(player, gem_to_hide, False)
                            print(f"[DEBUG] Гем {gem_to_hide} приховано (player.{gem_to_hide} = False)")
                        
                        # Додаємо тільки для statue40...statue44 (тобто при переході на statue41...statue45)
                        if base.startswith("statue4") and 0 <= num < 5:
                            player.protection += 5
                            print(f"[DEBUG] protection збільшено, тепер: {player.protection}")
                            
                        if base.startswith("statue5") and 0 <= num < 5:
                            player.health += 25
                            if hasattr(player, "max_health"):
                                player.max_health += 25
                            else:
                                player.max_health = player.health
                            print(f"[DEBUG] health збільшено, тепер: {player.health}, max_health: {player.max_health}")
                            
                        if base.startswith("statue6") and 0 <= num < 5:
                            player.atk += 10
                            print(f"[DEBUG] atk збільшено, тепер: {player.atk}")
                            

                        if base.startswith("statue7") and 0 <= num < 5:
                            player.speed += 1
                            print(f"[DEBUG] speed збільшено, тепер: {player.speed}")
                            
                        if base.startswith("statue8") and 0 <= num < 5:
                            player.luck += 1
                            print(f"[DEBUG] luck збільшено, тепер: {player.luck}")

                        # Змінюємо номер (циклічно 0-5)
                        if 0 <= num < 5:
                            num += 1
                        else:
                            num = 0
                        new_type = f"{base}{num}"
                        print(f"[DEBUG] Спроба змінити тип статуї на: {new_type}")
                        if new_type in textures:
                            statue.type = new_type
                            statue.texture = textures[new_type]
                            print(f"[DEBUG] Текстура статуї змінена на {new_type}")
                        else:
                            print(f"[DEBUG] Текстура {new_type} не знайдена в textures")
                        break
                    save_statues_state(statues)  # Зберігаємо стан статуй після кожного кліку
                if not clicked_any_statue:
                    print(f"[DEBUG] ПКМ не по жодній статуї. Координати кліку: {mouse_pos}")
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # ЛКМ
                mouse_pos = event.pos
                for item in items:
                    item_screen_rect = camera.apply_rect(item.rect)
                    # Отримуємо поточний час
                    current_time = pygame.time.get_ticks()
                    # --- Нове: Проверяем дистанцию и отсутствие стены между игроком и сундуком ---
                    # Проверяем, что курсор на сундуке
                    if item_screen_rect.collidepoint(mouse_pos) and getattr(item, "current_frame", 0) == 0:
                        # Проверяем дистанцию между игроком и сундуком (по центрам)
                        player_center = player.rect.center
                        item_center = item.rect.center
                        dx = player_center[0] - item_center[0]
                        dy = player_center[1] - item_center[1]
                        distance = (dx ** 2 + dy ** 2) ** 0.5
                        max_distance = 120  # Можно настроить
                        if distance > max_distance:
                            print("[DEBUG] Сундук слишком далеко для открытия.")
                            continue
                        # Проверяем прямую видимость (нет стены между игроком и сундуком)
                        def has_line_of_sight(start, end, blocks):
                            # Брезенхем по прямой между start и end, проверяем пересечение с solid блоками
                            steps = int(max(abs(end[0] - start[0]), abs(end[1] - start[1])) // 10) + 1
                            for i in range(1, steps):
                                x = int(start[0] + (end[0] - start[0]) * i / steps)
                                y = int(start[1] + (end[1] - start[1]) * i / steps)
                                point_rect = pygame.Rect(x, y, 4, 4)
                                for block in blocks:
                                    if block.is_solid and block.rect.colliderect(point_rect):
                                        return False
                            return True
                        if not has_line_of_sight(player_center, item_center, blocks):
                            print("[DEBUG] Между игроком и сундуком есть стена!")
                            continue
                        # --- Якщо все умови виконані, відкриваємо сундук ---
                        item.current_frame = 1
                        item.clicked_time = pygame.time.get_ticks()
        if is_paused:
            render_pause_menu(screen, pause_menu_image, pause_menu_buttons, button_positions, title_font, menu_font)
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                for button_name, button_pos in button_positions.items():
                    button_rect = pause_menu_buttons.get_rect(topleft=button_pos)
                    if button_rect.collidepoint(mouse_pos):
                        print(f"Кнопка '{button_name}' натиснута.")
                        if button_name == "continue":
                            is_paused = False
                            debug_state()
                        elif button_name == "saves":
                            print("Відкриття меню збережень...")
                            showing_saves = True
                            is_paused = False
                            selected_save_slot = None
                            debug_state()
                        elif button_name == "settings":
                            print("Відкриття меню налаштувань...")
                            showing_settings = True
                            is_paused = False
                            debug_state()
                        elif button_name == "exit":
                            showing_level = False
                            showing_menu = True
                            is_paused = False
                            debug_state()
        
        if showing_settings:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            screen.blit(overlay, (0, 0))
            render_settings_menu(screen, settings_menu_image, settings_menu_buttons, settings_button_positions, title_font, settings_font, menu_font)
            slider_x = int(SCREEN_WIDTH * 0.26)
            slider_y = int(SCREEN_HEIGHT * 0.36)
            slider_width = int(SCREEN_WIDTH * 0.22)
            slider_height = 10
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif ( event.type == pygame.MOUSEBUTTONDOWN or ( event.type == pygame.MOUSEMOTION and getattr(event, "buttons", (0,))[0] )) and slider_x <= event.pos[0] <= slider_x + slider_width and slider_y - 10 <= event.pos[1] <= slider_y + slider_height + 10:
                    mouse_pos = event.pos
                    # --- Повзунок гучності ---
                    #if (slider_x <= mouse_pos[0] <= slider_x + slider_width and
                    #  slider_y - 10 <= mouse_pos[1] <= slider_y + slider_height + 10):
                    ### DEBUG ###
                    print(f"MOUSE ={event.type},{getattr(event, "buttons", (0,))[0]},")
                    new_volume = (mouse_pos[0] - slider_x) / slider_width
                    new_volume = max(0, min(1, new_volume))
                    current_volume = new_volume
                    pygame.mixer.music.set_volume(current_volume)
                    settings["volume"] = int(current_volume * 100)
                elif event.type == pygame.MOUSEBUTTONDOWN: 
                    mouse_pos = event.pos
                    # --- Кнопки меню налаштувань ---
                    for button_name, button_pos in settings_button_positions.items():
                        button_rect = settings_menu_buttons.get_rect(topleft=button_pos)
                        if button_rect.collidepoint(mouse_pos):
                            print(f"Кнопка '{button_name}' натиснута в меню налаштувань.")
                            if button_name == "back":
                                loaded_settings = load_settings_from_file()
                                if loaded_settings:
                                    settings.clear()
                                    settings.update(loaded_settings)
                                    current_volume = settings.get("volume", 100) / 100
                                    pygame.mixer.music.set_volume(current_volume)
                                showing_settings = False
                            elif button_name == "default":
                                set_default_settings()
                            elif button_name == "save_back":
                                settings["volume"] = int(current_volume * 100)
                                save_settings_to_file(settings)
                                showing_settings = False
                            elif button_name == "save":
                                settings["volume"] = int(current_volume * 100)
                                save_settings_to_file(settings)
                    # --- Чекбокси ---
                    hints_rect = pygame.Rect(int(SCREEN_WIDTH * 0.42), int(SCREEN_HEIGHT * 0.45), 30, 30)
                    if hints_rect.collidepoint(mouse_pos):
                        settings["hints"] = not settings.get("hints", True)
                    windowed_rect = pygame.Rect(int(SCREEN_WIDTH * 0.42), int(SCREEN_HEIGHT * 0.45) + int(SCREEN_HEIGHT * 0.09), 30, 30)
                    if windowed_rect.collidepoint(mouse_pos):
                        settings["fullscreen"] = not settings.get("fullscreen", False)
                        if settings["fullscreen"]:
                            screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
                        else:
                            screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
                    level_select_rect = pygame.Rect(int(SCREEN_WIDTH * 0.42), int(SCREEN_HEIGHT * 0.45) + 2 * int(SCREEN_HEIGHT * 0.09), 30, 30)
                    if level_select_rect.collidepoint(mouse_pos):
                        settings["level_select"] = not settings.get("level_select", False)
                elif event.type == pygame.MOUSEMOTION and getattr(event, "buttons", (0,))[0]:
                    # --- Повзунок гучності drag ---
                    mouse_pos = event.pos
                    if (slider_x <= mouse_pos[0] <= slider_x + slider_width and
                        slider_y - 10 <= mouse_pos[1] <= slider_y + slider_height + 10):
                        new_volume = (mouse_pos[0] - slider_x) / slider_width
                        new_volume = max(0, min(1, new_volume))
                        current_volume = new_volume
                        pygame.mixer.music.set_volume(current_volume)
                        settings["volume"] = int(current_volume * 100)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        showing_settings = False
                elif event.type == pygame.KEYUP:
                    if event.key in pressed_keys:
                        pressed_keys.discard(event.key)
            cursor.draw(screen)
            pygame.display.flip()
            continue
        elif showing_saves:
            slot_rects, save_rect, load_rect, back_rect = render_saves_menu(screen, menu_font, pause_menu_image, pause_menu_buttons, SAVE_SLOTS, selected_save_slot)
            cursor.draw(screen)
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos
                    for slot, rect in slot_rects:
                        if rect.collidepoint(mouse_pos):
                            selected_save_slot = slot
                            break
                    if back_rect and back_rect.collidepoint(mouse_pos):
                        showing_saves = False
                        is_paused = True
                        selected_save_slot = None
                        break
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        selected_save_slot = None
                        showing_saves = False
                        is_paused = True
            continue
        current_time = pygame.time.get_ticks()
        for item in items:
            if item.current_frame == 1:
                if current_time - item.clicked_time >= 500:
                    item.current_frame = 2

            # --- Додаємо: якщо current_frame == 2, даємо гравцю випадковий гем або зілля лікування ---
            if item.current_frame == 2 and not getattr(item, "reward_given", False):
                reward_type = random.choice(["gem", "potion"])
                if reward_type == "gem":
                    # Список всіх можливих гемів у гравця
                    gem_names = [f"gem{x}{y}" for x in range(1, 6) for y in range(1, 6)]
                    random.shuffle(gem_names)
                    gem_awarded = False
                    for gem in gem_names:
                        # Якщо такого атрибута немає або він False, даємо його
                        if hasattr(player, gem) and not getattr(player, gem):
                            setattr(player, gem, True)
                            gem_awarded = True
                            break
                else:
                    # Додаємо зілля лікування
                    showing_potions = settings.get("showing_potions", True)
                    player_potions += 1
                item.reward_given = True  # Позначаємо, що нагорода вже видана для цього item

        # --- Оновлення стану гри, якщо не на паузі ---
        if not is_paused and not showing_stats and not showing_settings:
            for enemy in enemies:
                initial_position = enemy.rect.topleft
                distance_to_player = ((enemy.rect.centerx - player.rect.centerx) ** 2 +
                                      (enemy.rect.centery - player.rect.centery) ** 2) ** 0.5
                if distance_to_player <= 600:
                    path_blocked = False
                    if enemy.rect.x != player.rect.x:
                        step = 1 if enemy.rect.x < player.rect.x else -1
                        for x in range(enemy.rect.x, player.rect.x, step * TILE_SIZE):
                            if any(block.is_solid and block.rect.collidepoint(x, enemy.rect.centery) for block in blocks):
                                path_blocked = True
                                break
                    if enemy.rect.y != player.rect.y and not path_blocked:
                        step = 1 if enemy.rect.y < player.rect.y else -1
                        for y in range(enemy.rect.y, player.rect.y, step * TILE_SIZE):
                            if any(block.is_solid and block.rect.collidepoint(enemy.rect.centerx, y) for block in blocks):
                                path_blocked = True
                                break
                    if not path_blocked:
                        enemy.move_towards_player(player.rect, blocks)
                        enemy.rect.x += enemy.dx
                        for block in blocks:
                                if block.is_solid and enemy.rect.colliderect(block.rect):
                                    enemy.rect.x = initial_position[0]
                                break
                        for statue in statues:
                            if statue.is_solid and enemy.rect.colliderect(statue.rect):
                                enemy.rect.x = initial_position[0]
                                break
                        enemy.rect.y += enemy.dy
                        for block in blocks:
                            if block.is_solid and enemy.rect.colliderect(block.rect):
                                enemy.rect.y = initial_position[1]
                                break
                        for statue in statues:
                            if statue.is_solid and enemy.rect.colliderect(statue.rect):
                                enemy.rect.y = initial_position[1]
                                break
                    for statue in statues:
                        if statue.is_solid and enemy.rect.colliderect(statue.rect):
                            enemy.rect.topleft = initial_position
                            break
                    # --- ВРАГИ НАНОСЯТ УРОН ---
                    if player.rect.colliderect(enemy.rect):
                        enemy.dx = 0
                        enemy.dy = 0
                        # Добавляем урон врага игроку
                        if not hasattr(enemy, "attack_cooldown"):
                            enemy.attack_cooldown = 0
                        if enemy.attack_cooldown <= 0:
                            damage = getattr(enemy, "damage", 5)  # По умолчанию 5 урона
                            effective_damage = max(1, int(damage * (1 - getattr(player, "protection", 0) / 100)))
                            player.health -= effective_damage
                            # --- Add damage popup for player ---
                            add_damage_popup(player.rect.centerx, player.rect.top, f"-{effective_damage}", (255, 0, 0))
                            enemy.attack_cooldown = 30  # 30 кадров задержка между ударами (~0.5 сек при 60 FPS)
                        else:
                            enemy.attack_cooldown -= 1
                        enemy.dx = 0
                enemy.dy = 0

            # --- УДАРИ ПО ІГРОКАМ (по кнопці пробел) ---
            if pygame.key.get_pressed()[pygame.K_SPACE]:
                enemies_to_remove = []
                for enemy in enemies:
                    if player.rect.colliderect(enemy.rect):
                        if not hasattr(enemy, "hit_cooldown"):
                            enemy.hit_cooldown = 0
                        if enemy.hit_cooldown <= 0:
                            player_damage = getattr(player, "atk", 10)
                            prev_health = getattr(enemy, "health", 10)
                            enemy.health = prev_health - player_damage
                            # --- Add damage popup for enemy ---
                            add_damage_popup(enemy.rect.centerx, enemy.rect.top, f"-{player_damage}", (255, 255, 0))
                            if enemy.health <= 0:
                                # --- Якщо убит босс, появляется телепорт ---
                                if hasattr(enemy, "type") and "boss" in enemy.type:
                                    npcs.append(Npc(
                                        enemy.rect.x,
                                        enemy.rect.y,
                                        "teleport",
                                        {
                                            'enter': textures['enter'],
                                            'teleport': textures['teleport']
                                        }
                                    ))
                                    boss_defeated_and_portal_used = False
                                enemies_to_remove.append(enemy)
                            else:
                                enemy.hit_cooldown = 15
                        else:
                            enemy.hit_cooldown -= 1
                # Remove dead enemies after the loop
                for enemy in enemies_to_remove:
                    if enemy in enemies:
                        enemies.remove(enemy)
        
            keys = {pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d}
            pressed = pygame.key.get_pressed()
            active_keys = {key for key in keys if pressed[key]}
            player.handle_input(active_keys)
            if not active_keys:
                player.dx = 0
                player.dy = 0
            player.update(blocks, items, statues)
            camera.update(player)


        # Перевірка колізій з ворогами
        for enemy in enemies:
            if player.rect.colliderect(enemy.rect):
                overlap_rect = player.rect.clip(enemy.rect)
                if overlap_rect.width > 0 and overlap_rect.height > 0:
                    enemy.attack(player)

        # Перевірка колізії з NPC типу 'Enter' або 'Teleport'
        for npc in npcs:
            if player.rect.colliderect(npc.rect):
                if npc.type == 'enter' and not level_transitioning:
                    if settings.get("level_select", False):
                        # --- Діалог вибору рівня ---
                        selected_file = select_level_file()
                        if selected_file:
                            print(f"Вибрано рівень: {selected_file}")
                            # --- Зберігаємо стан гемів і статуй перед переходом ---
                            save_player_gems_state(player)
                            save_statues_state(statues)
                            level_transitioning = True
                            level_path = Path(selected_file)
                            player = None
                            camera = None
                            background_grid = None
                            statues = None  # залишаємо для явного скидання
                            # Після цього цикл ініціалізує новий рівень автоматично
                            level_transitioning = False
                        else:
                            print("Вибір рівня скасовано.")
                        break
                    else:
                        # --- Цикл по уровням: после портала грузим следующий номер ---
                        if boss_defeated_and_portal_used:
                            # Try to load next level by number
                            next_level_path = LEVELS_DIR / f"level{current_level_number}.lvl"
                            # If file doesn't exist, cycle to level1.lvl
                            if not next_level_path.exists():
                                current_level_number = 1
                                next_level_path = LEVELS_DIR / f"level{current_level_number}.lvl"
                            print(f"Завантаження рівня {next_level_path.name} (цикл по рівнях)...")
                            save_player_gems_state(player)
                            save_statues_state(statues)
                            level_transitioning = True
                            level_path = next_level_path
                            player = None
                            camera = None
                            background_grid = None
                            statues = None
                            boss_defeated_and_portal_used = False  # Reset flag after entering
                            level_transitioning = False
                        else:
                            print("Завантаження рівня level1...")
                            save_player_gems_state(player)
                            save_statues_state(statues)
                            level_transitioning = True
                            level_path = LEVELS_DIR / "level1.lvl"
                            player = None
                            camera = None
                            background_grid = None
                            statues = None
                            level_transitioning = False
                        break
                elif npc.type == 'teleport' and not level_transitioning:
                    print("Телепортація на рівень level0...")
                    # --- Зберігаємо стан гемів і статуй перед переходом ---
                    save_player_gems_state(player)
                    save_statues_state(statues)
                    level_transitioning = True
                    level_path = LEVELS_DIR / "level0.lvl"
                    player = None
                    camera = None
                    background_grid = None
                    statues = None
                    level_transitioning = False
                    boss_defeated_and_portal_used = True
                    current_level_number += 1  # <--- INCREMENT LEVEL NUMBER for next cave entry
                    break

        # --- Рендер меню налаштувань після обробки подій ---
    if showing_settings:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        screen.blit(mainmenu_bg, (0, 0))  # Малюємо фон головного меню
        screen.blit(overlay, (0, 0))     # Малюємо напівпрозорий шар
        if 'rotating_image' not in globals() or 'rotating_image_rect' not in globals():
            update_scaled_images()
        try:
            rotation_angle = (rotation_angle + 1) % 360  # Збільшуємо кут обертання
        except NameError:
            rotation_angle = 0
        rotated_image = pygame.transform.rotate(rotating_image, rotation_angle)
        rotated_rect = rotated_image.get_rect(center=rotating_image_rect.center)
        screen.blit(rotated_image, rotated_rect.topleft)
        render_settings_menu(screen, settings_menu_image, settings_menu_buttons, settings_button_positions,title_font, settings_font, menu_font)
        slider_x = int(SCREEN_WIDTH * 0.26)
        slider_y = int(SCREEN_HEIGHT * 0.36)
        slider_width = int(SCREEN_WIDTH * 0.22)
        slider_height = 10
        for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif ( event.type == pygame.MOUSEBUTTONDOWN 
                or ( event.type == pygame.MOUSEMOTION and getattr(event, "buttons", (0,))[0] )) and slider_x <= event.pos[0] <= slider_x + slider_width and slider_y - 10 <= event.pos[1] <= slider_y + slider_height + 10:
                    mouse_pos = event.pos
                    # --- Повзунок гучності ---
                    #if (slider_x <= mouse_pos[0] <= slider_x + slider_width and
                    #  slider_y - 10 <= mouse_pos[1] <= slider_y + slider_height + 10):
                    ### DEBUG ###
                    print(f"MOUSE ={event.type},{getattr(event, 'buttons', (0,))[0]},")
                    new_volume = (mouse_pos[0] - slider_x) / slider_width
                    new_volume = max(0, min(1, new_volume))
                    current_volume = new_volume
                    pygame.mixer.music.set_volume(current_volume)
                    settings["volume"] = int(current_volume * 100)
                elif event.type == pygame.MOUSEBUTTONDOWN: 
                    mouse_pos = event.pos
                    # --- Кнопки меню налаштувань ---
                    for button_name, button_pos in settings_button_positions.items():
                        button_rect = settings_menu_buttons.get_rect(topleft=button_pos)
                        if button_rect.collidepoint(mouse_pos):
                            print(f"Кнопка '{button_name}' натиснута в меню налаштувань.")
                            if button_name == "back":
                                loaded_settings = load_settings_from_file()
                                if loaded_settings:
                                    settings.clear()
                                    settings.update(loaded_settings)
                                    current_volume = settings.get("volume", 100) / 100
                                    pygame.mixer.music.set_volume(current_volume)
                                showing_settings = False
                                showing_menu = True
                            elif button_name == "default":
                                set_default_settings()
                            elif button_name == "save_back":
                                settings["volume"] = int(current_volume * 100)
                                save_settings_to_file(settings)
                                showing_settings = False
                                showing_menu = True
                            elif button_name == "save":
                                settings["volume"] = int(current_volume * 100)
                                save_settings_to_file(settings)
                    # --- Чекбокси ---
                    hints_rect = pygame.Rect(int(SCREEN_WIDTH * 0.42), int(SCREEN_HEIGHT * 0.45), 30, 30)
                    if hints_rect.collidepoint(mouse_pos):
                        settings["hints"] = not settings.get("hints", True)
                    windowed_rect = pygame.Rect(int(SCREEN_WIDTH * 0.42), int(SCREEN_HEIGHT * 0.45) + int(SCREEN_HEIGHT * 0.09), 30, 30)
                    if windowed_rect.collidepoint(mouse_pos):
                        settings["fullscreen"] = not settings.get("fullscreen", False)
                        # --- Переход в оконный режим при снятии флажка ---
                        if settings["fullscreen"]:
                            screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
                        else:
                            screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
                    level_select_rect = pygame.Rect(int(SCREEN_WIDTH * 0.42), int(SCREEN_HEIGHT * 0.45) + 2 * int(SCREEN_HEIGHT * 0.09), 30, 30)
                    if level_select_rect.collidepoint(mouse_pos):
                        settings["level_select"] = not settings.get("level_select", False)
                elif event.type == pygame.MOUSEMOTION and getattr(event, "buttons", (0,))[0]:
                    # --- Повзунок гучності drag ---
                    mouse_pos = event.pos
                    if (slider_x <= mouse_pos[0] <= slider_x + slider_width and
                        slider_y - 10 <= mouse_pos[1] <= slider_y + slider_height + 10):
                        new_volume = (mouse_pos[0] - slider_x) / slider_width
                        new_volume = max(0, min(1, new_volume))
                        current_volume = new_volume
                        pygame.mixer.music.set_volume(current_volume)
                        settings["volume"] = int(current_volume * 100)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        showing_settings = False
                elif event.type == pygame.KEYUP:
                    if event.key in pressed_keys:
                        pressed_keys.discard(event.key)
                        cursor.draw(screen)
                        pygame.display.flip()
                continue

        if showing_saves:
            slot_rects, save_rect, load_rect, back_rect = render_saves_menu(screen, menu_font, pause_menu_image, pause_menu_buttons, SAVE_SLOTS, selected_save_slot)
            cursor.draw(screen)
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos
                    for slot, rect in slot_rects:
                        if rect.collidepoint(mouse_pos):
                            selected_save_slot = slot
                            break
                    if back_rect and back_rect.collidepoint(mouse_pos):
                        showing_saves = False
                        is_paused = True
                        selected_save_slot = None
                        break
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        selected_save_slot = None
                        showing_saves = False
                        is_paused = True
            continue
        if is_paused and not showing_stats and not showing_settings:
            render_pause_menu(screen, pause_menu_image, pause_menu_buttons, button_positions, title_font, font, menu_font)
            cursor.draw(screen)
            pygame.display.flip()
            continue  # Просто малюємо меню паузи і переходимо до наступного кадру
        cursor.draw(screen)
        pygame.display.flip()
    elif showing_settings:
        # --- Додаємо напівпрозорий фон для меню налаштувань з головного меню ---
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        screen.blit(mainmenu_bg, (0, 0))  # Малюємо фон головного меню
        screen.blit(overlay, (0, 0))     # Малюємо напівпрозорий шар
        if 'rotating_image' not in globals() or 'rotating_image_rect' not in globals():
            update_scaled_images()
        try:
            rotation_angle = (rotation_angle + 1) % 360  # Збільшуємо кут обертання
        except NameError:
            rotation_angle = 0
        rotated_image = pygame.transform.rotate(rotating_image, rotation_angle)
        rotated_rect = rotated_image.get_rect(center=rotating_image_rect.center)
        screen.blit(rotated_image, rotated_rect.topleft)
        render_settings_menu(screen, settings_menu_image, settings_menu_buttons, settings_button_positions, title_font, settings_font, menu_font)
        slider_x = int(SCREEN_WIDTH * 0.26)
        slider_y = int(SCREEN_HEIGHT * 0.36)
        slider_width = int(SCREEN_WIDTH * 0.22)
        slider_height = 10
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # --- Добавлено: обработка ресайза окна в меню настроек ---
            elif event.type == pygame.VIDEORESIZE:
                SCREEN_WIDTH, SCREEN_HEIGHT = event.w, event.h
                screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
                update_scaled_images()
                button_positions = {
                    "continue": (int(SCREEN_WIDTH * 0.39), int(SCREEN_HEIGHT * 0.4)),
                    "saves": (int(SCREEN_WIDTH * 0.39), int(SCREEN_HEIGHT * 0.55)),
                    "exit": (int(SCREEN_WIDTH * 0.39), int(SCREEN_HEIGHT * 0.7)),
                }
                settings_button_positions = {
                    "back": (int(SCREEN_WIDTH * 0.05), int(SCREEN_HEIGHT * 0.80)),
                    "default": (int(SCREEN_WIDTH * 0.28), int(SCREEN_HEIGHT * 0.80)),
                    "save_back": (int(SCREEN_WIDTH * 0.51), int(SCREEN_HEIGHT * 0.80)),
                    "save": (int(SCREEN_WIDTH * 0.74), int(SCREEN_HEIGHT * 0.80)),
                }
                continue
            elif ( event.type == pygame.MOUSEBUTTONDOWN 
                or ( event.type == pygame.MOUSEMOTION and getattr(event, "buttons", (0,))[0] ) 
              ) and slider_x <= event.pos[0] <= slider_x + slider_width and slider_y - 10 <= event.pos[1] <= slider_y + slider_height + 10:
                mouse_pos = event.pos
                # --- Повзунок гучності ---
                print(f"MOUSE ={event.type},{getattr(event, 'buttons', (0,))[0]},")
                new_volume = (mouse_pos[0] - slider_x) / slider_width
                new_volume = max(0, min(1, new_volume))
                current_volume = new_volume
                pygame.mixer.music.set_volume(current_volume)
                settings["volume"] = int(current_volume * 100)
            elif event.type == pygame.MOUSEBUTTONDOWN: 
                mouse_pos = event.pos
                # --- Кнопки меню налаштувань ---
                for button_name, button_pos in settings_button_positions.items():
                    button_rect = settings_menu_buttons.get_rect(topleft=button_pos)
                    if button_rect.collidepoint(mouse_pos):
                        print(f"Кнопка '{button_name}' натиснута в меню налаштувань.")
                        if button_name == "back":
                            loaded_settings = load_settings_from_file()
                            if loaded_settings:
                                settings.clear()
                                settings.update(loaded_settings)
                                current_volume = settings.get("volume", 100) / 100
                                pygame.mixer.music.set_volume(current_volume)
                            showing_settings = False
                            showing_menu = True
                        elif button_name == "default":
                            set_default_settings()
                        elif button_name == "save_back":
                            settings["volume"] = int(current_volume * 100)
                            save_settings_to_file(settings)
                            showing_settings = False
                            showing_menu = True
                        elif button_name == "save":
                            settings["volume"] = int(current_volume * 100)
                            save_settings_to_file(settings)
                                    # --- Чекбокси ---
                    hints_rect = pygame.Rect(int(SCREEN_WIDTH * 0.42), int(SCREEN_HEIGHT * 0.45), 30, 30)
                    if hints_rect.collidepoint(mouse_pos):
                        settings["hints"] = not settings.get("hints", True)
                    windowed_rect = pygame.Rect(int(SCREEN_WIDTH * 0.42), int(SCREEN_HEIGHT * 0.45) + int(SCREEN_HEIGHT * 0.09), 30, 30)
                    if windowed_rect.collidepoint(mouse_pos):
                        settings["fullscreen"] = not settings.get("fullscreen", False)
                        # --- Переход в оконный режим при снятии флажка ---
                        if settings["fullscreen"]:
                            screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
                        else:
                            screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
                    level_select_rect = pygame.Rect(int(SCREEN_WIDTH * 0.42), int(SCREEN_HEIGHT * 0.45) + 2 * int(SCREEN_HEIGHT * 0.09), 30, 30)
                    if level_select_rect.collidepoint(mouse_pos):
                        settings["level_select"] = not settings.get("level_select", False)

                    elif event.type == pygame.MOUSEMOTION and getattr(event, "buttons", (0,))[0]:
                    # --- Повзунок гучності drag ---
                        mouse_pos = event.pos
                    if (slider_x <= mouse_pos[0] <= slider_x + slider_width and
                        slider_y - 10 <= mouse_pos[1] <= slider_y + slider_height + 10):
                        new_volume = (mouse_pos[0] - slider_x) / slider_width
                        new_volume = max(0, min(1, new_volume))
                        current_volume = new_volume
                        pygame.mixer.music.set_volume(current_volume)
                        settings["volume"] = int(current_volume * 100)
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            showing_settings = False
                    elif event.type == pygame.KEYUP:
                        if event.key in pressed_keys:
                            pressed_keys.discard(event.key)
                        cursor.draw(screen)
                        pygame.display.flip()
            continue

        if showing_saves:
            slot_rects, save_rect, load_rect, back_rect = render_saves_menu(screen, menu_font, pause_menu_image, pause_menu_buttons, SAVE_SLOTS, selected_save_slot)
            cursor.draw(screen)
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos
                    for slot, rect in slot_rects:
                        if rect.collidepoint(mouse_pos):
                            selected_save_slot = slot
                            break
                    if back_rect and back_rect.collidepoint(mouse_pos):
                        showing_saves = False
                        is_paused = True
                        selected_save_slot = None
                        break
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        selected_save_slot = None
                        showing_saves = False
                        is_paused = True
            continue
        if is_paused and not showing_stats and not showing_settings:
            render_pause_menu(screen, pause_menu_image, pause_menu_buttons, button_positions, title_font, font, menu_font)
            cursor.draw(screen)
            pygame.display.flip()
            continue  # Просто малюємо меню паузи і переходимо до наступного кадру
        cursor.draw(screen)
        pygame.display.flip()
        continue
    elif showing_saves:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        screen.blit(mainmenu_bg, (0, 0))  # Малюємо фон головного меню
        screen.blit(overlay, (0, 0))     # Малюємо напівпрозорий шар
        if 'rotating_image' not in globals() or 'rotating_image_rect' not in globals():
            update_scaled_images()
        try:
            rotation_angle = (rotation_angle + 1) % 360  # Збільшуємо кут обертання
        except NameError:
            rotation_angle = 0
        rotated_image = pygame.transform.rotate(rotating_image, rotation_angle)
        rotated_rect = rotated_image.get_rect(center=rotating_image_rect.center)
        screen.blit(rotated_image, rotated_rect.topleft)
        slot_rects, save_rect, load_rect, back_rect = render_saves_menu(screen, menu_font, pause_menu_image, pause_menu_buttons, SAVE_SLOTS, selected_save_slot)
        cursor.draw(screen)
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # --- Добавлено: обработка ресайза окна в меню настроек ---
            elif event.type == pygame.VIDEORESIZE:
                SCREEN_WIDTH, SCREEN_HEIGHT = event.w, event.h
                screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
                update_scaled_images()
                button_positions = {
                    "continue": (int(SCREEN_WIDTH * 0.39), int(SCREEN_HEIGHT * 0.4)),
                    "saves": (int(SCREEN_WIDTH * 0.39), int(SCREEN_HEIGHT * 0.55)),
                    "exit": (int(SCREEN_WIDTH * 0.39), int(SCREEN_HEIGHT * 0.7)),
                }
                settings_button_positions = {
                    "back": (int(SCREEN_WIDTH * 0.05), int(SCREEN_HEIGHT * 0.80)),
                    "default": (int(SCREEN_WIDTH * 0.28), int(SCREEN_HEIGHT * 0.80)),
                    "save_back": (int(SCREEN_WIDTH * 0.51), int(SCREEN_HEIGHT * 0.80)),
                    "save": (int(SCREEN_WIDTH * 0.74), int(SCREEN_HEIGHT * 0.80)),
                }
                continue
            elif ( event.type == pygame.MOUSEBUTTONDOWN 
                or ( event.type == pygame.MOUSEMOTION and getattr(event, "buttons", (0,))[0] ) 
              ) and slider_x <= event.pos[0] <= slider_x + slider_width and slider_y - 10 <= event.pos[1] <= slider_y + slider_height + 10:
                mouse_pos = event.pos
                # --- Повзунок гучності ---
                print(f"MOUSE ={event.type},{getattr(event, 'buttons', (0,))[0]},")
                new_volume = (mouse_pos[0] - slider_x) / slider_width
                new_volume = max(0, min(1, new_volume))
                current_volume = new_volume
                pygame.mixer.music.set_volume(current_volume)
                settings["volume"] = int(current_volume * 100)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                for slot, rect in slot_rects:
                    if rect.collidepoint(mouse_pos):
                        selected_save_slot = slot
                        break
                if back_rect and back_rect.collidepoint(mouse_pos):
                    showing_saves = False
                    selected_save_slot = None
                    # Повертаємося у головне меню, якщо не в грі
                    if not showing_level:
                        showing_menu = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:

                    selected_save_slot = None
                    showing_saves = False
                    if not showing_level:
                        showing_menu = True
    # --- Game Over Screen ---
    elif showing_game_over:
        screen.blit(mainmenu_bg, (0, 0))
        button_rect = render_game_over(screen, title_font, menu_font)
        cursor.draw(screen)
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if button_rect.collidepoint(event.pos):
                    # --- Скидаємо стан гри та запускаємо нову гру ---
                    showing_game_over = False
                    showing_menu = False
                    showing_level = True
                    level_path = LEVELS_DIR / "level0.lvl"
                    player = None
                    camera = None
                    background_grid = None
                    blocks = []
                    enemies = []
                    items = []
                    statues = []
                    npcs = []
                    pressed_keys.clear()
                    showing_stats = False
                    is_paused = False
                    showing_settings = False
                    showing_saves = False
                    selected_save_slot = None
                    level_data = None
                    player_gems_state = {}
                    statues_state = {}
                    break
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    showing_game_over = False
                    showing_menu = False
                    showing_level = True
                    level_path = LEVELS_DIR / "level0.lvl"
                    player = None
                    camera = None
                    background_grid = None
                    blocks = []
                    enemies = []
                    items = []
                    statues = []
                    npcs = []
                    pressed_keys.clear()
                    showing_stats = False
                    is_paused = False
                    showing_settings = False
                    showing_saves = False
                    selected_save_slot = None
                    level_data = None
                    player_gems_state = {}
                    statues_state = {}
                    break
        continue
    cursor.draw(screen)
    pygame.display.flip()
pygame.quit()
print("Програма завершена")  # Додано: журнал для перевірки завершення програми
sys.exit()
