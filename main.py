import pygame
import sys
import json
import os
from pathlib import Path
from engine.loader import load_textures, generate_background_grid, determine_tree_texture, render_background, enemy_type_mapping, npc_type_mapping, statue_type_mapping, load_grass_textures
from engine.parser import parse_level_file
from engine.entities import Player, Block, Enemy, Item, Npc, Camera, IntStat
import tkinter as tk
from tkinter import filedialog

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
    # Оновлення фонового зображення
    try:
        mainmenu_bg = pygame.image.load(str(INTERFACE_DIR / "mainmenu.png")).convert_alpha()
        mainmenu_bg = pygame.transform.smoothscale(mainmenu_bg, (screen.get_width(), screen.get_height()))
    except pygame.error as e:
        print(f"Помилка завантаження фонового зображення: {e}")
        sys.exit()

try:
    # Масштабуємо rotating_image як квадрат: сторона = висота екрана
    side = SCREEN_HEIGHT
    rotating_image_raw = pygame.image.load(str(INTERFACE_DIR / "mainmaenu_particles.png")).convert_alpha()
    rotating_image = pygame.transform.smoothscale(rotating_image_raw, (side, side))
except pygame.error as e:
    print(f"Помилка завантаження зображення для обертання: {e}")
    sys.exit()
rotating_image_rect = rotating_image.get_rect(center=(SCREEN_WIDTH * 0.63, SCREEN_HEIGHT // 2))
rotation_angle = 0  # Початковий кут обертання

# Завантаження текстур
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
    slider_width = 400
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

    # --- Обробка подій для повзунка гучності та кнопок ---
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.MOUSEBUTTONDOWN or (event.type == pygame.MOUSEMOTION and event.buttons[0]):
            mouse_pos = event.pos
            # --- Повзунок гучності ---
            slider_y = int(SCREEN_HEIGHT * 0.36)
            slider_width = 400
            slider_height = 10
            slider_x_aligned = int(SCREEN_WIDTH * 0.26)
            if (slider_x_aligned <= mouse_pos[0] <= slider_x_aligned + slider_width and
                slider_y - 10 <= mouse_pos[1] <= slider_y + slider_height + 10):
                new_volume = (mouse_pos[0] - slider_x_aligned) / slider_width
                new_volume = max(0, min(1, new_volume))
                current_volume = new_volume
                pygame.mixer.music.set_volume(current_volume)
                settings["volume"] = int(current_volume * 100)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            # SAVE
            save_btn_pos = settings_button_positions["save"]
            save_btn_rect = settings_menu_buttons.get_rect(topleft=save_btn_pos)
            if save_btn_rect.collidepoint(mouse_pos):
                settings["volume"] = int(current_volume * 100)
                save_settings_to_file(settings)
            # SAVE_BACK
            save_back_btn_pos = settings_button_positions["save_back"]
            save_back_btn_rect = settings_menu_buttons.get_rect(topleft=save_back_btn_pos)
            if save_back_btn_rect.collidepoint(mouse_pos):
                settings["volume"] = int(current_volume * 100)
                save_settings_to_file(settings)
                globals()["showing_settings"] = False
            # BACK
            back_btn_pos = settings_button_positions["back"]
            back_btn_rect = settings_menu_buttons.get_rect(topleft=back_btn_pos)
            if back_btn_rect.collidepoint(mouse_pos):
                loaded_settings = load_settings_from_file()
                if loaded_settings:
                    settings.clear()
                    settings.update(loaded_settings)
                    globals()["current_volume"] = settings.get("volume", 100) / 100
                    pygame.mixer.music.set_volume(globals()["current_volume"])
                globals()["showing_settings"] = False
            # Чекбокс "Підказки"
            if hints_rect.collidepoint(mouse_pos):
                settings["hints"] = not settings.get("hints", True)
            # Чекбокс "Віконний режим"
            if windowed_rect.collidepoint(mouse_pos):
                settings["fullscreen"] = not settings.get("fullscreen", False)
                if settings["fullscreen"]:
                    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
                else:
                    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
            # Чекбокс "Вибір рівнів"
            if level_select_rect.collidepoint(mouse_pos):
                settings["level_select"] = not settings.get("level_select", False)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                globals()["showing_settings"] = False
                globals()["is_paused"] = False

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
    save_settings_to_file(settings)
    # Примусове перемальовування меню налаштувань
    render_settings_menu(
        screen,
        settings_menu_image,
        settings_menu_buttons,
        settings_button_positions,
        title_font,
        settings_font,
        menu_font
    )
    pygame.display.flip()
    
def create_player(player_start, textures):
    """
    Фабрична функція для створення Player з урахуванням TILE_SIZE та словника текстур.
    :param player_start: (x, y) координати гравця у клітинках
    :param textures: словник текстур
    :return: Player instance
    """
    return Player(
        (player_start[0] * TILE_SIZE, player_start[1] * TILE_SIZE),
        {
            "player_left": textures["player_left"],
            "player_right": textures["player_right"],
            "player_back_left": textures.get("player_back_left", textures["player_left"]),
            "player_back_right": textures.get("player_back_right", textures["player_right"])
        }
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

def debug_state():
    print(f"showing_menu={showing_menu}, showing_level={showing_level}, showing_settings={showing_settings}, is_paused={is_paused}")

current_frame = 0
frame_delay = 10  # Кількість кадрів між зміною зображення
frame_counter = 0

while running:
    clock.tick(60)
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
        rotation_angle = (rotation_angle + 1) % 360  # Збільшуємо кут обертання
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
                        'zombie': 1,
                        'skeleton': 3,
                        'boss': 5
                    }.get(enemy_type_mapping.get(enemy['type'], 'zombie_left'), 1)
                ) for enemy in level_data['enemies']
            ]

            items = [
                Item(item['x'] * TILE_SIZE, item['y'] * TILE_SIZE, item.get('is_solid', True), textures['item_frames'])
                for item in level_data['items']
            ]

            statue_type_mapping = {f"statue{key}": value for key, value in statue_type_mapping.items()}
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

            # Створення набору координат блоків для швидкого доступу
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

            # Завантаження текстур ворогів
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

            # Мапінг типів ворогів із файлу рівня до ключів у словнику текстур
            enemies = [
                Enemy(
                    enemy['x'], enemy['y'], enemy_type_mapping.get(enemy['type'], 'zombie_left'), enemy_textures,
                    health={
                        'zombie': 1,
                        'skeleton': 3,
                        'boss': 5
                    }.get(enemy_type_mapping.get(enemy['type'], 'zombie_left'), 1)  # Значення здоров'я за замовчуванням — 1
                ) for enemy in level_data['enemies']
            ]
            items = [
                Item(item['x'] * TILE_SIZE, item['y'] * TILE_SIZE, item.get('is_solid', True), textures['item_frames'])
                for item in level_data['items']
            ]

            # Оновлення ключів у statue_type_mapping
            statue_type_mapping = {f"{key}": value for key, value in statue_type_mapping.items()}

            # Перевірка оновлених ключів
            print(f"Оновлені ключі в statue_type_mapping: {list(statue_type_mapping.keys())}")

            statues = [
                IntStat(
                    statue['x'] * TILE_SIZE,
                    statue['y'] * TILE_SIZE,
                    statue.get('is_solid', True),
                    f"statue{statue['type']}",  # тип як str
                    textures  # словник текстур
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

            # Ініціалізація камери
            camera = Camera(level_data['width'] * TILE_SIZE, level_data['height'] * TILE_SIZE)

            # Генерація сітки фону на основі розміру рівня
            background_grid = generate_background_grid(textures, level_data, level_path.name)

        screen.fill((0, 0, 0))
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

        # Якщо меню характеристик увімкнено, малюємо його
        if showing_stats:
            screen.blit(pause_menu_image, pause_menu_rect)  # Відображення зображення меню
            stat_text = font.render("Характеристика", True, (255, 255, 255))  # Білий текст
            stat_text_rect = stat_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 270))
            screen.blit(stat_text, stat_text_rect)

            health_text = menu_font.render(f"Здоров'я: {player.health} (+5)", True, (255, 255, 255))
            health_text_rect = health_text.get_rect(center=(SCREEN_WIDTH // 2 - 85, SCREEN_HEIGHT // 2 - 150))
            screen.blit(health_text, health_text_rect)
            
            protection_text = menu_font.render(f"Захист: {player.protection} (+5%)", True, (255, 255, 255))
            protection_text_rect = protection_text.get_rect(center=(SCREEN_WIDTH // 2 - 85, SCREEN_HEIGHT // 2 - 50))
            screen.blit(protection_text, protection_text_rect)
            
            atk_text = menu_font.render(f"Атака: {player.atk}", True, (255, 255, 255))
            atk_text_rect = atk_text.get_rect(center=(SCREEN_WIDTH // 2 - 140, SCREEN_HEIGHT // 2 + 50))
            screen.blit(atk_text, atk_text_rect)
            
            speed_text = menu_font.render(f"Швидкість: {player.speed}", True, (255, 255, 255))
            speed_text_rect = speed_text.get_rect(center=(SCREEN_WIDTH // 2 - 95, SCREEN_HEIGHT // 2 + 150))
            screen.blit(speed_text, speed_text_rect)
            
            luck_text = menu_font.render(f"Удача: {player.luck}", True, (255, 255, 255))
            luck_text_rect = luck_text.get_rect(center=(SCREEN_WIDTH // 2 - 145, SCREEN_HEIGHT // 2 + 250))
            screen.blit(luck_text, luck_text_rect)

        # --- Обробка подій рівня ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if showing_stats:
                        showing_stats = False
                    elif showing_settings:
                        showing_settings = False
                    else:
                        if not is_paused and not showing_stats and not showing_settings:
                            is_paused = True
                            render_pause_menu(screen, pause_menu_image, pause_menu_buttons, button_positions, title_font, font, menu_font)
                            debug_state()
                        elif is_paused and not showing_stats and not showing_settings:
                            is_paused = False
                            debug_state()
                elif event.key == pygame.K_c:
                    showing_stats = not showing_stats
                elif not showing_stats and not showing_settings:
                    pressed_keys.add(event.key)
            elif event.type == pygame.KEYUP:
                if event.key in pressed_keys:
                    pressed_keys.discard(event.key)
            elif event.type == pygame.MOUSEBUTTONDOWN and is_paused:
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
                            is_paused = True  # Просто перемикаємо прапорці, не рендеримо тут меню!
                            debug_state()
                        elif button_name == "exit":
                            showing_level = False
                            running_level = False
                            showing_menu = True
                            is_paused = False
                            

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
                            level_transitioning = True
                            level_path = Path(selected_file)
                            player = None
                            camera = None
                            background_grid = None
                            # Після цього цикл ініціалізує новий рівень автоматично
                            level_transitioning = False
                        else:
                            print("Вибір рівня скасовано.")
                        break
                    else:
                        print("Завантаження рівня level1...")
                        level_transitioning = True
                        level_path = LEVELS_DIR / "level1.lvl"
                        player = None
                        camera = None
                        background_grid = None
                        # Після цього цикл ініціалізує новий рівень автоматично
                        level_transitioning = False
                        break
                elif npc.type == 'teleport' and not level_transitioning:
                    print("Телепортація на рівень level0...")
                    level_transitioning = True
                    level_path = LEVELS_DIR / "level0.lvl"
                    player = None
                    camera = None
                    background_grid = None
                    # Після цього цикл ініціалізує новий рівень автоматично
                    level_transitioning = False
                    break

        # --- Рендер меню налаштувань після обробки подій ---
        if showing_settings and is_paused:
            render_settings_menu(screen, settings_menu_image, settings_menu_buttons, settings_button_positions, title_font, settings_font, menu_font)
            pygame.display.flip()
            continue
        # --- Рендер меню паузи після обробки подій ---
        if is_paused and not showing_stats and not showing_settings:
            render_pause_menu(screen, pause_menu_image, pause_menu_buttons, button_positions, title_font, font, menu_font)
            pygame.display.flip()
            continue
        pygame.display.flip()

pygame.quit()
print("Програма завершена")  # Додано: журнал для перевірки завершення програми
sys.exit()