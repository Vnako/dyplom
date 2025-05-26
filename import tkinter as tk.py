import tkinter as tk
from tkinter import ttk

def update_volume(val):
    volume_label.config(text=f"Гучність: {int(float(val))}%")

# Створюємо головне вікно
root = tk.Tk()
root.title("Повзунок гучності")
root.geometry("300x150")

# Повзунок
volume_slider = ttk.Scale(
    root,
    from_=0,
    to=100,
    orient='horizontal',
    command=update_volume
)
volume_slider.set(50)  # Початкове значення
volume_slider.pack(pady=20)

# Мітка для відображення гучності
volume_label = tk.Label(root, text="Гучність: 50%")
volume_label.pack()

# Запуск
root.mainloop()
