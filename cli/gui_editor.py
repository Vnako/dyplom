import sys
import json
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHBoxLayout, QMenuBar, QAction, QFileDialog, QMessageBox, QLineEdit, QPushButton, QInputDialog, QMenu, QFrame, QLabel
from PyQt5.QtGui import QColor, QFont, QIcon, QPixmap, QPainter, QBrush
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QDesktopWidget
from editor_logic import load_level, save_edit, update_level_table, fill_with_spaces, save_table_to_file

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "cli_assets"

class LevelEditorApp(QWidget):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle('Редактор рівнів')
        self.current_file_path = None  # Додано для зберігання шляху до файлу
        self.is_modified = False  # Додано для відстеження змін

        # Встановлення вікна на максимальну висоту екрану
        screen_geometry = QDesktopWidget().availableGeometry()
        self.setGeometry(100, 100, 1000, screen_geometry.height())

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
        #self.level_table.setEditTriggers(QTableWidget.NoEditTriggers)  # Забороняє редагування таблиці
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

        self.clear_button = self.create_image_button('Очистити', '.', center_text=True)
        self.clear_button.setShortcut("Backspace")
        utility_layout.addWidget(self.clear_button)

        self.layout.addLayout(utility_layout)

        self.setLayout(self.layout)

        # Додавання обробки подій для збільшення/зменшення масштабу
        self.scale_factor = 1.0  # Початковий масштаб

        # Enable custom context menu for the table
        self.level_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.level_table.customContextMenuRequested.connect(self.show_context_menu)

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
        zoom_in_action.triggered.connect(self.zoom_in)
        view_menu.addAction(zoom_in_action)

        zoom_out_action = QAction("Зменшити", self)
        zoom_out_action.setShortcut("Ctrl+WheelDown")
        zoom_out_action.triggered.connect(self.zoom_out)
        view_menu.addAction(zoom_out_action)

        # Меню "Довідка"
        help_menu = self.menu_bar.addMenu("Довідка")
        about_action = QAction("Про програму", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        # Оновлення стану пташок для тем після створення атрибутів
        self.update_theme_checkmarks()

    def create_image_button(self, text, char, center_text=False):
        button = QPushButton()
        button.setStyleSheet("border: none; background-color: transparent;")  # Приховуємо межі кнопки

        # Завантаження основного зображення кнопки
        pixmap = QPixmap("cli_assets/button_sm.png")
        if pixmap.isNull():
            QMessageBox.critical(self, "Помилка", f"Не вдалося завантажити зображення: cli_assets/button_sm.png")
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

                width = 10
                height = 10

                # Створення нового рівня
                level_data = {
                    "file_type": "level_json",
                    "level_name": file_path.stem,
                    "width": width,
                    "height": height,
                    "content": [" " * width for _ in range(height)]  # Заповнення пробілами
                }

                with file_path.open('w') as f:
                    json.dump(level_data, f, indent=4)

                self.current_file_path = file_path
                self.setWindowTitle(f"Редактор рівнів ({file_path.name})")
                self.update_level_table()
                QMessageBox.information(self, "Успіх", "Новий файл успішно створено!")
        except Exception as e:
            QMessageBox.critical(self, "Помилка", f"Не вдалося створити новий файл: {e}")

    def open_level(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Виберіть файл рівня", str(Path("levels")), "Level Files (*.lvl)")
        if file_path:
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
                                # Якщо символ відповідає іконці, додаємо іконку
                                item.setIcon(QIcon(self.images[cell].scaled(30, 30, Qt.KeepAspectRatio)))
                                item.setText("")  # Очищуємо текст
                            else:
                                # Якщо символ не відповідає іконці, додаємо текст
                                item.setText(cell)
                            item.setBackground(QColor("#ebfbff"))  # Фон як у порожньої клітинки
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
        QMessageBox.information(self, "Про програму", "Це редактор рівнів для 2D ігрового рушія.")

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
                
        add_enemy_menu = menu.addMenu("Додати ворога")
        add_enemy_action = QAction("Додати зомбі", self)
        add_enemy_action.triggered.connect(lambda: self.add_element('1'))  # Наприклад, додаємо ворога 1
        add_enemy_menu.addAction(add_enemy_action)
        
        add_enemy_action = QAction("Додати скелета", self)
        add_enemy_action.triggered.connect(lambda: self.add_element('1'))  # Наприклад, додаємо ворога 1
        add_enemy_menu.addAction(add_enemy_action)
        
        add_enemy_action = QAction("Додати боса", self)
        add_enemy_action.triggered.connect(lambda: self.add_element('1'))  # Наприклад, додаємо ворога 1
        add_enemy_menu.addAction(add_enemy_action)

        add_player_action = QAction("Додати гравця", self)
        add_player_action.triggered.connect(lambda: self.add_element('@'))
        menu.addAction(add_player_action)
        
        add_item_action = QAction("Додати предмет", self)
        add_item_action.triggered.connect(lambda: self.add_element('*'))
        menu.addAction(add_item_action)
        
        add_wall_action = QAction("Додати стіну", self)
        add_wall_action.triggered.connect(lambda: self.add_element('#'))
        menu.addAction(add_wall_action)

        clear_cell_action = QAction("Очистити клітинку", self)
        clear_cell_action.triggered.connect(lambda: self.add_element('.'))
        menu.addAction(clear_cell_action)

        # Відобразити меню в позиції курсора
        menu.exec_(self.level_table.viewport().mapToGlobal(position))

    def resizeEvent(self, event):
        """Оновлює розмір фонового зображення при зміні розміру вікна."""
        self.background_label.setGeometry(self.rect())  # Оновлюємо розмір QLabel
        super().resizeEvent(event)

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
    sys.exit(app.exec_())