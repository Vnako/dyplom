from pathlib import Path
import sys
import os
import pygame
import random

# Додаємо кореневу папку проєкту до PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine.entities import Player, Block, Enemy, Item, Npc, IntStat
from engine.parser import parse_level_file

# Ініціалізація Pygame
pygame.init()

# Константи
display_info = pygame.display.Info()
SCREEN_WIDTH, SCREEN_HEIGHT = display_info.current_w, display_info.current_h
TILE_SIZE = 100

# Базовий шлях до ресурсів
BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"
DANGEON_DIR = ASSETS_DIR / "img" / "dangeon"
ENTITIES_DIR = ASSETS_DIR / "img" / "entities"
START_LOC_DIR = ASSETS_DIR / "img" / "start_loc"
STATUE_DIR = ENTITIES_DIR / "statue"
ITEMS_DIR = ASSETS_DIR / "img" / "pick_items"

# Курсор
def load_image(path):
    return pygame.image.load(path).convert_alpha()

def load_cursor():
    return load_image("assets/img/interface/cursor.png")


# Завантаження текстур
def load_textures():
    """
    Завантажує текстури для рівнів і створінь, повертає їх у вигляді словника.
    """
    try:
        textures = {
            "block": pygame.image.load(str(DANGEON_DIR / "wall.png")),
            "wall": pygame.image.load(str(DANGEON_DIR / "wall.png")),
            "wall_top": pygame.image.load(str(DANGEON_DIR / "wall_top.png")).convert_alpha(),
            "wall_bottom": pygame.image.load(str(DANGEON_DIR / "wall_bottom.png")).convert_alpha(),
            "wall_left": pygame.image.load(str(DANGEON_DIR / "wall_left.png")).convert_alpha(),
            "wall_right": pygame.image.load(str(DANGEON_DIR / "wall_right.png")).convert_alpha(),
            "wall_right_top": pygame.image.load(str(DANGEON_DIR / "wall_right_top.png")).convert_alpha(),
            "wall_left_top": pygame.image.load(str(DANGEON_DIR / "wall_left_top.png")).convert_alpha(),
            "wall_right_bottom": pygame.image.load(str(DANGEON_DIR / "wall_right_bottom.png")).convert_alpha(),
            "wall_left_bottom": pygame.image.load(str(DANGEON_DIR / "wall_left_bottom.png")).convert_alpha(),
            "wall_top_bottom": pygame.image.load(str(DANGEON_DIR / "wall_top_bottom.png")).convert_alpha(),
            "wall_left_right": pygame.image.load(str(DANGEON_DIR / "wall_left_right.png")).convert_alpha(),
            "wall_left_right_top": pygame.image.load(str(DANGEON_DIR / "wall_left_right_top.png")).convert_alpha(),
            "wall_left_right_bottom": pygame.image.load(str(DANGEON_DIR / "wall_left_right_bottom.png")).convert_alpha(),
            "wall_right_top_bottom": pygame.image.load(str(DANGEON_DIR / "wall_right_top_bottom.png")).convert_alpha(),
            "wall_left_top_bottom": pygame.image.load(str(DANGEON_DIR / "wall_left_top_bottom.png")).convert_alpha(),
            "wall_block": pygame.image.load(str(DANGEON_DIR / "wall_block.png")),
            "dangeon_floor": pygame.image.load(str(DANGEON_DIR / "floor.png")),
            "zombie_left": pygame.image.load(str(ENTITIES_DIR / "zombie_left.png")).convert_alpha(),
            "zombie_right": pygame.image.load(str(ENTITIES_DIR / "zombie_right.png")).convert_alpha(),
            "zombie_back_left": pygame.image.load(str(ENTITIES_DIR / "zombie_back_left.png")).convert_alpha(),
            "zombie_back_right": pygame.image.load(str(ENTITIES_DIR / "zombie_back_right.png")).convert_alpha(),
            "skeleton_left": pygame.image.load(str(ENTITIES_DIR / "skeleton_left.png")).convert_alpha(),
            "skeleton_right": pygame.image.load(str(ENTITIES_DIR / "skeleton_right.png")).convert_alpha(),
            "skeleton_back_left": pygame.image.load(str(ENTITIES_DIR / "skeleton_back_left.png")).convert_alpha(),
            "skeleton_back_right": pygame.image.load(str(ENTITIES_DIR / "skeleton_back_right.png")).convert_alpha(),
            "boss_left": pygame.image.load(str(ENTITIES_DIR / "boss2.png")).convert_alpha(),
            "boss_right": pygame.image.load(str(ENTITIES_DIR / "boss2.png")).convert_alpha(),
            "boss_back_left": pygame.image.load(str(ENTITIES_DIR / "boss2.png")).convert_alpha(),
            "boss_back_right": pygame.image.load(str(ENTITIES_DIR / "boss2.png")).convert_alpha(),
            "player_left": pygame.image.load(str(ENTITIES_DIR / "player_left.png")).convert_alpha(),
            "player_right": pygame.image.load(str(ENTITIES_DIR / "player_right.png")).convert_alpha(),
            "player_back_left": pygame.image.load(str(ENTITIES_DIR / "player_back_left.png")).convert_alpha(),
            "player_back_right": pygame.image.load(str(ENTITIES_DIR / "player_back_right.png")).convert_alpha(),
            "item": pygame.image.load(str(ENTITIES_DIR / "item.png")).convert_alpha(),
            "item2": pygame.image.load(str(ENTITIES_DIR / "item2.png")).convert_alpha(),
            "item3": pygame.image.load(str(ENTITIES_DIR / "item3.png")).convert_alpha(),
            "teleport": pygame.image.load(str(ENTITIES_DIR / "teleport.png")).convert_alpha() if (ENTITIES_DIR / "teleport.png").exists() else None,
            "item_frames": [
                pygame.image.load(str(ENTITIES_DIR / "item.png")).convert_alpha(),
                pygame.image.load(str(ENTITIES_DIR / "item2.png")).convert_alpha(),
                pygame.image.load(str(ENTITIES_DIR / "item3.png")).convert_alpha()
            ],
            "floor": pygame.image.load(str(START_LOC_DIR / "grass" / "grass2.png")),
            "enter": pygame.image.load(str(START_LOC_DIR / "dangeon_enter.png")).convert_alpha(),
            "tree": pygame.image.load(str(START_LOC_DIR / "tree.png")).convert_alpha(),
            "trees_left": pygame.image.load(str(START_LOC_DIR / "trees_left.png")).convert_alpha(),
            "trees_center": pygame.image.load(str(START_LOC_DIR / "trees_center.png")).convert_alpha(),
            "trees_right": pygame.image.load(str(START_LOC_DIR / "trees_right.png")).convert_alpha(),
            "trees_top": pygame.image.load(str(START_LOC_DIR / "trees_top.png")).convert_alpha(),
            "trees_center_top": pygame.image.load(str(START_LOC_DIR / "trees_center_top.png")).convert_alpha(),
            "statue40": pygame.image.load(str(STATUE_DIR / "statue10.png")).convert_alpha(),
            "statue41": pygame.image.load(str(STATUE_DIR / "statue11.png")).convert_alpha(),
            "statue42": pygame.image.load(str(STATUE_DIR / "statue12.png")).convert_alpha(),
            "statue43": pygame.image.load(str(STATUE_DIR / "statue13.png")).convert_alpha(),
            "statue44": pygame.image.load(str(STATUE_DIR / "statue14.png")).convert_alpha(),
            "statue45": pygame.image.load(str(STATUE_DIR / "statue15.png")).convert_alpha(),
            "statue50": pygame.image.load(str(STATUE_DIR / "statue20.png")).convert_alpha(),
            "statue51": pygame.image.load(str(STATUE_DIR / "statue21.png")).convert_alpha(),
            "statue52": pygame.image.load(str(STATUE_DIR / "statue22.png")).convert_alpha(),
            "statue53": pygame.image.load(str(STATUE_DIR / "statue23.png")).convert_alpha(),
            "statue54": pygame.image.load(str(STATUE_DIR / "statue24.png")).convert_alpha(),
            "statue55": pygame.image.load(str(STATUE_DIR / "statue25.png")).convert_alpha(),
            "statue60": pygame.image.load(str(STATUE_DIR / "statue30.png")).convert_alpha(),
            "statue61": pygame.image.load(str(STATUE_DIR / "statue31.png")).convert_alpha(),
            "statue62": pygame.image.load(str(STATUE_DIR / "statue32.png")).convert_alpha(),
            "statue63": pygame.image.load(str(STATUE_DIR / "statue33.png")).convert_alpha(),
            "statue64": pygame.image.load(str(STATUE_DIR / "statue34.png")).convert_alpha(),
            "statue65": pygame.image.load(str(STATUE_DIR / "statue35.png")).convert_alpha(),
            "statue70": pygame.image.load(str(STATUE_DIR / "statue40.png")).convert_alpha(),
            "statue71": pygame.image.load(str(STATUE_DIR / "statue41.png")).convert_alpha(),
            "statue72": pygame.image.load(str(STATUE_DIR / "statue42.png")).convert_alpha(),
            "statue73": pygame.image.load(str(STATUE_DIR / "statue43.png")).convert_alpha(),
            "statue74": pygame.image.load(str(STATUE_DIR / "statue44.png")).convert_alpha(),
            "statue75": pygame.image.load(str(STATUE_DIR / "statue45.png")).convert_alpha(),
            "statue80": pygame.image.load(str(STATUE_DIR / "statue50.png")).convert_alpha(),
            "statue81": pygame.image.load(str(STATUE_DIR / "statue51.png")).convert_alpha(),
            "statue82": pygame.image.load(str(STATUE_DIR / "statue52.png")).convert_alpha(),
            "statue83": pygame.image.load(str(STATUE_DIR / "statue53.png")).convert_alpha(),
            "statue84": pygame.image.load(str(STATUE_DIR / "statue54.png")).convert_alpha(),
            "statue85": pygame.image.load(str(STATUE_DIR / "statue55.png")).convert_alpha(),
            "gem11": pygame.image.load(str(ITEMS_DIR / "gem11.png")).convert_alpha(),
            "gem12": pygame.image.load(str(ITEMS_DIR / "gem12.png")).convert_alpha(),
            "gem13": pygame.image.load(str(ITEMS_DIR / "gem13.png")).convert_alpha(),
            "gem14": pygame.image.load(str(ITEMS_DIR / "gem14.png")).convert_alpha(),
            "gem15": pygame.image.load(str(ITEMS_DIR / "gem15.png")).convert_alpha(),
            "gem21": pygame.image.load(str(ITEMS_DIR / "gem21.png")).convert_alpha(),
            "gem22": pygame.image.load(str(ITEMS_DIR / "gem22.png")).convert_alpha(),
            "gem23": pygame.image.load(str(ITEMS_DIR / "gem23.png")).convert_alpha(),
            "gem24": pygame.image.load(str(ITEMS_DIR / "gem24.png")).convert_alpha(),
            "gem25": pygame.image.load(str(ITEMS_DIR / "gem25.png")).convert_alpha(),
            "gem31": pygame.image.load(str(ITEMS_DIR / "gem31.png")).convert_alpha(),
            "gem32": pygame.image.load(str(ITEMS_DIR / "gem32.png")).convert_alpha(),
            "gem33": pygame.image.load(str(ITEMS_DIR / "gem33.png")).convert_alpha(),
            "gem34": pygame.image.load(str(ITEMS_DIR / "gem34.png")).convert_alpha(),
            "gem35": pygame.image.load(str(ITEMS_DIR / "gem35.png")).convert_alpha(),
            "gem41": pygame.image.load(str(ITEMS_DIR / "gem41.png")).convert_alpha(),
            "gem42": pygame.image.load(str(ITEMS_DIR / "gem42.png")).convert_alpha(),
            "gem43": pygame.image.load(str(ITEMS_DIR / "gem43.png")).convert_alpha(),
            "gem44": pygame.image.load(str(ITEMS_DIR / "gem44.png")).convert_alpha(),
            "gem45": pygame.image.load(str(ITEMS_DIR / "gem45.png")).convert_alpha(),
            "gem51": pygame.image.load(str(ITEMS_DIR / "gem51.png")).convert_alpha(),
            "gem52": pygame.image.load(str(ITEMS_DIR / "gem52.png")).convert_alpha(),
            "gem53": pygame.image.load(str(ITEMS_DIR / "gem53.png")).convert_alpha(),
            "gem54": pygame.image.load(str(ITEMS_DIR / "gem54.png")).convert_alpha(),
            "gem55": pygame.image.load(str(ITEMS_DIR / "gem55.png")).convert_alpha(),
        }
        # Перевірка наявності текстур
        for texture_name, texture_path in [
            ("enter", START_LOC_DIR / "dangeon_enter.png"),
            ("teleport", ENTITIES_DIR / "teleport.png")
        ]:
            if not texture_path.exists():
                print(f"Попередження: Файл '{texture_name}' відсутній за шляхом {texture_path}.")
            elif textures[texture_name] is None:
                print(f"Попередження: Текстура '{texture_name}' не завантажена.")
        # Додано: журнал для перевірки текстур
        for key in ["enter", "teleport"]:
            if textures[key] is None:
                print(f"Попередження: Текстура '{key}' не завантажена.")
        return textures
    except pygame.error as e:
        print(f"Помилка завантаження текстур: {e}")
        sys.exit()

def determine_tree_texture(x, y, blocks_set, textures):
    """
    Визначає текстуру дерева залежно від його позиції.
    :param x: Координата X дерева
    :param y: Координата Y дерева
    :param blocks_set: Набір координат усіх блоків
    :param textures: Словник текстур
    :return: Відповідна текстура дерева
    """
    has_left = (x - 1, y) in blocks_set
    has_right = (x + 1, y) in blocks_set

    if not has_left:
        return textures['trees_left']
    elif has_left and has_right:
        return textures['trees_center']
    elif not has_right:
        return textures['trees_right']
    else:
        return textures['trees_center']  # За замовчуванням

# Мапінг типів ворогів із файлу рівня до ключів у словнику текстур
enemy_type_mapping = {
    '1': 'zombie',
    '2': 'skeleton',
    '3': 'boss'
}

npc_type_mapping = {
    'e': 'enter',    
    't': 'teleport'
}

statue_type_mapping = {  
    '4': 'statue4',
    '5': 'statue5',
    '6': 'statue6',
    '7': 'statue7',
    '8': 'statue8'
}

# Завантаження рівня
def load_level(level_path, textures):
    """
    Завантажує рівень і створює об'єкти на основі даних рівня.
    """
    level_data = parse_level_file(level_path)

    player = Player(level_data['player_start'], {
        "player_left": textures["player_left"],
        "player_right": textures["player_right"],
        "player_back_left": textures.get("player_back_left", textures["player_left"]),
        "player_back_right": textures.get("player_back_right", textures["player_right"])
    })

    blocks_set = {(block['x'], block['y']) for block in level_data['blocks']}

    blocks = [
        Block(
            block['x'] * TILE_SIZE,
            block['y'] * TILE_SIZE,
            block['is_solid'],
            determine_tree_texture(block['x'], block['y'], blocks_set, textures) if level_path.name == "level0.lvl" else textures['block']
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
        Item(item['x'], item['y'], item['is_solid'], textures['item_frames'])  # Використовується item['is_solid']
        for item in level_data['items']
    ]

    statues = [
        IntStat(
            statue['x'] * TILE_SIZE, statue['y'] * TILE_SIZE, statue['is_solid'], statue_type_mapping.get(statue['type'], 'statue40'), {
                'statue4': textures['statue40'],
                'statue5': textures['statue50'],
                'statue6': textures['statue60'],
                'statue7': textures['statue70'],
                'statue8': textures['statue80']
            },
        )
        for statue in level_data['statues']
    ]

    npcs = [
        Npc(
            npc['x'] * TILE_SIZE, npc['y'] * TILE_SIZE, npc_type_mapping.get(npc['type'], 'teleport'), {
                'enter': textures['enter'],
                'teleport': textures['teleport']
            }
        )
        for npc in level_data['npc']
    ]
    
    return {
        "player": player,
        "blocks": blocks,
        "enemies": enemies,
        "items": items,
        "statues": statues,  # Додано: статуї
        "npcs": npcs,
        "level_data": level_data
    }

def generate_background_grid(textures, level_data, level_name):
    """
    Генерує сітку текстур для фону на основі розміру рівня.
    :param textures: Словник текстур
    :param level_data: Дані рівня
    :param level_name: Назва рівня
    :return: Сітка текстур
    """
    grid = []
    for y in range(0, level_data['height'] * TILE_SIZE, TILE_SIZE):
        row = []
        for x in range(0, level_data['width'] * TILE_SIZE, TILE_SIZE):
            if level_name == "level0.lvl":
                # Для стартовой локации трава
                random_grass = random.choice([
                    textures['grass1'],
                    textures['grass2'],
                    textures['grass3'],
                    textures['grass4'],
                    textures['grass5'],
                    textures['grass6'],
                    textures['grass7']
                ])
                row.append(random_grass)
            else:
                # Для всех остальных — каменный пол
                row.append(textures['dangeon_floor'])
        grid.append(row)
    return grid

def render_background(screen, background_grid, camera):
    """
    Малює фон рівня на основі попередньо згенерованої сітки текстур трави з урахуванням камери.
    :param screen: Поверхня для малювання
    :param background_grid: Сітка текстур трави
    :param camera: Камера для зміщення
    """
    for row_index, row in enumerate(background_grid):
        for col_index, texture in enumerate(row):
            x = col_index * TILE_SIZE
            y = row_index * TILE_SIZE
            screen.blit(texture, camera.apply_rect(pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)))

def load_grass_textures(grass_dir):
    """
    Завантажує текстури трави з вказаної директорії.
    :param grass_dir: Шлях до директорії з текстурами трави
    :return: Словник із текстурами трави
    """
    grass_textures = {}
    for i in range(1, 8):  # grass1.png до grass7.png
        texture_path = grass_dir / f"grass{i}.png"
        grass_textures[f"grass{i}"] = pygame.image.load(str(texture_path))
    return grass_textures

def draw_player_gems(player, screen):
    """
    Малює зображення гемів у верхній частині екрана, якщо відповідний gemXX == True.
    """
    gem_size = 50  # Розмір гема (можна змінити)
    margin = 8     # Відступ між гемами
    start_x = int(SCREEN_WIDTH * 0.8)   # Початковий X
    start_y = int(SCREEN_HEIGHT * 0.02)   # Початковий Y (верхня частина екрана)

    for i in range(1, 6):
        for j in range(1, 6):
            attr = f"gem{i}{j}"
            if getattr(player, attr, True):
                texture = player.gem_textures.get(attr)
                if texture:
                    x = start_x + (i - 1) * (gem_size + margin)
                    y = start_y + (j - 1) * (gem_size + margin)
                    screen.blit(pygame.transform.scale(texture, (gem_size, gem_size)), (x, y))

def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("2D Ігровий рушій")
    clock = pygame.time.Clock()

    textures = load_textures()
    level_path = Path("levels/level0.lvl")  # Перетворення рядка на об'єкт Path
    level_data = load_level(level_path, textures)

    player = level_data['player']
    blocks = level_data['blocks']
    enemies = level_data['enemies']
    items = level_data['items']
    npcs = level_data['npcs']
    statues = level_data['statues']
    level_data = level_data['level_data']

    background_grid = generate_background_grid(textures, level_data, level_path.name)

    # Основний цикл
    running = True
    while running:
        clock.tick(60)
        screen.fill((0, 0, 0))

        # Малювання текстури grass1.png на порожніх клітинках
        render_background(screen, background_grid)

        # Малювання інших об'єктів
        for block in blocks:
            block.draw(screen)
        for item in items:
            item.draw(screen)
        for enemy in enemies:
            enemy.draw(screen)
        for npc in npcs:
            npc.draw(screen)
        for statue in statues:
            statue.draw(screen)
        player.draw(screen)

        # Малювання гемів гравця
        draw_player_gems(player, screen)

        # Обробка подій
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Рух гравця
        keys = pygame.key.get_pressed()
        player.handle_input(keys)
        player.update(blocks)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
