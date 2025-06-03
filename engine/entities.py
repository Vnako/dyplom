import pygame
import time

TILE_SIZE = 100

class Block:
    def __init__(self, x, y, is_solid, texture):
        """
        Ініціалізує об'єкт Block.
        :param x: Координата X
        :param y: Координата Y
        :param is_solid: Чи є блок твердим
        :param texture: Текстура блоку
        """
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.is_solid = is_solid
        self.texture = texture

    def draw(self, screen, camera):
        """
        Малює блок на екрані з урахуванням камери.
        :param screen: Поверхня для малювання
        :param camera: Камера для зміщення
        """
        screen.blit(self.texture, camera.apply(self))

class Player:
    def __init__(self, pos, textures, gem_textures=None):
        """
        Ініціалізує гравця.
        :param pos: Початкова позиція гравця (x, y)
        :param textures: Словник текстур для гравця
        """
        self.textures = textures  # Assign textures to self.textures
        self.rect = pygame.Rect(pos[0], pos[1], self.textures['player_left'].get_width(), self.textures['player_left'].get_height())
        self.texture = textures['player_left']  # Початкова текстура
        self.speed = 7
        self.dx = 0
        self.dy = 0
        self.health = 100
        self.protection = 5
        self.luck = 1
        self.atk = 10
        self.last_damage_time = 0  # Час останнього отримання шкоди

        # --- Додаємо змінні для гемів 5x5 ---
        for i in range(1, 6):
            for j in range(1, 6):
                setattr(self, f"gem{i}{j}", False)
        self.gem_textures = gem_textures if gem_textures is not None else {}

    def handle_input(self, active_keys):
        """
        Обробляє введення з клавіатури для руху гравця.
        :param active_keys: Набір активних клавіш
        """
        self.dx = 0
        self.dy = 0  # Скидаємо рух перед обробкою клавіш

        if pygame.K_a in active_keys:  # Ліва клавіша (A)
            self.dx = -self.speed
            self.texture = self.textures['player_left']
        elif pygame.K_d in active_keys:  # Права клавіша (D)
            self.dx = self.speed
            self.texture = self.textures['player_right']

        if pygame.K_w in active_keys:  # Верхня клавіша (W)
            self.dy = -self.speed
            self.texture = self.textures['player_back_left']
            if pygame.K_a in active_keys:  # Якщо рух вліво
                self.texture = self.textures['player_back_left']
            elif pygame.K_d in active_keys:  # Якщо рух вправо
                self.texture = self.textures['player_back_right']
        elif pygame.K_s in active_keys:  # Нижня клавіша (S)
            self.dy = self.speed
            self.texture = self.textures['player_left']
            if pygame.K_a in active_keys:  # Якщо рух вліво
                self.texture = self.textures['player_left']
            elif pygame.K_d in active_keys:  # Якщо рух вправо
                self.texture = self.textures['player_right']

    def update(self, blocks, items, statues):
        """
        Оновлює положення гравця та перевіряє колізії з блоками, предметами та статуями.
        """
        # Перевірка колізій по X
        self.rect.x += self.dx
        for block in blocks:
            if block.is_solid and self.rect.colliderect(block.rect):
                if self.dx > 0:  # Рух праворуч
                    self.rect.right = block.rect.left
                elif self.dx < 0:  # Рух ліворуч
                    self.rect.left = block.rect.right

        for item in items:
            if item.is_solid and self.rect.colliderect(item.rect):
                if self.dx > 0:  # Рух праворуч
                    self.rect.right = item.rect.left
                elif self.dx < 0:  # Рух ліворуч
                    self.rect.left = item.rect.right

        for statue in statues:
            if statue.is_colliding(self.rect):  # Використовуємо метод is_colliding
                if self.dx > 0:  # Рух праворуч
                    self.rect.right = statue.solid_rect.left
                elif self.dx < 0:  # Рух ліворуч
                    self.rect.left = statue.solid_rect.right

        # Перевірка колізій по Y
        self.rect.y += self.dy
        for block in blocks:
            if block.is_solid and self.rect.colliderect(block.rect):
                if self.dy > 0:  # Рух вниз
                    self.rect.bottom = block.rect.top
                elif self.dy < 0:  # Рух вгору
                    self.rect.top = block.rect.bottom

        for item in items:
            if item.is_solid and self.rect.colliderect(item.rect):
                if self.dy > 0:  # Рух вниз
                    self.rect.bottom = item.rect.top
                elif self.dy < 0:  # Рух вгору
                    self.rect.top = item.rect.bottom

        for statue in statues:
            if statue.is_colliding(self.rect):  # Використовуємо метод is_colliding
                if self.dy > 0:  # Рух вниз
                    self.rect.bottom = statue.solid_rect.top
                elif self.dy < 0:  # Рух вгору
                    self.rect.top = statue.solid_rect.bottom

    def draw(self, screen, camera):
        """
        Малює гравця на екрані з урахуванням камери.
        """
        screen.blit(self.texture, camera.apply(self))

    def take_damage(self, amount=1, enemy_rect=None):
        """
        Зменшує здоров'я гравця на задану кількість.
        Якщо здоров'я <= 0, гравець помирає.
        :param amount: Кількість шкоди (за замовчуванням 1)
        :param enemy_rect: Прямокутник ворога, який завдав шкоди
        """
        current_time = pygame.time.get_ticks()
        self.health -= amount
        self.last_damage_time = current_time

        if enemy_rect:
                # Тимчасове зміщення текстури гравця
                offset_x = 10 if self.rect.centerx < enemy_rect.centerx else -10
                offset_y = 10 if self.rect.centery < enemy_rect.centery else -10
                self.rect.move_ip(offset_x, offset_y)
                pygame.time.delay(300)  # Затримка 0,3 секунди для візуального ефекту
                # Повернення до початкової позиції
                self.rect.move_ip(-offset_x, -offset_y)

        if self.health <= 0:
                print("Гравець помер")
                self.health = 0

class Camera:
    """
    Клас для управління камерою, яка слідує за гравцем.
    """
    def __init__(self, width, height):
        self.camera_rect = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, entity):
        """
        Зміщує об'єкт відповідно до положення камери.
        """
        return entity.rect.move(self.camera_rect.topleft)

    def apply_rect(self, rect):
        """
        Зміщує прямокутник відповідно до положення камери.
        """
        return rect.move(self.camera_rect.topleft)

    def update(self, target):
        """
        Оновлює положення камери відповідно до положення гравця.
        """
        display_info = pygame.display.Info()
        SCREEN_WIDTH, SCREEN_HEIGHT = display_info.current_w, display_info.current_h
        x = -target.rect.centerx + SCREEN_WIDTH // 2
        y = -target.rect.centery + SCREEN_HEIGHT // 2

        # Обмеження камери в межах рівня
        x = min(0, x)  # Ліва межа
        y = min(0, y)  # Верхня межа
        x = max(-(self.width - SCREEN_WIDTH), x)  # Права межа
        y = max(-(self.height - SCREEN_HEIGHT), y)  # Нижня межа

        self.camera_rect = pygame.Rect(x, y, self.width, self.height)

class Enemy:
    def __init__(self, x, y, enemy_type, textures, health):
        
        if enemy_type in textures:
            self.texture = textures[enemy_type]
        else:
            print(f"Попередження: Текстура для типу ворога '{enemy_type}' відсутня. Використовується текстура зомбі.")
            self.texture = textures['zombie_left']  # За замовчуванням текстура зомбі

        # Визначення розміру текстури
        texture_width, texture_height = self.texture.get_width(), self.texture.get_height()

        # Розрахунок зміщення для позиціонування rect посередині текстури знизу
        rect_x = x * TILE_SIZE + (TILE_SIZE - texture_width) // 2
        rect_y = y * TILE_SIZE + (TILE_SIZE - texture_height)
        self.rect = pygame.Rect(rect_x, rect_y, texture_width, texture_height)

        self.type = enemy_type
        self.health = health
        self.last_attack_time = time.time()  # Час останньої атаки
        self.is_colliding_with_player = False  # Стан колізії з гравцем
        self.dx = 0  # Ініціалізація зміщення по осі X
        self.dy = 0  # Ініціалізація зміщення по осі Y
        self.textures = textures  # Зберігаємо словник текстур
        self.current_texture = self.texture  # Ініціалізуємо поточну текстуру

        # Встановлення початкової текстури залежно від типу ворога
        if enemy_type == "zombie":
            self.current_texture = textures["zombie_left"]
        elif enemy_type == "skeleton":
            self.current_texture = textures["skeleton_left"]
        elif enemy_type == "boss":
            self.current_texture = textures["boss_left"]
        else:
            print(f"Попередження: Текстура для типу ворога '{enemy_type}' відсутня. Використовується текстура зомбі.")
            self.current_texture = textures["zombie_left"]

    def draw(self, surface, camera):
        surface.blit(self.texture, camera.apply(self))

    def move_towards_player(self, player_rect, blocks):
        """
        Рух ворога у напрямку до гравця.
        :param player_rect: Прямокутник гравця.
        :param blocks: Список блоків, які є перешкодами.
        """
        self.dx = 0
        self.dy = 0

        # Визначення напрямку руху
        if self.rect.x < player_rect.x:
            self.dx = 1
        elif self.rect.x > player_rect.x:
            self.dx = -1

        if self.rect.y < player_rect.y:
            self.dy = 1
        elif self.rect.y > player_rect.y:
            self.dy = -1

        if self.type == "zombie":
            if self.dy > 0:  # Рух вниз
                self.current_texture = self.textures["zombie_left"]
            elif self.dy < 0:  # Рух вгору
                if self.dx < 0:  # Вгору і вліво
                    self.current_texture = self.textures["zombie_back_left"]
                elif self.dx > 0:  # Вгору і вправо
                    self.current_texture = self.textures["zombie_back_right"]
                else:  # Просто вгору
                    self.current_texture = self.textures["zombie_back_left"]
            elif self.dx < 0:  # Рух вліво
                self.current_texture = self.textures["zombie_left"]
            elif self.dx > 0:  # Рух вправо
                self.current_texture = self.textures["zombie_right"]

        elif self.type == "skeleton":
            if self.dy > 0:  # Рух вниз
                self.current_texture = self.textures["skeleton_left"]
            elif self.dy < 0:  # Рух вгору
                if self.dx < 0:  # Вгору і вліво
                    self.current_texture = self.textures["skeleton_back_left"]
                elif self.dx > 0:  # Вгору і вправо
                    self.current_texture = self.textures["skeleton_back_right"]
                else:  # Просто вгору
                    self.current_texture = self.textures["skeleton_back_left"]
            elif self.dx < 0:  # Рух вліво
                self.current_texture = self.textures["skeleton_left"]
            elif self.dx > 0:  # Рух вправо
                self.current_texture = self.textures["skeleton_right"]

        elif self.type == "boss":
            if self.dy > 0:  # Рух вниз
                self.current_texture = self.textures["boss_left"]
            elif self.dy < 0:  # Рух вгору
                if self.dx < 0:  # Вгору і вліво
                    self.current_texture = self.textures["boss_back_left"]
                elif self.dx > 0:  # Вгору і вправо
                    self.current_texture = self.textures["boss_back_right"]
                else:  # Просто вгору
                    self.current_texture = self.textures["boss_back_left"]
            elif self.dx < 0:  # Рух вліво
                self.current_texture = self.textures["boss_left"]
            elif self.dx > 0:  # Рух вправо
                self.current_texture = self.textures["boss_right"]

    def draw(self, screen, camera):
        """
        Малює ворога на екрані.
        :param screen: Екран для малювання.
        :param camera: Камера для врахування зміщення.
        """
        screen.blit(self.current_texture, camera.apply(self))

    def handle_movement(self, blocks, statues):
        """
        Обробляє переміщення ворога з урахуванням перешкод.
        :param blocks: Список блоків, які є перешкодами.
        :param statues: Список статуй, які можуть бути перешкодами.
        """
        # Зберігаємо початкову позицію
        initial_position = self.rect.topleft

        # Оновлюємо позицію ворога
        self.rect.x += self.dx
        # Перевірка колізій із блоками по осі X
        for block in blocks:
            if block.is_solid and self.rect.colliderect(block.rect):
                self.rect.x = initial_position[0]  # Повертаємо ворога на початкову позицію по X
                break

        # Перевірка колізій із статуями по осі X
        for statue in statues:
            if statue.is_solid and self.rect.colliderect(statue.rect):
                self.rect.x = initial_position[0]  # Повертаємо ворога на початкову позицію по X
                break

        self.rect.y += self.dy
        # Перевірка колізій із блоками по осі Y
        for block in blocks:
            if block.is_solid and self.rect.colliderect(block.rect):
                self.rect.y = initial_position[1]  # Повертаємо ворога на початкову позицію по Y
                break

        # Перевірка колізій із статуями по осі Y
        for statue in statues:
            if statue.is_solid and self.rect.colliderect(statue.rect):
                self.rect.y = initial_position[1]  # Повертаємо ворога на початкову позицію по Y
                break

        # Скидаємо зміщення після обробки
        self.dx = 0
        self.dy = 0
    
    def take_damage(self, amount):
        """
        Реакція ворога на отримання шкоди.
        Текстура ворога підіймається на 10 пікселів на 0,3 секунди.
        ;param amount: Кількість шкоди
        """
        self.health -= amount
        if self.health <= 0:
            print(f"{self.type.capitalize()} помер")
            self.health = 0
            return
        original_position = self.rect.topleft
        self.rect.move_ip(-10, 0)  # Піднімаємо текстуру на 10 пікселів
        pygame.time.delay(300)  # Затримка 0,3 секунди
        self.rect.topleft = original_position  # Повертаємо текстуру на місце

    def attack(self, player):
        """
        Атакує гравця, якщо пройшла 1 секунда з моменту останньої атаки.
        :param player: Об'єкт гравця
        """
        current_time = pygame.time.get_ticks()
        if current_time - self.last_attack_time >= 1000:  # Інтервал атаки 1 секунда
            print(f"Ворог {self.type} атакує гравця. Здоров'я гравця: {player.health}")
            player.take_damage(amount=1, enemy_rect=self.rect)  # Завдає шкоди гравцю
            self.last_attack_time = current_time

class Item:
    def __init__(self, x, y, is_solid, textures):
        """
        Ініціалізує об'єкт Item.
        :param x: Координата X
        :param y: Координата Y
        :param is_solid: Чи є об'єкт твердим
        :param textures: Список текстур для анімації
        """
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.is_solid = is_solid
        if isinstance(textures, list):
            self.textures = textures  # Список текстур для анімації
        else:
            raise TypeError("textures має бути списком текстур для анімації.")
        self.current_frame = 0
        self.animation_active = False
        self.animation_speed = 10  # Кількість кадрів між зміною текстури
        self.frame_counter = 0

    def trigger_animation(self):
        """
        Запускає анімацію об'єкта.
        """
        if not self.animation_active:  # Запускаємо анімацію, тільки якщо вона ще не активна
            self.animation_active = True
            self.current_frame = 0
            self.frame_counter = 0

    def is_adjacent(self, player_rect):
        """
        Перевіряє, чи гравець знаходиться в сусідньому блоці від предмета.
        :param player_rect: Прямокутник гравця
        :return: True, якщо гравець у сусідньому блоці, інакше False
        """
        return (
            abs(self.rect.x - player_rect.x) == TILE_SIZE and self.rect.y == player_rect.y or
            abs(self.rect.y - player_rect.y) == TILE_SIZE and self.rect.x == player_rect.x
        )

    def update(self):
        """
        Оновлює стан анімації.
        """
        if self.animation_active:
            self.frame_counter += 1
            if self.frame_counter >= self.animation_speed:
                self.current_frame += 1
                self.frame_counter = 0
                if self.current_frame >= len(self.textures):
                    self.animation_active = False  # Завершення анімації
                    self.current_frame = len(self.textures) - 1  # Залишаємо останній кадр
                    print(f"Item.update: Анімація завершена для Item на позиції ({self.rect.x}, {self.rect.y})")  # Додано: журнал

    def draw(self, screen, camera):
        """
        Малює об'єкт на екрані.
        :param screen: Поверхня для малювання
        :param camera: Камера для зміщення
        """
        texture = self.textures[self.current_frame]
        screen.blit(texture, camera.apply(self))
        
    def debug_draw_rect(self, screen, camera):
        """
        Малює прямокутник предмета для налагодження.
        :param screen: Поверхня для малювання
        :param camera: Камера для зміщення
        """
        #pygame.draw.rect(screen, (255, 0, 0), camera.apply_rect(self.rect), 2)  # Червоний прямокутник

class Npc:
    def __init__(self, x, y, npc_type, textures):
        """
        Ініціалізація NPC.

        :param x: Координата X
        :param y: Координата Y
        :param npc_type: Тип NPC ('teleport', 'enemy')
        :param textures: Словник текстур для npc_type
        """
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.type = npc_type

        if npc_type in textures:
            self.texture = textures[npc_type]
        else:
            print(f"Попередження: Текстура для типу NPC '{npc_type}' відсутня або є None.")
            self.texture = textures['teleport']

        # Визначення позиції текстури відносно лівого нижнього кута
        self.texture_offset = max(0, self.texture.get_height() - TILE_SIZE)  # Захист від негативного значення

    def draw(self, surface, camera):
        """
        Малює NPC на екрані.
        :param surface: Поверхня для малювання
        :param camera: Камера для зміщення
        """
        texture_position = camera.apply(self).move(0, -self.texture_offset)  # Зміщення текстури вниз
        surface.blit(self.texture, texture_position)

class IntStat:
    def __init__(self, x, y, is_solid, statue_type, textures):
        if not isinstance(textures, dict):  # Перевіряємо, чи textures є словником
            raise TypeError("textures має бути словником, що містить текстури статуй.")

        # Використовуємо ключ із префіксом 'statue'
        self.texture = textures.get(statue_type)
        if self.texture is None:
            raise KeyError(f"Текстура для типу статуї '{statue_type}' відсутня в словнику textures.")

        # Визначення розміру текстури
        texture_width, texture_height = self.texture.get_width(), self.texture.get_height()

        # Розрахунок зміщення для позиціонування rect посередині текстури знизу
        rect_x = x
        rect_y = y - (texture_height - TILE_SIZE)  # Враховуємо висоту текстури
        self.rect = pygame.Rect(rect_x, rect_y, texture_width, texture_height)

        # Додано: визначення твердої області
        solid_width = 150
        solid_height = 65
        solid_x = rect_x + (texture_width - solid_width) // 2
        solid_y = rect_y + texture_height - solid_height
        self.solid_rect = pygame.Rect(solid_x, solid_y, solid_width, solid_height)

        self.type = statue_type
        self.is_solid = is_solid
        
    def draw(self, screen, camera):
        """
        Малює всю текстуру статуї на екрані.
        :param screen: Поверхня для малювання
        :param camera: Камера для зміщення
        """
        # Отримуємо позицію для малювання текстури з урахуванням камери
        texture_position = camera.apply_rect(self.rect)
                
        # Малюємо всю текстуру статуї
        screen.blit(self.texture, texture_position)
        
    def is_colliding(self, other_rect):
        """
        Перевіряє, чи є колізія з твердою областю статуї.
        :param other_rect: Прямокутник іншого об'єкта
        :return: True, якщо є колізія, інакше False
        """
        return self.is_solid and self.solid_rect.colliderect(other_rect)
