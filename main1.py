import pygame
import sys
from pathlib import Path
from engine.loader import load_textures, generate_background_grid, determine_tree_texture, render_background, enemy_type_mapping, npc_type_mapping, statue_type_mapping, load_grass_textures
from engine.parser import parse_level_file
from engine.entities import Player, Block, Enemy, Item, Npc, Camera, IntStat

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
pygame.display.set_caption("Меню гри")
clock = pygame.time.Clock()

# Шляхи до ресурсів
BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
INTERFACE_DIR = ASSETS_DIR / "img" / "interface"
GRASS_DIR = ASSETS_DIR / "img" / "start_loc" / "grass"
LEVELS_DIR = BASE_DIR / "levels"

# Завантаження кадрів GIF
def load_gif_frames(folder_path):
    """
    Завантажує всі кадри GIF із вказаної папки.
    :param folder_path: Шлях до папки з кадрами GIF
    :return: Список кадрів (поверхонь Pygame)
    """
    frames = []
    absolute_path = Path(folder_path).resolve()
    if not absolute_path.exists():
        print(f"Помилка: Папка {absolute_path} не існує.")
        sys.exit()

    for filename in sorted(absolute_path.iterdir()):
        if filename.suffix == ".png":  # Завантажуємо лише PNG-файли
            frame = pygame.image.load(str(filename))
            frames.append(frame)

    if not frames:
        print(f"Помилка: У папці {absolute_path} немає файлів .png.")
        sys.exit()

    return frames

# Завантаження кадрів GIF
gif_frames = load_gif_frames(INTERFACE_DIR / "mainmenu_frames")
current_frame = 0
frame_delay = 10  # Кількість кадрів між зміною зображення
frame_counter = 0

# Завантаження шрифту
try:
    font = pygame.font.Font("assets/fonts/Hitch-hike.otf", 100)
    title_font = pygame.font.Font("assets/fonts/Hitch-hike.otf", 150) 
    menu_font = pygame.font.Font("assets/fonts/Hitch-hike.otf", 50)
except FileNotFoundError as e:
    print(f"Помилка завантаження шрифту: {e}")
    sys.exit()

# Завантаження зображення стрілки
try:
    arrow_image = pygame.image.load(str(INTERFACE_DIR / "arrow.png"))
except pygame.error as e:
    print(f"Помилка завантаження зображення стрілки: {e}")
    sys.exit()

# Завантаження зображення для обертання
try:
    rotating_image = pygame.image.load(str(INTERFACE_DIR / "mainmaenu_particles.png"))
except pygame.error as e:
    print(f"Помилка завантаження зображення для обертання: {e}")
    sys.exit()

rotating_image_rect = rotating_image.get_rect(center=(SCREEN_WIDTH // 2 + 200, SCREEN_HEIGHT // 2))  # Зміщено на 100 пікселів вправо
rotation_angle = 0  # Початковий кут обертання

# Завантаження текстур
textures = load_textures()
textures.update(load_grass_textures(GRASS_DIR))

# Завантаження рівня
level_path = LEVELS_DIR / "level0.lvl"
level_data = None  # Рівень буде завантажено після натискання "Нова гра"

# Текстові елементи
menu_items = ["Нова гра", "Збереження", "Налаштування", "Вихід"]
menu_positions = [(200, 450), (200, 560), (200, 670), (200, 780)]  # Вирівнювання по лівому краю

# Основний цикл
running = True
showing_menu = True  # Меню відображається спочатку
showing_level = False  # Додано: стан для відображення рівня
is_paused = False # Додано: змінна для стану паузи
showing_settings = False # Додано: змінна для стану меню налаштувань

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
    "continue": (SCREEN_WIDTH // 2 - 160, SCREEN_HEIGHT // 2 - 75),
    "saves": (SCREEN_WIDTH // 2 - 160, SCREEN_HEIGHT // 2 + 25),
    "preferences": (SCREEN_WIDTH // 2 - 160, SCREEN_HEIGHT // 2 + 125),
    "exit": (SCREEN_WIDTH // 2 - 160, SCREEN_HEIGHT // 2 + 225),
}

# Додано: змінна для стану паузи
is_paused = False

# Додано: змінна для стану меню налаштувань
showing_settings = False

# Розташування кнопок на зображенні налаштувань
settings_button_positions = {
    "back": (SCREEN_WIDTH // 2 - 689, SCREEN_HEIGHT // 2 + 225),
    "default": (SCREEN_WIDTH // 2 - 337, SCREEN_HEIGHT // 2 + 225),
    "save_back": (SCREEN_WIDTH // 2 + 30, SCREEN_HEIGHT // 2 + 225),
    "save": (SCREEN_WIDTH // 2 + 382, SCREEN_HEIGHT // 2 + 225),
}

# Завантаження зображення для меню налаштувань
try:
    settings_menu_image = pygame.image.load(str(INTERFACE_DIR / "settings_menu.png")).convert_alpha()
    settings_menu_buttons = pygame.image.load(str(INTERFACE_DIR / "button.png"))
except pygame.error as e:
    print(f"Помилка завантаження зображення меню налаштувань: {e}")
    sys.exit()

settings_menu_rect = settings_menu_image.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))  # Центрування зображення

# Додано: прапор для запобігання повторного завантаження рівня
level_transitioning = False

def render_pause_menu(screen, pause_menu_image, pause_menu_buttons, button_positions, title_font, font, menu_font):
    """
    Малює вікно паузи та кнопки на екрані.
    """
    # Відображення зображення паузи поверх гри
    screen.blit(pause_menu_image, pause_menu_rect)

    # Додавання тексту "Пауза" зверху
    pause_text = title_font.render("Пауза", True, (255, 255, 255))  # Білий текст
    pause_text_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 270))
    screen.blit(pause_text, pause_text_rect)

    # Додавання тексту "||" під "Пауза"
    pause_separator = font.render("||", True, (255, 255, 255))  # Білий текст
    pause_separator_rect = pause_separator.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 110))
    screen.blit(pause_separator, pause_separator_rect)

    # Відображення кнопок паузи
    for button_name, button_pos in button_positions.items():
        screen.blit(pause_menu_buttons, button_pos)

        # Додавання тексту поверх кнопок
        button_text = menu_font.render({
            "continue": "Продовжити",
            "saves": "Збереження",
            "preferences": "Налаштування",
            "exit": "Вихід"
        }[button_name], True, (255, 255, 255))  # Білий текст
        button_text_rect = button_text.get_rect(center=(button_pos[0] + pause_menu_buttons.get_width() // 2,
                                                        button_pos[1] + pause_menu_buttons.get_height() // 2))
        screen.blit(button_text, button_text_rect)

def render_settings_menu(screen, settings_menu_image, settings_menu_buttons, settings_button_positions, title_font, font, menu_font):
    """
    Малює вікно налаштувань та кнопки на екрані.
    """
    # Відображення зображення налаштувань поверх гри
    screen.blit(settings_menu_image, settings_menu_rect)

    # Додавання тексту "Налаштування" зверху
    settings_text = title_font.render("Налаштування", True, (255, 255, 255))  # Білий текст
    settings_text_rect = settings_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 270))
    screen.blit(settings_text, settings_text_rect)

    # Відображення кнопок налаштувань
    for button_name, button_pos in settings_button_positions.items():
        screen.blit(settings_menu_buttons, button_pos)

        # Додавання тексту поверх кнопок
        button_text = menu_font.render({
            "back": "Повернутися",
            "default": "Стандартні налаштування",
            "save_back": "Зберегти та повернутися",
            "save": "Зберегти",
        }[button_name], True, (255, 255, 255))  # Білий текст
        button_text_rect = button_text.get_rect(center=(button_pos[0] + settings_menu_buttons.get_width() // 2,
                                                        button_pos[1] + settings_menu_buttons.get_height() // 2))
        screen.blit(button_text, button_text_rect)

def toggle_pause(is_paused):
    """
    Перемикає стан паузи.
    """
    return not is_paused

# Додано: змінна для стану меню характеристик
showing_stats = False

# Змінна для відстеження, чи була відтворена .wav
menu1_played = False

# Функція для відтворення музики
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

# Змінна для збереження поточної музики
current_music = None

# Функція для зупинки музики
def stop_music():
    """
    Зупиняє відтворення музики.
    """
    pygame.mixer.music.stop()

# Перевірка типів значень у statue_type_mapping

while running:
        # Відображення анімованого фону
        screen.blit(gif_frames[current_frame], (0, 0))
        print(f"Відображено кадр GIF: {current_frame}")  # Додано: журнал
        frame_counter += 1
        if frame_counter >= frame_delay:
            current_frame = (current_frame + 1) % len(gif_frames)  # Перехід до наступного кадру
            frame_counter = 0

        # Обертання зображення
        rotation_angle = (rotation_angle + 1) % 360  # Збільшуємо кут обертання
        rotated_image = pygame.transform.rotate(rotating_image, rotation_angle)
        rotated_rect = rotated_image.get_rect(center=rotating_image_rect.center)
        screen.blit(rotated_image, rotated_rect.topleft)
        print(f"Відображено обертаюче зображення")  # Додано: журнал

        # Обробка подій
        event_list = pygame.event.get()
        for event in event_list:
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:  # Обробляємо кліки миші тут, щоб уникнути дублювання
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
                            elif text == "Налаштування":
                                showing_menu = False
                                showing_settings = True
                elif is_paused:
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
                                is_paused = False
                            elif button_name == "exit":
                                running = False
                                running_level = False
                elif showing_settings:
                    for button_name, button_pos in settings_button_positions.items():
                        button_rect = settings_menu_buttons.get_rect(topleft=button_pos)
                        if button_rect.collidepoint(mouse_pos):
                            print(f"Кнопка '{button_name}' натиснута в меню налаштувань.")
                            if button_name == "back":
                                showing_settings = False
                                if is_paused:
                                    is_paused = True
                                else:
                                    showing_menu = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if showing_stats:
                        showing_stats = False
                    elif showing_settings:
                        showing_settings = False
                        if is_paused:
                            is_paused = True
                    else:
                        is_paused = not is_paused
                        print(f"Гра {'на паузі' if is_paused else 'продовжена'}")
                        if showing_level:
                            showing_menu = is_paused
                            showing_level = not is_paused
                        elif showing_menu:
                            showing_menu = not is_paused
                            showing_level = is_paused
                        else:
                            showing_menu = False
                            showing_level = False
                            is_paused = True
                elif event.key == pygame.K_c:
                    showing_stats = not showing_stats
                    print(f"Меню характеристик {'увімкнено' if showing_stats else 'вимкнено'}")

        if showing_menu:
            print("Відображення головного меню")
            # Відображення назви гри
            title_text = title_font.render("Slime Quest: Dungeon", True, (255, 255, 255))  # Білий колір
            title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 3, 300))  # Центрування по горизонталі
            print(f"Розмір title_text: {title_rect.width}, {title_rect.height}")  # Додано: журнал
            screen.blit(title_text, title_rect)
            print(f"Відображено назву гри")  # Додано: журнал

            # Відображення тексту
            text_rects = []  # Зберігаємо прямокутники тексту для перевірки кліків
            for i, text in enumerate(menu_items):
                rendered_text = font.render(text, True, (255, 255, 255))  # Білий колір
                text_rect = rendered_text.get_rect(topleft=menu_positions[i])  # Вирівнювання по лівому краю
                print(f"Розмір {text}: {text_rect.width}, {text_rect.height}")  # Додано: журнал
                text_rects.append((text, text_rect))  # Зберігаємо текст і його прямокутник
                screen.blit(rendered_text, text_rect)
                print(f"Відображено текст: {text}")  # Додано: журнал

            # Отримання позиції миші
            mouse_pos = pygame.mouse.get_pos()

            # Відображення стрілки при наведенні (лише одне зображення)
            arrow_drawn = False  # Флаг для контролю відображення стрілки
            for i, (_, rect) in enumerate(text_rects):
                if rect.collidepoint(mouse_pos) and not arrow_drawn:  # Якщо курсор наведений на текст
                    arrow_pos = (rect.left - 100, rect.centery - arrow_image.get_height() // 2)
                    screen.blit(arrow_image, arrow_pos)
                    arrow_drawn = True  # Встановлюємо флаг, щоб стрілка відображалася лише один раз
            pygame.display.flip()  # Додано: оновлення екрану після відображення меню
        elif is_paused and not showing_stats and not showing_settings:
            print("Відображення меню паузи")
            render_pause_menu(screen, pause_menu_image, pause_menu_buttons, button_positions, title_font, font, menu_font)
            pygame.display.flip()  # Додано: оновлення екрану після відображення меню
        elif showing_settings:
            print("Відображення меню налаштувань")
            render_settings_menu(screen, settings_menu_image, settings_menu_buttons, settings_button_positions, title_font, font, menu_font)
            pygame.display.flip()  # Додано: оновлення екрану після відображення меню
        elif showing_level:
            print("Відображення рівня")
        else:
            showing_menu = True
            showing_level = False

        # Визначаємо, яку музику потрібно відтворити
        if level_path == LEVELS_DIR / "level0.lvl":
            music_file = str(ASSETS_DIR / "audio" / "start_loc_bg2.wav")
            level_key = "level0"
        elif level_path == LEVELS_DIR / "level1.lvl":
            music_file = str(ASSETS_DIR / "audio" / "menu2.wav")
            level_key = "level1"
        else:
            music_file = None
            level_key = None

        # Виводимо інформацію для налагодження
        print(f"level_path: {level_path}")
        print(f"music_file: {music_file}")
        print(f"current_music: {current_music}")

        # Перевіряємо, чи існує файл
        if music_file and not Path(music_file).exists():
            print(f"Помилка: Файл {music_file} не знайдено!")
            music_file = None  # Щоб не було спроб відтворення

        # Відтворюємо музику, якщо вона змінилася
        if music_file and current_music != level_key:
            stop_music()
            play_music(music_file)
            current_music = level_key

        if level_data is None:
            print("Завантаження даних рівня")
            level_data = parse_level_file(level_path)

        if level_data['player_start'] is None:
            print("Помилка: Початкова позиція гравця не визначена у файлі рівня.")
            running = False
            break

        player = Player(
            (level_data['player_start'][0] * TILE_SIZE, level_data['player_start'][1] * TILE_SIZE),
            {
                "player_left": textures["player_left"],
                "player_right": textures["player_right"],
                "player_back_left": textures.get("player_back_left", textures["player_left"]),
                "player_back_right": textures.get("player_back_right", textures["player_right"])
            }
        )
        
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
        statue_type_mapping = {f"statue{key}": value for key, value in statue_type_mapping.items()}

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

        pressed_keys = set()  # Додано: набір для збереження натиснутих клавіш

        running_level = True
            
        # Основний цикл рівня
        while running_level:
            clock.tick(60)
            screen.fill((0, 0, 0))

            # Обробка подій
            event_list = pygame.event.get()
            for event in event_list:
                if event.type == pygame.QUIT:
                    running_level = False  # Закінчуємо цикл рівня, а не всю гру
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if showing_stats:
                            showing_stats = False
                        elif showing_settings:
                            showing_settings = False
                            if is_paused:
                                is_paused = True
                            else:
                                showing_menu = True
                                showing_level = False
                    else:
                        is_paused = not is_paused
                        print(f"Гра {'на паузі' if is_paused else 'продовжена'}")
                        if showing_level:
                            showing_menu = is_paused
                            showing_level = not is_paused
                        elif showing_menu:
                            showing_menu = not is_paused
                            showing_level = is_paused
                        else:
                            showing_menu = False
                            showing_level = False
                            is_paused = True
                elif event.key == pygame.K_c:
                    showing_stats = not showing_stats
                    print(f"Меню характеристик {'увімкнено' if showing_stats else 'вимкнено'}")

            # Оновлення камери
            camera.update(player)

            # Рендеринг фону з урахуванням камери
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
                screen.blit(atk_text, atk_text_rect), True, (255, 255, 255)
                
                speed_text = menu_font.render(f"Швидкість: {player.speed}", True, (255, 255, 255))
                speed_text_rect = speed_text.get_rect(center=(SCREEN_WIDTH // 2 - 95, SCREEN_HEIGHT // 2 + 150))
                screen.blit(speed_text, speed_text_rect), True, (255, 255, 255)
                
                luck_text = menu_font.render(f"Удача: {player.luck}", True, (255, 255, 255))
                luck_text_rect = luck_text.get_rect(center=(SCREEN_WIDTH // 2 - 145, SCREEN_HEIGHT // 2 + 250))
                screen.blit(luck_text, luck_text_rect), True, (255, 255, 255)
            # Рух гравця
            keys = pygame.key.get_pressed()
            player.handle_input(keys)
            player.update(blocks, items, statues)
            pygame.display.flip()
 
# Додано: змінна для стану меню налаштувань
showing_settings = False
def render_settings_menu(screen, settings_menu_image, settings_menu_buttons, settings_button_positions, title_font, font, menu_font):
    """
    Малює вікно налаштувань та кнопки на екрані.(screen, settings_menu_image, settings_menu_buttons, settings_button_positions, title_font, font, menu_font):
    """
    # Відображення зображення налаштувань поверх гри
    screen.blit(settings_menu_image, settings_menu_rect)

    # Додавання тексту "Налаштування" зверхуeen.blit(settings_menu_image, settings_menu_rect)
    settings_text = title_font.render("Налаштування", True, (255, 255, 255))  # Білий текст
    settings_text_rect = settings_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 270))
    screen.blit(settings_text, settings_text_rect)    
    # Відображення кнопок налаштувань
    for button_name, button_pos in settings_button_positions.items():
        screen.blit(settings_menu_buttons, button_pos)
    for button_name, button_pos in settings_button_positions.items():
        # Додавання тексту поверх кнопокtons, button_pos)
        button_text = menu_font.render({
            "continue": "Продовжити",
            "saves": "Збереження",        
            "preferences": "Налаштування",
            "exit": "Вихід"
        }[button_name], True, (255, 255, 255))  # Білий текст
        button_text_rect = button_text.get_rect(center=(button_pos[0] + pause_menu_buttons.get_width() // 2,
                                                        button_pos[1] + pause_menu_buttons.get_height() // 2))
        screen.blit(button_text, button_text_rect)
    pygame.quit()

print("Програма завершена")  # Додано: журнал для перевірки завершення програми
sys.exit()