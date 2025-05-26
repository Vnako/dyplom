import os
import json
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QHBoxLayout, QMessageBox, QFileDialog
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt

def save_level(level_name, width=None, height=None, folder="levels"):
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, f"{level_name}.lvl")
    level_data = {
        "file_type": "level_json",
        "level_name": level_name,
        "width": width,
        "height": height,
        "content": [" " * width for _ in range(height)] if width and height else []
    }
    with open(filepath, "w") as f:
        json.dump(level_data, f, indent=4)
    return filepath

def load_level(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def open_create_level_window(parent):
    create_window = QWidget()
    create_window.setWindowTitle('Введіть назву рівня')
    create_window.setGeometry(100, 100, 300, 150)
    
    layout = QVBoxLayout()

    level_name_input = QLineEdit()
    level_name_input.setPlaceholderText('Введіть назву рівня')
    layout.addWidget(level_name_input)

    save_button = QPushButton('Зберегти рівень')
    save_button.clicked.connect(lambda: save_new_level(create_window, level_name_input))
    layout.addWidget(save_button)
    
    create_window.setLayout(layout)
    create_window.show()

def save_new_level(create_window, level_name_input):
    level_name = level_name_input.text().strip()
    
    if not level_name:
        show_error(create_window, 'Назва рівня не може бути порожньою!')
        return
    
    level_filename = QFileDialog.getSaveFileName(create_window, 'Зберегти рівень', f'{level_name}.json', 'JSON Files (*.json)')
    
    if level_filename[0]:
        with open(level_filename[0], 'w') as f:
            level_data = {
                "level_name": level_name,
                "width": 0,
                "height": 0,
                "content": []
            }
            json.dump(level_data, f, indent=4)
        
        create_window.close()
        open_edit_level_window(create_window, level_filename[0])  # Відкриваємо вікно редагування рівня

def open_edit_level_window(parent, level_filename, content=""):
    edit_window = QWidget()
    edit_window.setWindowTitle(f'Редагувати рівень: {os.path.basename(level_filename)}')
    edit_window.setGeometry(200, 200, 1000, 1000)
    
    layout = QVBoxLayout()
    
    width_input = QLineEdit()
    width_input.setPlaceholderText('Введіть ширину рівня')
    layout.addWidget(width_input)

    height_input = QLineEdit()
    height_input.setPlaceholderText('Введіть висоту рівня')
    layout.addWidget(height_input)
    
    level_table = QTableWidget()
    layout.addWidget(level_table)

    level_table.horizontalHeader().setDefaultSectionSize(20)
    level_table.verticalHeader().setDefaultSectionSize(20)

    update_table_button = QPushButton('Оновити мапу')
    update_table_button.clicked.connect(lambda: update_level_table(width_input, height_input, level_table))
    layout.addWidget(update_table_button)

    # Додавання кнопок для ворогів, гравця, предметів та інших функцій
    enemy_layout = QHBoxLayout()

    x_input = QLineEdit()
    x_input.setPlaceholderText('Координата X')
    enemy_layout.addWidget(x_input)

    y_input = QLineEdit()
    y_input.setPlaceholderText('Координата Y')
    enemy_layout.addWidget(y_input)

    add_enemy1_button = QPushButton('Ворог 1')
    add_enemy1_button.clicked.connect(lambda: add_enemy(level_table, x_input, y_input, '1'))
    enemy_layout.addWidget(add_enemy1_button)

    add_enemy2_button = QPushButton('Ворог 2')
    add_enemy2_button.clicked.connect(lambda: add_enemy(level_table, x_input, y_input, '2'))
    enemy_layout.addWidget(add_enemy2_button)

    add_enemy3_button = QPushButton('Ворог 3')
    add_enemy3_button.clicked.connect(lambda: add_enemy(level_table, x_input, y_input, '3', single_instance=True))
    enemy_layout.addWidget(add_enemy3_button)

    layout.addLayout(enemy_layout)

    # Додавання кнопок для гравця, предметів, порожнечі та очищення
    utility_layout = QHBoxLayout()

    add_player_button = QPushButton('Гравець (@)')
    add_player_button.clicked.connect(lambda: add_player(level_table, x_input, y_input))
    utility_layout.addWidget(add_player_button)

    add_item_button = QPushButton('Предмет (*)')
    add_item_button.clicked.connect(lambda: add_item(level_table, x_input, y_input))
    utility_layout.addWidget(add_item_button)

    fill_empty_button = QPushButton('Стіна (#)')
    fill_empty_button.clicked.connect(lambda: fill_area(level_table, '#'))
    utility_layout.addWidget(fill_empty_button)

    clear_button = QPushButton('Очистити (.)')
    clear_button.clicked.connect(lambda: fill_area(level_table, ' '))
    utility_layout.addWidget(clear_button)

    layout.addLayout(utility_layout)

    save_edit_button = QPushButton('Зберегти зміни')
    save_edit_button.clicked.connect(lambda: save_edit(edit_window, level_filename, width_input, height_input, level_table))
    layout.addWidget(save_edit_button)
    
    # Завантаження даних з файлу рівня
    with open(level_filename, 'r') as f:
        level_data = json.load(f)
        width_input.setText(str(level_data.get('width', '')))
        height_input.setText(str(level_data.get('height', '')))
        update_level_table(width_input, height_input, level_table)
        for y, row in enumerate(level_data.get('content', [])):
            for x, cell in enumerate(row):
                level_table.setItem(y, x, QTableWidgetItem(cell))

    level_table.cellClicked.connect(lambda row, col: update_inputs_from_table(row, col, x_input, y_input))
    edit_window.setLayout(layout)
    edit_window.show()

def update_inputs_from_table(row, col, x_input, y_input):
    x_input.setText(str(col))
    y_input.setText(str(row))

def add_enemy(level_table, x_input, y_input, enemy_type, single_instance=False):
    try:
        x = int(x_input.text())
        y = int(y_input.text())

        if x < 0 or y < 0:
            raise ValueError('Координати повинні бути додатними числами!')

        if single_instance:
            # Перевірка, чи ворог вже існує, і переміщення його на нову позицію
            for row in range(level_table.rowCount()):
                for col in range(level_table.columnCount()):
                    if level_table.item(row, col) and level_table.item(row, col).text() == enemy_type:
                        level_table.setItem(row, col, QTableWidgetItem(' '))
                        break

        level_table.setItem(y, x, QTableWidgetItem(enemy_type))
    except ValueError as e:
        show_error(level_table, f"Помилка: {e}")

def add_player(level_table, x_input, y_input):
    try:
        x = int(x_input.text())
        y = int(y_input.text())

        if x < 0 or y < 0:
            raise ValueError('Координати повинні бути додатними числами!')

        # Перевірка, чи гравець вже існує, і переміщення його на нову позицію
        for row in range(level_table.rowCount()):
            for col in range(level_table.columnCount()):
                if level_table.item(row, col) and level_table.item(row, col).text() == '@':
                    level_table.setItem(row, col, QTableWidgetItem(' '))
                    break

        level_table.setItem(y, x, QTableWidgetItem('@'))
    except ValueError as e:
        show_error(level_table, f"Помилка: {e}")

def add_item(level_table, x_input, y_input):
    try:
        x = int(x_input.text())
        y = int(y_input.text())

        if x < 0 or y < 0:
            raise ValueError('Координати повинні бути додатними числами!')

        # Перевірка, чи клітинка є порожньою
        if level_table.item(y, x) and level_table.item(y, x).text() == '#':
            raise ValueError('Не можна ставити елементи в області порожнечі (#).')

        level_table.setItem(y, x, QTableWidgetItem('*'))
    except ValueError as e:
        show_error(level_table, f"Помилка: {e}")

def fill_area(level_table, char):
    selected_ranges = level_table.selectedRanges()
    if not selected_ranges:
        show_error(level_table, "Виберіть область для заповнення!")
        return

    already_exists = False
    for selected_range in selected_ranges:
        for row in range(selected_range.topRow(), selected_range.bottomRow() + 1):
            for col in range(selected_range.leftColumn(), selected_range.rightColumn() + 1):
                if char in ('3', '@'):
                    # Перевірка, чи ворог або гравець вже існує
                    if not already_exists:
                        for r in range(level_table.rowCount()):
                            for c in range(level_table.columnCount()):
                                if level_table.item(r, c) and level_table.item(r, c).text() == char:
                                    already_exists = True
                                    break
                            if already_exists:
                                break

                    if already_exists:
                        show_error(level_table, f"На карті може бути лише один елемент типу '{char}'!")
                        return

                level_table.setItem(row, col, QTableWidgetItem(char))

def is_adjacent_to_empty(level_table, row, col):
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # Верх, низ, ліво, право
    for dr, dc in directions:
        r, c = row + dr, col + dc
        if 0 <= r < level_table.rowCount() and 0 <= c < level_table.columnCount():
            if level_table.item(r, c) and level_table.item(r, c).text() == ' ':
                return True
    return False

def update_level_table(width_input, height_input, level_table):
    try:
        width = int(width_input.text())
        height = int(height_input.text())

        if width <= 0 or height <= 0:
            raise ValueError('Розміри повинні бути додатними числами!')

        level_table.setRowCount(height)
        level_table.setColumnCount(width)

        for row in range(height):
            for col in range(width):
                level_table.setItem(row, col, QTableWidgetItem(" "))
    except ValueError as e:
        show_error(level_table, f"Помилка: {e}")

def save_edit(parent, level_filename, width_input, height_input, level_table):
    try:
        width = int(width_input.text())
        height = int(height_input.text())

        if width <= 0 or height <= 0:
            raise ValueError('Розміри повинні бути додатними числами!')

        level_data = {
            "file_type": "level_json",
            "level_name": os.path.splitext(os.path.basename(level_filename))[0],
            "width": width,
            "height": height,
            "content": []
        }

        # Формування контенту рівня з таблиці
        for row in range(height):
            row_data = ""
            for col in range(width):
                item = level_table.item(row, col)
                row_data += item.text() if item and item.text() else " "
            level_data["content"].append(row_data)

        # Збереження рівня у файл
        with open(level_filename, 'w') as f:
            json.dump(level_data, f, indent=4)

        QMessageBox.information(parent, "Збереження", "Рівень успішно збережено!")
    except ValueError as e:
        QMessageBox.critical(parent, "Помилка", f"Помилка: {e}")
    except Exception as e:
        QMessageBox.critical(parent, "Помилка", f"Помилка під час збереження: {e}")

def show_error(parent, message):
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Critical)
    msg.setText(message)
    msg.setWindowTitle('Помилка')
    msg.exec_()

def show_info(parent, message):
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Information)
    msg.setText(message)
    msg.setWindowTitle('Інформація')
    msg.exec_()

def move_existing_element(level_table, char, new_row, new_col):
    """
    Переміщує існуючий елемент (гравця або ворога типу 3) на нову клітинку.

    :param level_table: Таблиця рівня
    :param char: Символ елемента ('@' або '3')
    :param new_row: Новий рядок
    :param new_col: Нова колонка
    """
    for row in range(level_table.rowCount()):
        for col in range(level_table.columnCount()):
            item = level_table.item(row, col)
            if item and item.text() == char:
                # Очищення попередньої клітинки
                item.setText("")
                break
    # Додавання елемента на нову клітинку
    new_item = level_table.item(new_row, new_col)
    if not new_item:
        new_item = QTableWidgetItem()
        level_table.setItem(new_row, new_col, new_item)
    new_item.setText(char)

def fill_with_spaces(level_table):
    """Заповнює всі клітинки таблиці пробілами."""
    for row in range(level_table.rowCount()):
        for col in range(level_table.columnCount()):
            item = level_table.item(row, col)
            if not item:
                item = QTableWidgetItem(" ")
                item.setBackground(QColor("#ebfbff"))  # Світлий фон
                level_table.setItem(row, col, item)
            elif not item.text().strip():
                item.setText(" ")  # Замінюємо порожній текст пробілом

def save_table_to_file(level_table, file_path, width, height, images):
    """Зберігає таблицю у файл із відповідними символами та текстом."""
    level_data = {
        "file_type": "level_json",
        "level_name": os.path.splitext(os.path.basename(file_path))[0],
        "width": width,
        "height": height,
        "content": []
    }

    for row in range(height):
        row_data = ""
        for col in range(width):
            item = level_table.item(row, col)
            if item and item.text().strip():
                row_data += item.text().strip()  # Зчитуємо текст клітинки
                print(f"Текст '{item.text().strip()}' збережено на позиції ({row}, {col})")
            else:
                row_data += " "  # Якщо клітинка порожня, додаємо пробіл
                print(f"Порожня клітинка на позиції ({row}, {col})")
        level_data["content"].append(row_data)

    # Збереження у файл
    with open(file_path, 'w') as f:
        json.dump(level_data, f, indent=4)


