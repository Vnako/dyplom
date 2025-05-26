from editor_logic import save_level, load_level

def main():
    print("=== CLI Редактор Рівнів ===")
    print("1. Створити рівень")
    print("2. Відкрити рівень")
    choice = input("Ваш вибір: ")

    if choice == "1":
        name = input("Введіть ім’я рівня: ")
        width = input("Введіть ширину рівня: ")
        height = input("Введіть висоту рівня: ")
        try:
            width = int(width)
            height = int(height)
            path = save_level(name, width, height)
            print(f"Рівень збережено в: {path}")
        except ValueError:
            print("Помилка: ширина та висота повинні бути цілими числами.")
    elif choice == "2":
        name = input("Введіть ім’я рівня для відкриття: ")
        try:
            level_name = load_level(name)
            print(f"Завантажено рівень: {level_name}")
        except FileNotFoundError as e:
            print(f"Помилка: {e}")
    else:
        print("Невідомий вибір.")

if __name__ == "__main__":
    main()
