#ПРОШУ ПРОЩЕНИЯ ЗА ТО ЧТО НЕТ КОМЕНТАРИЕВ, МНЕ БЫЛО ЛЕНЬ＞﹏＜

import time
import keyboard
import mouse
from dataclasses import dataclass

@dataclass
class Clicker:
    button: str
    acceleration: bool
    base_interval: float
    start_interval: float
    min_interval: float
    current_interval: float = 1.0
    active: bool = False

    def click(self):
        mouse.hold(button=self.button)
        time.sleep(self.get_interval())
        mouse.release(button=self.button)
        time.sleep(self.get_interval())
        self.update_interval()

    def get_interval(self):
        return self.current_interval if self.acceleration else self.base_interval / 2

    def update_interval(self):
        if self.acceleration and self.current_interval > self.min_interval:
            self.current_interval *= 0.95
            if self.current_interval < self.min_interval:
                self.current_interval = self.min_interval

    def reset_interval(self):
        self.current_interval = self.start_interval

def main():
    print("Включить ускорение? (1 - Да, 0 - Нет)")
    acceleration = input().strip() == "1"

    base_interval = 0.1
    start_interval = 0.5
    min_interval = 0.01
    reset_key = ""
    
    if acceleration:
        print("Задайте начальный интервал для ускорения (милисекунды):")
        start_interval = float(input().strip()) / 1000
        print("Задайте конечный (минимальный) интервал для ускорения (милисекунды):")
        min_interval = float(input().strip()) / 1000
        
        if min_interval >= start_interval:
            print("Ошибка: конечный интервал должен быть меньше начального!")
            print("Установлены значения по умолчанию: начальный=500мс, конечный=10мс")
            start_interval = 0.5
            min_interval = 0.01
        elif min_interval < 0.001:
            print("Предупреждение: установлено очень малое значение интервала!")
        
        print("Клавиша для сброса ускорения (опционально):", end=' ')
        reset_key = input().strip()
    
    if not acceleration:
        print("Задайте базовый интервал (милисекунды):")
        base_interval = float(input().strip()) / 1000

    print("Задайте горячие клавиши")
    print("ЛКМ", end=' ')
    LKM = input().strip()
    
    print("ПКМ", end=' ')
    PKM = input().strip()
    
    print("Включить оптимизацию? (1 - Да, 0 - Нет)")
    print("*количество кпс немного уменьшится")
    opt = int(input().strip())

    left_clicker = Clicker(
        button="left", 
        acceleration=acceleration, 
        base_interval=base_interval,
        start_interval=start_interval,
        min_interval=min_interval
    )
    right_clicker = Clicker(
        button="right", 
        acceleration=acceleration, 
        base_interval=base_interval,
        start_interval=start_interval,
        min_interval=min_interval
    )
    
    left_clicker.reset_interval()
    right_clicker.reset_interval()

    keyboard.add_hotkey(LKM, lambda: setattr(left_clicker, "active", not left_clicker.active))
    keyboard.add_hotkey(PKM, lambda: setattr(right_clicker, "active", not right_clicker.active))
    
    if acceleration and reset_key:
        keyboard.add_hotkey(reset_key, lambda: [
            left_clicker.reset_interval(),
            right_clicker.reset_interval(),
            print("Ускорение сброшено!")
        ])

    print(f"\nГотово!")
    print(f"{LKM} - Вкл/Выкл ЛКМ")
    print(f"{PKM} - Вкл/Выкл ПКМ")
    if acceleration and reset_key:
        print(f"{reset_key} - Сброс ускорения")
    print("Текущие настройки:")
    if acceleration:
        print(f"  Ускорение: ВКЛ")
        print(f"  Начальный интервал: {start_interval*1000:.1f}мс")
        print(f"  Конечный интервал: {min_interval*1000:.1f}мс")
    else:
        print(f"  Ускорение: ВЫКЛ")
        print(f"  Интервал: {base_interval*1000:.1f}мс")
    print(f"  Оптимизация: {'ВКЛ' if opt == 1 else 'ВЫКЛ'}")
    print("Ctrl+C - выход\n")

    try:
        while True:
            if left_clicker.active:
                left_clicker.click()
            if right_clicker.active:
                right_clicker.click()
            if opt == 1:
                time.sleep(0.001)
            else:
                time.sleep(0.0001)
    except KeyboardInterrupt:
        print("\nПрограмма завершена.")

if __name__ == "__main__":
    main()
