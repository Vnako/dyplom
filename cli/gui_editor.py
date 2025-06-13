import sys
import json
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHBoxLayout, QMenuBar, QAction, QFileDialog, QMessageBox, QLineEdit, QPushButton, QInputDialog, QMenu, QLabel, QShortcut
from PyQt5.QtGui import QColor, QFont, QIcon, QPixmap, QPainter, QKeySequence
from PyQt5.QtCore import Qt, QSize, QTimer, QUrl
from PyQt5.QtGui import QDesktopServices
from editor_logic import save_edit, fill_with_spaces, save_table_to_file

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "cli_assets"

class LevelEditorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Редактор рівнів Slime Quest: Dungeon')
        self.current_file_path = None
        self.is_modified = False

        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        window_size = screen_geometry.height()
        self.resize(window_size, window_size)

        self.layout = QVBoxLayout()

        # Встановлення шрифту Nimbus Mono PS для всього вікна
        app.setFont(QFont("Nimbus Mono PS", 12))

        # Ініціалізація теми за замовчуванням
        self.current_theme = "light"

        # Додавання головного меню
        self.menu_bar = QMenuBar(self)
        self.init_menu()
        self.layout.setMenuBar(self.menu_bar)

        # Встановлення ідентифікатора для кореневого віджета
        self.setObjectName("root")

        # Додавання QLabel для фонового зображення
        self.background_label = QLabel(self)
        self.background_label.setScaledContents(True)  # Дозволяє масштабування зображення

        background_path = ASSETS_DIR / 'background_light.png'
        if not background_path.exists():
            print(f"Файл {background_path} не знайдено! Використовується білий фон.")
            self.background_label.setStyleSheet("background-color: white;")
        else:
            try:
                pixmap = QPixmap(str(background_path))
                if pixmap.isNull():
                    raise ValueError("Не вдалося завантажити зображення.")
                print(f"Файл {background_path} успішно завантажено.")
                self.background_label.setPixmap(pixmap)
            except Exception as e:
                print(f"Помилка при завантаженні зображення {background_path}: {e}")
                self.background_label.setStyleSheet("background-color: white;")

        self.background_label.lower()  # Переміщуємо фон на задній план

        # Поля для ширини та висоти в одному рядку
        size_layout = QHBoxLayout()
        self.width_input = QLineEdit()
        self.width_input.setPlaceholderText('Ширина')
        self.width_input.setStyleSheet("background: #ebfbff")  # Прозорий фон
        self.width_input.returnPressed.connect(self.focus_height_input)  # Переходить до висоти
        size_layout.addWidget(self.width_input)

        self.height_input = QLineEdit()
        self.height_input.setPlaceholderText('Висота')
        self.height_input.setStyleSheet("background: #ebfbff")  # Прозорий фон
        self.height_input.returnPressed.connect(self.update_level_table)  # Оновлює таблицю
        size_layout.addWidget(self.height_input)

        self.layout.addLayout(size_layout)

        # Встановлення теми після створення QLineEdit
        self.set_theme(self.current_theme)

        # Таблиця рівня
        self.level_table = QTableWidget()
        self.level_table.horizontalHeader().setDefaultSectionSize(32)  # Розмір клітинок
        self.level_table.verticalHeader().setDefaultSectionSize(32)
        # Забороняємо зміну розміру рядків та стовпців вручну
        self.level_table.horizontalHeader().setSectionResizeMode(QTableWidget.horizontalHeader(self.level_table).Fixed)
        self.level_table.verticalHeader().setSectionResizeMode(QTableWidget.verticalHeader(self.level_table).Fixed)
        self.level_table.setStyleSheet("""
            QTableWidget {
                background: transparent;  /* Прозорий фон */
                border: 1px solid black;  /* Чорні кордони */
            }
            QTableWidget::item {
                padding: 0px;
                margin: 0px;
            }
        """)  # Встановлення стилів для таблиці
        self.level_table.setEditTriggers(QTableWidget.NoEditTriggers)  # Забороняє редагування таблиці
        self.layout.addWidget(self.level_table)

        # Додатковий відладковий код
        print("Фон встановлено через QFrame")

        # Завантаження зображень для умовних позначок
        self.images = {
            '*': QPixmap(str(ASSETS_DIR / "icon_item.png")),
            '@': QPixmap(str(ASSETS_DIR / "icon_mc.png")),
            '1': QPixmap(str(ASSETS_DIR / "icon_zombie.png")),
            '2': QPixmap(str(ASSETS_DIR / "icon_skeleton.png")),
            '3': QPixmap(str(ASSETS_DIR / "icon_boss.png")),
            '#': QPixmap(str(ASSETS_DIR / "icon_wall.png"))
        }

        # Кнопки для ворогів, гравця, предметів, порожнечі та очищення
        utility_layout = QHBoxLayout()

        self.add_enemy1_button = self.create_image_button('Ворог 1', '1')
        self.add_enemy1_button.setShortcut("1")
        utility_layout.addWidget(self.add_enemy1_button)

        self.add_enemy2_button = self.create_image_button('Ворог 2', '2')
        self.add_enemy2_button.setShortcut("2")
        utility_layout.addWidget(self.add_enemy2_button)

        self.add_enemy3_button = self.create_image_button('Ворог 3', '3')
        self.add_enemy3_button.setShortcut("3")
        utility_layout.addWidget(self.add_enemy3_button)

        self.add_player_button = self.create_image_button('Гравець', '@')
        self.add_player_button.setShortcut("4")
        utility_layout.addWidget(self.add_player_button)

        self.add_item_button = self.create_image_button('Предмет', '*')
        self.add_item_button.setShortcut("5")
        utility_layout.addWidget(self.add_item_button)

        self.fill_empty_button = self.create_image_button('Стіна', '#', center_text=True)
        self.fill_empty_button.setShortcut("6")
        utility_layout.addWidget(self.fill_empty_button)

        self.clear_button = self.create_image_button('Очистити все', '.', center_text=True)
        self.clear_button.clicked.disconnect()  # Remove previous connection if any
        self.clear_button.clicked.connect(self.clear_all_cells)
        utility_layout.addWidget(self.clear_button)

        self.layout.addLayout(utility_layout)

        self.setLayout(self.layout)

        # Додавання обробки подій для збільшення/зменшення масштабу
        self.scale_factor = 1.0  # Початковий масштаб

        # Enable custom context menu for the table
        self.level_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.level_table.customContextMenuRequested.connect(self.show_context_menu)

        # Наприклад, для кнопки "Очистити все"
        QShortcut(QKeySequence("Ctrl+Del"), self, activated=self.clear_all_cells)
        QShortcut(QKeySequence("Ctrl+Backspace"), self, activated=self.clear_all_cells)

        # Додаємо гарячу клавішу Backspace для очищення виділеної області
        QShortcut(QKeySequence("Backspace"), self.level_table, activated=self.clear_selected_cells)

        # Додаємо гарячу клавішу Ctrl+A для виділення всіх клітинок
        QShortcut(QKeySequence("Ctrl+A"), self.level_table, activated=self.select_all_cells)
        # Додаємо гарячу клавішу Ctrl+C для копіювання виділених клітинок
        QShortcut(QKeySequence("Ctrl+C"), self.level_table, activated=self.copy_selected_cells)
        # Додаємо гарячу клавішу Ctrl+V для вставлення клітинок
        QShortcut(QKeySequence("Ctrl+V"), self.level_table, activated=self.paste_cells)
        # Додаємо гарячу клавішу Ctrl+X для вирізання виділених клітинок
        QShortcut(QKeySequence("Ctrl+X"), self.level_table, activated=self.cut_selected_cells)

    def init_menu(self):
        # Меню "Файл"
        file_menu = self.menu_bar.addMenu("Файл")
        new_action = QAction("Новий файл", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_level)
        file_menu.addAction(new_action)

        open_action = QAction("Відкрити", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_level)
        file_menu.addAction(open_action)

        save_action = QAction("Зберегти", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_level)
        file_menu.addAction(save_action)

        save_as_action = QAction("Зберегти як", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_level_as)
        file_menu.addAction(save_as_action)

        exit_action = QAction("Вийти", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Меню "Вигляд"
        view_menu = self.menu_bar.addMenu("Вигляд")
        self.light_theme_action = QAction("Світла тема", self, checkable=True)
        self.light_theme_action.triggered.connect(lambda: self.set_theme("light"))
        view_menu.addAction(self.light_theme_action)

        self.dark_theme_action = QAction("Темна тема", self, checkable=True)
        self.dark_theme_action.triggered.connect(lambda: self.set_theme("dark"))
        view_menu.addAction(self.dark_theme_action)

        font_size_action = QAction("Розмір шрифту", self)
        font_size_action.triggered.connect(self.change_font_size)
        view_menu.addAction(font_size_action)

        zoom_in_action = QAction("Збільшити", self)
        zoom_in_action.setShortcut("Ctrl+WheelUp")
        zoom_in_action.setShortcut(QKeySequence("Ctrl++"))
        zoom_in_action.triggered.connect(self.zoom_in)
        view_menu.addAction(zoom_in_action)

        zoom_out_action = QAction("Зменшити", self)
        zoom_out_action.setShortcut("Ctrl+WheelDown")
        zoom_out_action.setShortcut(QKeySequence("Ctrl+-"))
        zoom_out_action.triggered.connect(self.zoom_out)
        view_menu.addAction(zoom_out_action)

        # Меню "Довідка"
        help_menu = self.menu_bar.addMenu("Довідка")
        about_action = QAction("Про програму", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        inst1 = QAction("Інструкція розробника", self)
        inst1.triggered.connect(self.open_instruction1_html)
        help_menu.addAction(inst1)
        
        inst2 = QAction("Інструкція користувача", self)
        inst2.triggered.connect(self.open_instruction2_html)
        help_menu.addAction(inst2)

        # Оновлення стану пташок для тем після створення атрибутів
        self.update_theme_checkmarks()

    def create_image_button(self, text, char, center_text=False):
        button = QPushButton()
        button.setStyleSheet("border: none; background-color: transparent;")  # Приховуємо межі кнопки

        # Завантаження основного зображення кнопки
        pixmap = QPixmap(str(ASSETS_DIR / "button.png"))
        if pixmap.isNull():
            QMessageBox.critical(self, "Помилка", f"Не вдалося завантажити зображення: cli_assets/button.png")
            return button

        pixmap = pixmap.scaled(150, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        painter = QPainter(pixmap)
        painter.setFont(QFont("Nimbus Mono PS", 12))
        painter.setPen(Qt.white)

        # Додавання тексту
        if center_text:
            painter.drawText(pixmap.rect(), Qt.AlignCenter, text)
        else:
            painter.drawText(pixmap.rect().adjusted(10, 0, -40, 0), Qt.AlignLeft | Qt.AlignVCenter, text)

        # Додавання іконки, якщо символ присутній у `self.images` і це не '#'
        if char in self.images and char != '#':
            icon_pixmap = self.images[char].scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            painter.drawPixmap(pixmap.width() - 40, (pixmap.height() - 32) // 2, icon_pixmap)

        painter.end()

        # Встановлення іконки на кнопку
        button.setIcon(QIcon(pixmap))
        button.setIconSize(QSize(150, 40))
        button.clicked.connect(lambda: self.handle_button_click(char))
        return button

    def handle_button_click(self, char):
        self.add_element(char)  # Спочатку додаємо елемент
        self.level_table.clearSelection()  # Потім знімаємо виділення з таблиці

    def change_font_size(self):
        size, ok = QInputDialog.getInt(self, "Розмір шрифту", "Введіть розмір шрифту:", 12, 8, 48)
        if ok:
            self.level_table.setFont(QFont("Nimbus Mono PS", size))
            self.level_table.horizontalHeader().setDefaultSectionSize(size * 2 + 4)  # Ширина трохи більша за висоту
            self.level_table.verticalHeader().setDefaultSectionSize(size * 2)

    def new_level(self):
        try:
            file_path, _ = QFileDialog.getSaveFileName(self, "Створити новий файл", str(Path("levels")), "Level Files (*.lvl)")
            if file_path:
                file_path = Path(file_path)
                # Переконуємося, що файл має розширення .lvl
                if file_path.suffix != ".lvl":
                    file_path = file_path.with_suffix(".lvl")

                # Поля розміру залишаємо порожніми, таблицю очищаємо
                level_data = {
                    "file_type": "level_json",
                    "level_name": file_path.stem,
                    "width": "",
                    "height": "",
                    "content": []
                }

                with file_path.open('w') as f:
                    json.dump(level_data, f, indent=4)

                self.current_file_path = file_path
                self.width_input.setText("")
                self.height_input.setText("")
                self.level_table.setRowCount(0)
                self.level_table.setColumnCount(0)
                self.setWindowTitle(f"Редактор рівнів Slime Quest: Dungeon ({file_path.name})")
                self.is_modified = False
                self.width_input.setFocus()  # Робимо активним перше поле для вводу
                QMessageBox.information(self, "Успіх", "Новий файл успішно створено!")
        except Exception as e:
            QMessageBox.critical(self, "Помилка", f"Не вдалося створити новий файл: {e}")

    def open_level(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Виберіть файл рівня", str(Path("levels")), "Level Files (*.lvl)")
        if not file_path or not Path(file_path).is_file():
            return  # Користувач натиснув "Відміна" або не вибрав файл, або вийшов з папки
        file_path = Path(file_path)
        try:
            with file_path.open('r') as f:
                level_data = json.load(f)
                if level_data.get("file_type") != "level_json":
                    raise ValueError("Неправильний формат файлу!")

                self.width_input.setText(str(level_data.get("width", "")))
                self.height_input.setText(str(level_data.get("height", "")))
                self.update_level_table()

                for y, row in enumerate(level_data.get("content", [])):
                    for x, cell in enumerate(row):
                        item = QTableWidgetItem()
                        if cell in self.images:
                            item.setIcon(QIcon(self.images[cell].scaled(30, 30, Qt.KeepAspectRatio)))
                            item.setText(cell)
                            item.setForeground(QColor("#ebfbff"))
                        else:
                            item.setText(cell)
                        item.setBackground(QColor("#ebfbff"))
                        self.level_table.setItem(y, x, item)

                self.current_file_path = file_path
                self.setWindowTitle(f"Редактор рівнів для гри Slime Quest: Dungeon ({file_path.name})")
        except Exception as e:
            QMessageBox.critical(self, "Помилка", f"Не вдалося завантажити рівень: {e}")

    def save_level(self):
        if self.current_file_path:
            try:
                width = int(self.width_input.text())
                height = int(self.height_input.text())

                if width <= 0 or height <= 0:
                    raise ValueError("Ширина та висота повинні бути додатними числами!")

                save_table_to_file(self.level_table, self.current_file_path, width, height, self.images)
                self.is_modified = False  # Скидає статус змін після збереження
                self.setWindowTitle(self.windowTitle().lstrip("*"))  # Видаляє зірочку з заголовка
                QMessageBox.information(self, "Успіх", "Рівень успішно збережено!")
            except Exception as e:
                QMessageBox.critical(self, "Помилка", f"Не вдалося зберегти рівень: {e}")
        else:
            self.save_level_as()

    def save_level_as(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Зберегти рівень як", str(Path("levels")), "Level Files (*.lvl)")
        if file_path:
            file_path = Path(file_path)
            # Переконуємося, що файл має розширення .lvl
            if file_path.suffix != ".lvl":
                file_path = file_path.with_suffix(".lvl")
            try:
                self.current_file_path = file_path
                save_edit(self, str(file_path), self.width_input, self.height_input, self.level_table)
                self.is_modified = False  # Скидає статус змін після збереження
                self.setWindowTitle(self.windowTitle().lstrip("*"))  # Видаляє зірочку з заголовка
            except Exception as e:
                QMessageBox.critical(self, "Помилка", f"Не вдалося зберегти рівень: {e}")

    def update_level_table(self):
        try:
            width = int(self.width_input.text())
            height = int(self.height_input.text())

            if width <= 0 or height <= 0:
                raise ValueError('Ширина та висота повинні бути додатними числами!')

            self.level_table.setRowCount(height)
            self.level_table.setColumnCount(width)

            # Заповнення таблиці пробілами
            fill_with_spaces(self.level_table)
            self.mark_as_modified()  # Позначає файл як змінений після оновлення таблиці
        except ValueError as e:
            QMessageBox.critical(self, "Помилка", str(e))

    def add_element(self, char):
        selected_ranges = self.level_table.selectedRanges()
        if not selected_ranges:
            QMessageBox.warning(self, "Попередження", "Виберіть область для додавання!")
            return

        # Для '@' та '3' переміщуємо, якщо вже існує
        if char in ('@', '3'):
            found = None
            for row in range(self.level_table.rowCount()):
                for col in range(self.level_table.columnCount()):
                    item = self.level_table.item(row, col)
                    if item and item.text() == char:
                        found = (row, col)
                        break
                if found:
                    break

            # Додаємо тільки в першу виділену клітинку
            first_range = selected_ranges[0]
            target_row = first_range.topRow()
            target_col = first_range.leftColumn()

            if found:
                # Якщо вже на цій клітинці — нічого не робимо
                if found == (target_row, target_col):
                    return
                # Очищаємо попередню клітинку
                prev_item = self.level_table.item(found[0], found[1])
                if prev_item:
                    prev_item.setIcon(QIcon())
                    prev_item.setText(" ")
                    prev_item.setBackground(QColor("#ebfbff"))

            # Додаємо на нову клітинку
            item = self.level_table.item(target_row, target_col)
            if not item:
                item = QTableWidgetItem()
                self.level_table.setItem(target_row, target_col, item)
            if char in self.images:
                item.setIcon(QIcon(self.images[char].scaled(30, 30, Qt.KeepAspectRatio)))
                item.setText(char)
                item.setForeground(QColor("#ebfbff"))
                item.setBackground(QColor("#ebfbff"))
            else:
                item.setText(char)
                item.setTextAlignment(Qt.AlignCenter)
                item.setBackground(QColor("#ebfbff"))
            self.mark_as_modified()
            return
        
        for selected_range in selected_ranges:
            for row in range(selected_range.topRow(), selected_range.bottomRow() + 1):
                for col in range(selected_range.leftColumn(), selected_range.rightColumn() + 1):
                    item = self.level_table.item(row, col)
                    if not item:
                        item = QTableWidgetItem()
                        self.level_table.setItem(row, col, item)

                    if char == '.':
                        # Очищуємо клітинку
                        item.setIcon(QIcon())
                        item.setText(" ")  # Зберігаємо пробіл як текст
                        item.setBackground(QColor("#ebfbff"))
                    elif char in self.images:
                        # Додаємо іконку та умовну позначку
                        item.setIcon(QIcon(self.images[char].scaled(30, 30, Qt.KeepAspectRatio)))
                        item.setText(char)  # Зберігаємо умовну позначку в тексті
                        item.setForeground(QColor("#ebfbff"))  # Змінюємо колір тексту
                        item.setBackground(QColor("#ebfbff"))
                    else:
                        # Додаємо текст, якщо це не іконка
                        item.setText(char)
                        item.setTextAlignment(Qt.AlignCenter)
                        item.setBackground(QColor("#ebfbff"))
        self.mark_as_modified()

    def move_existing_element(self, char, new_row, new_col):
        """Переміщує існуючий елемент (гравця або ворога типу 3) на нову клітинку."""
        for row in range(self.level_table.rowCount()):
            for col in range(self.level_table.columnCount()):
                item = self.level_table.item(row, col)
                if item and item.icon() and char in self.images:
                    pixmap = self.images[char].scaled(30, 30, Qt.KeepAspectRatio)
                    if item.icon().pixmap(30, 30).toImage() == pixmap.toImage():
                        # Очищення попередньої клітинки
                        item.setIcon(QIcon())
                        item.setText("")
                        item.setBackground(QColor("#ebfbff"))
                        break
                elif item and item.text() == char:
                    # Очищення попередньої клітинки
                    item.setText("")
                    item.setBackground(QColor("#ebfbff"))
                    break
        # Додавання елемента на нову клітинку
        new_item = self.level_table.item(new_row, new_col)
        if not new_item:
            new_item = QTableWidgetItem()
            self.level_table.setItem(new_row, new_col, new_item)
        new_item.setIcon(QIcon(self.images[char].scaled(30, 30, Qt.KeepAspectRatio)))
        new_item.setText("")
        new_item.setBackground(QColor("#ebfbff"))

    def find_existing_element(self, char):
        """Перевіряє, чи існує на карті елемент із заданим символом."""
        for row in range(self.level_table.rowCount()):
            for col in range(self.level_table.columnCount()):
                item = self.level_table.item(row, col)
                if item and item.icon() and char in self.images:
                    pixmap = self.images[char].scaled(30, 30, Qt.KeepAspectRatio)
                    if item.icon().pixmap(30, 30).toImage() == pixmap.toImage():
                        return True
                elif item and item.text() == char:
                    return True
        return False

    def zoom_in(self):
        self.scale_factor += 0.1
        self.update_table_scale()

    def zoom_out(self):
        self.scale_factor = max(0.1, self.scale_factor - 0.1)
        self.update_table_scale()

    def update_table_scale(self):
        new_size = int(32 * self.scale_factor)
        # Дозволяємо змінювати розмір лише програмно (Ctrl+Wheel або гарячі клавіші)
        self.level_table.horizontalHeader().setSectionResizeMode(QTableWidget.horizontalHeader(self.level_table).Fixed)
        self.level_table.verticalHeader().setSectionResizeMode(QTableWidget.verticalHeader(self.level_table).Fixed)
        self.level_table.horizontalHeader().setDefaultSectionSize(new_size)
        self.level_table.verticalHeader().setDefaultSectionSize(new_size)

    def set_theme(self, theme):
        self.current_theme = theme
        if theme == "light":
            self.setStyleSheet("background-color: #ebfbff; color: black;")
            line_edit_style = "background-color: #ebfbff; color: black; border: 1px solid #ccc;"
            background_path = ASSETS_DIR / 'background_light.png'
        elif theme == "dark":
            self.setStyleSheet("background-color: #080D21; color: white;")
            line_edit_style = "background-color: #080D21; color: white; border: 1px solid #555;"
            background_path = ASSETS_DIR / 'background_dark.png'

        # Оновлення стилю для QLineEdit
        self.width_input.setStyleSheet(line_edit_style)
        self.height_input.setStyleSheet(line_edit_style)

        # Оновлення фонового зображення
        if background_path.exists():
            pixmap = QPixmap(str(background_path))
            if not pixmap.isNull():
                self.background_label.setPixmap(pixmap)
            else:
                print(f"Не вдалося завантажити зображення: {background_path}")
                self.background_label.setStyleSheet("background-color: white;")
        else:
            print(f"Файл {background_path} не знайдено! Використовується білий фон.")
            self.background_label.setStyleSheet("background-color: white;")

        self.update_theme_checkmarks()

    def update_theme_checkmarks(self):
        self.light_theme_action.setChecked(self.current_theme == "light")
        self.dark_theme_action.setChecked(self.current_theme == "dark")

    def show_about(self):
        QMessageBox.information(
            self,
            "Про програму",
            "Це редактор рівнів для гри Slime Quest: Dungeon.\n"
            "Версія 1.1.\n"
            "Дипломний проект виконала Коломоєць Вероніка з групи 123-21-1.\n"
            "За всіма питаннями звератись на пошту: veroniqe.kol.556@gmail.com"
        )

    def focus_height_input(self):
        self.height_input.setFocus()  # Переходить до поля висоти

    def closeEvent(self, event):
        """Перевіряє, чи потрібно зберегти зміни перед закриттям."""
        if self.is_modified:
            reply = QMessageBox.question(
                self,
                "Зберегти зміни",
                "Файл було змінено. Бажаєте зберегти перед виходом?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.Cancel
            )
            if reply == QMessageBox.Yes:
                self.save_level()
                event.accept()
            elif reply == QMessageBox.No:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def mark_as_modified(self):
        """Позначає файл як змінений, додаючи одну зірочку до назви вікна."""
        if not self.is_modified:
            self.is_modified = True
            if not self.windowTitle().startswith("*"):
                self.setWindowTitle(f"*{self.windowTitle()}")  # Додає зірочку до заголовка

    def wheelEvent(self, event):
        """Обробляє подію колеса миші для масштабування."""
        if QApplication.keyboardModifiers() == Qt.ControlModifier:
            if event.angleDelta().y() > 0:  # Прокрутка вгору
                self.zoom_in()
            elif event.angleDelta().y() < 0:  # Прокрутка вниз
                self.zoom_out()
        else:
            super().wheelEvent(event)  # Передаємо подію далі, якщо Ctrl не натиснуто

    def show_context_menu(self, position):  
        """Відображає контекстне меню для таблиці."""
        menu = QMenu(self)

        # Додати дії до контекстного меню
        paste_cells_action = menu.addAction("Вставити")
        paste_cells_action.triggered.connect(self.paste_cells)
        
        copy_selected_cells_action = menu.addAction("Копіювати")
        copy_selected_cells_action.triggered.connect(self.copy_selected_cells)
        
        cut_selected_cells_action = menu.addAction("Вирізати")
        cut_selected_cells_action.triggered.connect(self.cut_selected_cells)
        
        select_all_cells_action = menu.addAction("Виділити все")
        select_all_cells_action.triggered.connect(self.select_all_cells)

        # Група "Додати"
        add_menu = menu.addMenu("Додати")

        # Підгрупа "Додати ворога"
        add_enemy_menu = add_menu.addMenu("Ворог")
        add_enemy_action = QAction("Зомбі", self)
        add_enemy_action.triggered.connect(lambda: self.add_element('1'))  
        add_enemy_menu.addAction(add_enemy_action)
        
        add_enemy_action = QAction("Скелет", self)
        add_enemy_action.triggered.connect(lambda: self.add_element('2'))  
        add_enemy_menu.addAction(add_enemy_action)
        
        add_enemy_action = QAction("Бос", self)
        add_enemy_action.triggered.connect(lambda: self.add_element('3'))  
        add_enemy_menu.addAction(add_enemy_action)

        # Інші додавання
        add_player_action = QAction("Гравець", self)
        add_player_action.triggered.connect(lambda: self.add_element('@'))
        add_menu.addAction(add_player_action)
        
        add_item_action = QAction("Скриня", self)
        add_item_action.triggered.connect(lambda: self.add_element('*'))
        add_menu.addAction(add_item_action)
        
        add_wall_action = QAction("Стіна", self)
        add_wall_action.triggered.connect(lambda: self.add_element('#'))
        add_menu.addAction(add_wall_action)

        clear_cell_action = QAction("Очистити", self)
        clear_cell_action.triggered.connect(lambda: self.add_element('.'))
        menu.addAction(clear_cell_action)

        # Відобразити меню в позиції курсора
        menu.exec_(self.level_table.viewport().mapToGlobal(position))

    def resizeEvent(self, event):
        """Оновлює розмір фонового зображення при зміні розміру вікна."""
        self.background_label.setGeometry(self.rect())  # Оновлюємо розмір QLabel
        super().resizeEvent(event)

    def clear_all_cells(self):
        """Очищає всі клітинки таблиці (ставить пробіл, фон, прибирає іконки)."""
        for row in range(self.level_table.rowCount()):
            for col in range(self.level_table.columnCount()):
                item = self.level_table.item(row, col)
                if not item:
                    item = QTableWidgetItem()
                    self.level_table.setItem(row, col, item)
                item.setIcon(QIcon())
                item.setText(" ")
                item.setBackground(QColor("#ebfbff"))
        self.mark_as_modified()

    def clear_selected_cells(self):
        """Очищає всі виділені клітинки таблиці (ставить пробіл, фон, прибирає іконки)."""
        selected_ranges = self.level_table.selectedRanges()
        for selected_range in selected_ranges:
            for row in range(selected_range.topRow(), selected_range.bottomRow() + 1):
                for col in range(selected_range.leftColumn(), selected_range.rightColumn() + 1):
                    item = self.level_table.item(row, col)
                    if not item:
                        item = QTableWidgetItem()
                        self.level_table.setItem(row, col, item)
                    item.setIcon(QIcon())
                    item.setText(" ")
                    item.setBackground(QColor("#ebfbff"))
        self.mark_as_modified()

    def open_instruction1_html(self):
        instruction_path = BASE_DIR / "instruction1.html"
        if instruction_path.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(instruction_path.resolve())))
        else:
            QMessageBox.warning(self, "Файл не знайдено", f"Файл {instruction_path} не знайдено.")
            
    def open_instruction2_html(self):
        instruction_path = BASE_DIR / "instruction2.html"
        if instruction_path.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(instruction_path.resolve())))
        else:
            QMessageBox.warning(self, "Файл не знайдено", f"Файл {instruction_path} не знайдено.")

    def select_all_cells(self):
        """Виділяє всі клітинки таблиці."""
        self.level_table.selectAll()

    def copy_selected_cells(self):
        """Копіює виділені клітинки у буфер обміну у вигляді тексту."""
        selected_ranges = self.level_table.selectedRanges()
        if not selected_ranges:
            return
        copied = []
        for selected_range in selected_ranges:
            for row in range(selected_range.topRow(), selected_range.bottomRow() + 1):
                row_data = []
                for col in range(selected_range.leftColumn(), selected_range.rightColumn() + 1):
                    item = self.level_table.item(row, col)
                    row_data.append(item.text() if item else " ")
                copied.append("\t".join(row_data))
        clipboard = QApplication.clipboard()
        clipboard.setText("\n".join(copied))

    def paste_cells(self):
        """Вставляє дані з буфера обміну у виділену область."""
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if not text:
            return
        rows = text.splitlines()
        selected_ranges = self.level_table.selectedRanges()
        if not selected_ranges:
            return
        start_row = selected_ranges[0].topRow()
        start_col = selected_ranges[0].leftColumn()
        for i, row_data in enumerate(rows):
            cols = row_data.split("\t")
            for j, value in enumerate(cols):
                r = start_row + i
                c = start_col + j
                if r < self.level_table.rowCount() and c < self.level_table.columnCount():
                    item = self.level_table.item(r, c)
                    if not item:
                        item = QTableWidgetItem()
                        self.level_table.setItem(r, c, item)
                    # Якщо символ є іконкою, додаємо іконку
                    if value in self.images:
                        item.setIcon(QIcon(self.images[value].scaled(30, 30, Qt.KeepAspectRatio)))
                        item.setText(value)
                        item.setForeground(QColor("#ebfbff"))
                        item.setBackground(QColor("#ebfbff"))
                    else:
                        item.setIcon(QIcon())
                        item.setText(value)
                        item.setBackground(QColor("#ebfbff"))
        self.mark_as_modified()

    def cut_selected_cells(self):
        """Вирізає виділені клітинки (копіює та очищає їх)."""
        self.copy_selected_cells()
        self.clear_selected_cells()

def fill_with_hash(level_table, images):
    """Заповнює всі виділені клітинки таблиці символом #, іконкою icon_wall.png та фоном #080D21."""
    selected_ranges = level_table.selectedRanges()
    for selected_range in selected_ranges:
        for row in range(selected_range.topRow(), selected_range.bottomRow() + 1):
            for col in range(selected_range.leftColumn(), selected_range.rightColumn() + 1):
                item = level_table.item(row, col)
                if not item:
                    item = QTableWidgetItem()
                    level_table.setItem(row, col, item)
                item.setText("")  # Очищуємо текст
                item.setBackground(QColor("#080D21"))  # Встановлюємо темний фон
                if '#' in images:
                    item.setIcon(QIcon(images['#'].scaled(30, 30, Qt.KeepAspectRatio)))  # Додаємо іконку

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = LevelEditorApp()
    window.show()
    # Центрування після show() і після всіх layout-ів
    def center_window():
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        x = (screen_geometry.width() - window.frameGeometry().width()) // 2
        y = (screen_geometry.height() - window.frameGeometry().height()) // 2
        window.move(x, y)
    QTimer.singleShot(0, center_window)
    sys.exit(app.exec_())