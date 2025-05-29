import pygame
import sys
import json
import os
from pathlib import Path
from engine.loader import (
    load_textures, generate_background_grid, determine_tree_texture, render_background, enemy_type_mapping, npc_type_mapping, statue_type_mapping, load_grass_textures, draw_player_gems
)
from engine.parser import parse_level_file
from engine.entities import Player, Block, Enemy, Item, Npc, Camera, IntStat
import tkinter as tk
from tkinter import filedialog
import random

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
        # Масштабування не застосовується, якщо не потрібно
    except pygame.error as e:
        print(f"Помилка завантаження зображення паузи: {e}")
        sys.exit()

    # Оновлення зображення кнопок паузи
    try:
        pause_menu_buttons = pygame.image.load(str(INTERFACE_DIR / "button.png")).convert_alpha()
        # Масштабування не застосовується, якщо не потрібно
    except pygame.error as e:
        print(f"Помилка завантаження зображення кнопок: {e}")
        sys.exit()

    # Оновлення зображення меню налаштувань
    try:
        settings_menu_image = pygame.image.load(str(INTERFACE_DIR / "settings_menu.png")).convert_alpha()
        # Масштабування не застосовується, якщо не потрібно
    except pygame.error as e:
        print(f"Помилка завантаження зображення меню налаштувань: {e}")
        sys.exit()

    # Оновлення зображення стрілки
    try:
        arrow_image = pygame.image.load(str(INTERFACE_DIR / "arrow.png")).convert_alpha()
        # Масштабування не застосовується, якщо не потрібно
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

pause_menu_rect = pause_menu_image.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))  # Центрування зображення

# Розташування кнопок на зображенні паузи
button_positions = {
    "continue": (int(SCREEN_WIDTH * 0.41), int(SCREEN_HEIGHT * 0.4)),
    "saves": (int(SCREEN_WIDTH * 0.41), int(SCREEN_HEIGHT * 0.5)),
    "preferences": (int(SCREEN_WIDTH * 0.41), int(SCREEN_HEIGHT * 0.6)),
    "exit": (int(SCREEN_WIDTH * 0.41), int(SCREEN_HEIGHT * 0.7)),
}

# Розташування кнопок на зображенні налаштувань
settings_button_positions = {
    "back": (int(SCREEN_WIDTH * 0.12), int(SCREEN_HEIGHT * 0.75)),
    "default": (int(SCREEN_WIDTH * 0.31), int(SCREEN_HEIGHT * 0.75)),
    "save_back": (int(SCREEN_WIDTH * 0.51), int(SCREEN_HEIGHT * 0.75)),
    "save": (int(SCREEN_WIDTH * 0.7), int(SCREEN_HEIGHT * 0.75)),
}

# Завантаження зображення для меню налаштувань
try:
    settings_menu_image = pygame.image.load(str(INTERFACE_DIR / "settings_menu.png"))
    settings_menu_buttons = pygame.image.load(str(INTERFACE_DIR / "button.png"))
except pygame.error as e:
    print(f"Помилка завантаження зображення меню налаштувань: {e}")
    sys.exit()

settings_menu_rect = settings_menu_image.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
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

def render_pause_menu(screen, pause_menu_image, pause_menu_buttons, button_positions, title_font, font, menu_font):
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
            "preferences": "Налаштування",
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

# Основний цикл
running = True
showing_menu = True
showing_level = False
is_paused = False
showing_settings = False
level_transitioning = False
showing_stats = False
menu1_played = False
current_music = None

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

# --- Додаємо: збереження стану гемів між рівнями ---
player_gems_state = {}

# --- Додаємо: збереження стану статуй між рівнями ---
statues_state = {}

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
    print(f"showing_menu={showing_menu}, showing_level={showing_level}, showing_settings={showing_settings}, is_paused={is_paused}")

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
                                debug_state()
                                # Додайте break, щоб не обробляти події далі після перемикання стану
                                break
                            elif text == "Налаштування":
                                showing_menu = False
                                showing_settings = True
                                debug_state()
                                break
                elif showing_settings:
                    for button_name, button_pos in settings_button_positions.items():
                        button_rect = settings_menu_buttons.get_rect(topleft=button_pos)
                        if button_rect.collidepoint(mouse_pos):
                            print(f"Кнопка '{button_name}' натиснута в меню налаштувань.")
                            if button_name == "back":
                                showing_settings = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        showing_settings = False
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
                        'zombie': 20,
                        'skeleton': 30,
                        'boss': 50
                    }.get(enemy_type_mapping.get(enemy['type'], 'zombie_left'), 1)
                ) for enemy in level_data['enemies']
            ]

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
            background_grid = generate_background_grid(textures, level_data, level_path.name)

            # 8. Функція determine_block_texture(x, y, blocks_set)
            # Визначення текстури блоку за оточенням — дублюється у кількох місцях.

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

        # Якщо меню характеристик увімкнено, малюємо його
        if showing_stats:
            screen.blit(pause_menu_image, pause_menu_rect)  # Відображення зображення меню
            stat_text = settings_font.render("Характеристика", True, (255, 255, 255))  # Білий текст
            stat_text_rect = stat_text.get_rect(center=(SCREEN_WIDTH // 2, int(SCREEN_HEIGHT * 0.24)))
            screen.blit(stat_text, stat_text_rect)

            health_text = menu_font.render(f"Здоров'я: {player.health}", True, (255, 255, 255))
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
            # --- Обробка подій меню паузи ---
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
                            elif button_name == "preferences":
                                showing_settings = True
                                # Не змінюйте is_paused тут, просто відкрийте налаштування
                                debug_state()
                            elif button_name == "exit":
                                showing_level = False
                                showing_menu = True
                                is_paused = False
                    continue
                # ВАЖЛИВО: обробка ESC має бути тут, а не в окремому elif нижче!
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    is_paused = False
                    continue
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if showing_stats:
                        showing_stats = False
                    elif showing_settings:
                        showing_settings = False
                        is_paused = True
                    else:
                        if not is_paused and not showing_stats and not showing_settings:
                            is_paused = True
                            render_pause_menu(screen, pause_menu_image, pause_menu_buttons, button_positions, title_font, font, menu_font)
                elif event.key == pygame.K_c:
                    showing_stats = not showing_stats
                elif not showing_stats and not showing_settings:
                    pressed_keys.add(event.key)
            elif event.type == pygame.KEYUP:
                if event.key in pressed_keys:
                    pressed_keys.discard(event.key)
            elif is_paused and not showing_stats and not showing_settings:
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
                            elif button_name == "preferences":
                                showing_settings = True
                                # Не змінюйте is_paused тут, просто відкрийте налаштування
                                debug_state()
                            elif button_name == "exit":
                                showing_level = False
                                showing_menu = True
                                is_paused = False
                    continue
                # ВАЖЛИВО: обробка ESC має бути тут, а не в окремому elif нижче!
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    is_paused = False
                continue
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
                            print(f"[DEBUG] health збільшено, тепер: {player.health}")
                            
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
                    # Обробка кліку (тільки коли ще не натиснуто)
                    if item_screen_rect.collidepoint(mouse_pos) and getattr(item, "current_frame", 0) == 0:
                        item.current_frame = 1
                        item.clicked_time = pygame.time.get_ticks()
            
        current_time = pygame.time.get_ticks()
        for item in items:
            if item.current_frame == 1:
                if current_time - item.clicked_time >= 500:
                    item.current_frame = 2

            # --- Додаємо: якщо current_frame == 2, даємо гравцю випадковий гем ---
            if item.current_frame == 2 and not hasattr(item, "gem_given"):
                # Список всіх можливих гемів у гравця
                gem_names = [f"gem{x}{y}" for x in range(1, 6) for y in range(1, 6)]
                # Вибираємо випадковий гем
                random.shuffle(gem_names)
                for gem in gem_names:
                    # Якщо такого атрибута немає або він False, даємо його
                    if hasattr(player, gem) and not getattr(player, gem):
                        setattr(player, gem, True)
                        item.gem_given = True  # Позначаємо, що гем вже видано для цього item
                        break
                else:
                    # Якщо всі геми вже True, просто позначаємо, щоб не повторювати
                    item.gem_given = True

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
                    if player.rect.colliderect(enemy.rect):
                        enemy.dx = 0
                        enemy.dy = 0
                        enemy.attack(player)
                enemy.dx = 0
                enemy.dy = 0

            keys = {pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d}
            active_keys = {key for key in pressed_keys if key in keys}
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
                        print("Завантаження рівня level1...")
                        # --- Зберігаємо стан гемів і статуй перед переходом ---
                        save_player_gems_state(player)
                        save_statues_state(statues)
                        level_transitioning = True
                        level_path = LEVELS_DIR / "level1.lvl"
                        player = None
                        camera = None
                        background_grid = None
                        statues = None  # залишаємо для явного скидання
                        # Після цього цикл ініціалізує новий рівень автоматично
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
                    statues = None  # залишаємо для явного скидання
                    # Після цього цикл ініціалізує новий рівень автоматично
                    level_transitioning = False
                    break

        # --- Рендер меню налаштувань після обробки подій ---
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
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_pos = event.pos
                    # --- Повзунок гучності ---
                    if (slider_x <= mouse_pos[0] <= slider_x + slider_width and
                        slider_y - 10 <= mouse_pos[1] <= slider_y + slider_height + 10):
                        new_volume = (mouse_pos[0] - slider_x) / slider_width
                        new_volume = max(0, min(1, new_volume))
                        current_volume = new_volume
                        pygame.mixer.music.set_volume(current_volume)
                        settings["volume"] = int(current_volume * 100)
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
            pygame.display.flip()
            continue
        # --- Рендер меню паузи після обробки подій ---
        if is_paused and not showing_stats and not showing_settings:
            render_pause_menu(screen, pause_menu_image, pause_menu_buttons, button_positions, title_font, font, menu_font)
            pygame.display.flip()
            continue  # Просто малюємо меню паузи і переходимо до наступного кадру
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
            elif event.type == pygame.MOUSEBUTTONDOWN or (event.type == pygame.MOUSEMOTION and getattr(event, "buttons", (0,))[0]):
                mouse_pos = event.pos
                # --- Повзунок гучності ---
                if (slider_x <= mouse_pos[0] <= slider_x + slider_width and
                    slider_y - 10 <= mouse_pos[1] <= slider_y + slider_height + 10):
                    new_volume = (mouse_pos[0] - slider_x) / slider_width
                    new_volume = max(0, min(1, new_volume))
                    current_volume = new_volume
                    pygame.mixer.music.set_volume(current_volume)
                    settings["volume"] = int(current_volume * 100)
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
                    if settings["fullscreen"]:
                        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
                    else:
                        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
                level_select_rect = pygame.Rect(int(SCREEN_WIDTH * 0.42), int(SCREEN_HEIGHT * 0.45) + 2 * int(SCREEN_HEIGHT * 0.09), 30, 30)
                if level_select_rect.collidepoint(mouse_pos):
                    settings["level_select"] = not settings.get("level_select", False)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    showing_settings = False
            elif event.type == pygame.KEYUP:
                if event.key in pressed_keys:
                    pressed_keys.discard(event.key)
        pygame.display.flip()

pygame.quit()
print("Програма завершена")  # Додано: журнал для перевірки завершення програми
sys.exit()