import json
def parse_level_file(file_path):
    """
    Парсить файл рівня та повертає дані у вигляді словника.

    :param file_path: Шлях до файлу рівня
    :return: Словник з даними рівня
    """
    level_data = {
        'player_start': None,
        'blocks': [],
        'enemies': [],
        'items': [],
        'npc': [],  # Ініціалізація ключа 'npc'
        'width': 0,  # Додано для зберігання ширини рівня
        'height': 0,  # Додано для зберігання висоти рівня
        'statues': []  # Додано: список для статуй
    }

    with open(file_path, 'r') as f:
        data = json.load(f)

    # Зчитування розмірів рівня
    level_data['width'] = data.get('width', 0)
    level_data['height'] = data.get('height', 0)

    # Зчитування вмісту рівня
    for y, line in enumerate(data.get('content', [])):
        for x, char in enumerate(line):
            if char == '@':
                level_data['player_start'] = (x, y)
            elif char == '#':
                level_data['blocks'].append({'x': x, 'y': y, 'is_solid': True})
            elif char == '.':
                level_data['blocks'].append({'x': x, 'y': y, 'is_solid': False})
            elif char in ('1', '2', '3'):
                level_data['enemies'].append({'x': x, 'y': y, 'type': char})
            elif char == '*':
                level_data['items'].append({'x': x, 'y': y, 'is_solid': True}) 
            elif char in ('t', 'e'):
                level_data['npc'].append({'x': x, 'y': y, 'type': char})
            elif char in ('4', '5', '6', '7', '8'):
                level_data['statues'].append({'x': x, 'y': y, 'type': char, 'is_solid': True})  # Додано: обробка статуй
    return level_data