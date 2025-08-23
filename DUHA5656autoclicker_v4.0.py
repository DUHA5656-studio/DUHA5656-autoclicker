# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import time
import threading

# Функция для установки библиотек
def install_packages():
    required_packages = ['pyqt5', 'keyboard', 'mouse']
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            print(f"Устанавливаю {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Устанавливаем необходимые библиотеки
install_packages()

# Теперь импортируем библиотеки
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTextEdit, QCheckBox, QGroupBox, QMessageBox,
                             QSpinBox, QDoubleSpinBox, QComboBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor
import keyboard
import mouse

# Скрываем консольное окно (для Windows)
if os.name == 'nt':
    import ctypes
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

class BeautifulAutoClicker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DUHA5656 Autoclicker")
        self.setGeometry(100, 100, 800, 700)
        
        # Настройка темной цветовой палитры
        self.set_dark_palette()
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной layout
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Заголовок
        title = QLabel("DUHA5656 AUTOCLICKER")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #bb86fc; margin: 10px;")
        layout.addWidget(title)
        
        # Группа настроек
        settings_group = QGroupBox("Настройки кликера")
        settings_group.setStyleSheet("QGroupBox { color: #bb86fc; font-weight: bold; }")
        layout.addWidget(settings_group)
        
        settings_layout = QVBoxLayout(settings_group)
        
        # Настройка ускорения
        self.accel_checkbox = QCheckBox("Включить ускорение кликов")
        self.accel_checkbox.setStyleSheet("color: #ffffff;")
        settings_layout.addWidget(self.accel_checkbox)
        
        # Настройки интервалов
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Начальный интервал (мс):"))
        self.start_interval = QDoubleSpinBox()
        self.start_interval.setRange(0.001, 2000)
        self.start_interval.setValue(500)
        self.start_interval.setSuffix(" мс")
        self.start_interval.setDecimals(3)
        self.start_interval.setSingleStep(0.001)
        self.start_interval.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        interval_layout.addWidget(self.start_interval)
        
        interval_layout.addWidget(QLabel("Мин. интервал (мс):"))
        self.min_interval = QDoubleSpinBox()
        self.min_interval.setRange(0.001, 1000)
        self.min_interval.setValue(10)
        self.min_interval.setSuffix(" мс")
        self.min_interval.setDecimals(3)
        self.min_interval.setSingleStep(0.001)
        self.min_interval.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        interval_layout.addWidget(self.min_interval)
        settings_layout.addLayout(interval_layout)
        
        # Базовый интервал
        base_layout = QHBoxLayout()
        base_layout.addWidget(QLabel("Базовый интервал (мс):"))
        self.base_interval = QDoubleSpinBox()
        self.base_interval.setRange(0.001, 2000)
        self.base_interval.setValue(100)
        self.base_interval.setSuffix(" мс")
        self.base_interval.setDecimals(3)
        self.base_interval.setSingleStep(0.001)
        self.base_interval.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        base_layout.addWidget(self.base_interval)
        settings_layout.addLayout(base_layout)
        
        # Клавиша сброса ускорения
        reset_layout = QHBoxLayout()
        reset_layout.addWidget(QLabel("Клавиша сброса ускорения:"))
        self.reset_key = QComboBox()
        self.reset_key.addItems(["", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12"])
        self.reset_key.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        reset_layout.addWidget(self.reset_key)
        settings_layout.addLayout(reset_layout)
        
        # Горячие клавиши
        hotkey_group = QGroupBox("Горячие клавиши")
        hotkey_group.setStyleSheet("QGroupBox { color: #bb86fc; font-weight: bold; }")
        layout.addWidget(hotkey_group)
        
        hotkey_layout = QVBoxLayout(hotkey_group)
        
        lkm_layout = QHBoxLayout()
        lkm_layout.addWidget(QLabel("ЛКМ:"))
        self.lkm_key = QComboBox()
        self.lkm_key.addItems(["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12"])
        self.lkm_key.setCurrentText("F6")
        self.lkm_key.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        lkm_layout.addWidget(self.lkm_key)
        hotkey_layout.addLayout(lkm_layout)
        
        pkm_layout = QHBoxLayout()
        pkm_layout.addWidget(QLabel("ПКМ:"))
        self.pkm_key = QComboBox()
        self.pkm_key.addItems(["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12"])
        self.pkm_key.setCurrentText("F7")
        self.pkm_key.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        pkm_layout.addWidget(self.pkm_key)
        hotkey_layout.addLayout(pkm_layout)
        
        # Оптимизация
        self.optimization = QCheckBox("Включить оптимизацию (меньше КПС, но стабильнее)")
        self.optimization.setChecked(True)
        self.optimization.setStyleSheet("color: #ffffff;")
        hotkey_layout.addWidget(self.optimization)
        
        # Кнопки управления
        button_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("Запуск кликера")
        self.start_btn.setStyleSheet(self.get_button_style("#bb86fc"))
        self.start_btn.clicked.connect(self.start_clicker)
        button_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("Остановить")
        self.stop_btn.setStyleSheet(self.get_button_style("#cf6679"))
        self.stop_btn.clicked.connect(self.stop_clicker)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn)
        
        layout.addLayout(button_layout)
        
        # Статус
        self.status_label = QLabel("Готов к работе")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #03dac6; font-weight: bold; padding: 10px;")
        layout.addWidget(self.status_label)
        
        # Лог
        log_group = QGroupBox("Лог действий")
        log_group.setStyleSheet("QGroupBox { color: #bb86fc; font-weight: bold; }")
        layout.addWidget(log_group)
        
        log_layout = QVBoxLayout(log_group)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("color: #e0e0e0; background-color: #1e1e1e;")
        self.log_text.setFont(QFont("Consolas", 10))
        log_layout.addWidget(self.log_text)
        
        # Инициализация кликера
        self.clicker_active = False
        self.left_clicker = None
        self.right_clicker = None
        
        self.log("Программа инициализирована. Настройте параметры и нажмите 'Запуск кликера'")
    
    def set_dark_palette(self):
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(30, 30, 30))
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.Highlight, QColor(187, 134, 252))
        dark_palette.setColor(QPalette.HighlightedText, Qt.black)
        QApplication.setPalette(dark_palette)
    
    def get_button_style(self, color):
        return f"""
            QPushButton {{
                background-color: {color};
                color: black;
                border: none;
                padding: 12px;
                font-weight: bold;
                border-radius: 10px;
                min-width: 120px;
            }}
            QPushButton:hover {{
                background-color: #ffffff;
                color: black;
            }}
            QPushButton:pressed {{
                background-color: #2a2a2a;
                color: #666666;
            }}
            QPushButton:disabled {{
                background-color: #2a2a2a;
                color: #666666;
            }}
        """
    
    def log(self, message):
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
    
    def start_clicker(self):
        try:
            acceleration = self.accel_checkbox.isChecked()
            base_interval = self.base_interval.value() / 1000
            start_interval = self.start_interval.value() / 1000
            min_interval = self.min_interval.value() / 1000
            reset_key = self.reset_key.currentText()
            lkm_key = self.lkm_key.currentText()
            pkm_key = self.pkm_key.currentText()
            optimization = self.optimization.isChecked()
            
            if acceleration and min_interval >= start_interval:
                QMessageBox.warning(self, "Ошибка", "Конечный интервал должен быть меньше начального!")
                return
            
            if base_interval < 0.000001 or (acceleration and (start_interval < 0.000001 or min_interval < 0.000001)):
                QMessageBox.warning(self, "Внимание", "Слишком маленькие значения интервалов могут привести к нестабильной работе!")
            
            self.left_clicker = Clicker(
                button="left", 
                acceleration=acceleration, 
                base_interval=base_interval,
                start_interval=start_interval,
                min_interval=min_interval
            )
            self.right_clicker = Clicker(
                button="right", 
                acceleration=acceleration, 
                base_interval=base_interval,
                start_interval=start_interval,
                min_interval=min_interval
            )
            
            keyboard.add_hotkey(lkm_key, self.toggle_left_clicker)
            keyboard.add_hotkey(pkm_key, self.toggle_right_clicker)
            
            if acceleration and reset_key:
                keyboard.add_hotkey(reset_key, self.reset_acceleration)
            
            self.clicker_active = True
            self.clicker_thread = threading.Thread(target=self.clicker_loop, args=(optimization,))
            self.clicker_thread.daemon = True
            self.clicker_thread.start()
            
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.status_label.setText("Кликер активен")
            self.status_label.setStyleSheet("color: #03dac6; font-weight: bold; padding: 10px;")
            
            self.log("Автокликер запущен!")
            self.log(f"ЛКМ: {lkm_key}, ПКМ: {pkm_key}")
            if acceleration:
                self.log(f"Ускорение: ВКЛ (от {start_interval*1000:.3f}мс до {min_interval*1000:.3f}мс)")
                if reset_key:
                    self.log(f"Сброс ускорения: {reset_key}")
            else:
                self.log(f"Ускорение: ВЫКЛ (интервал: {base_interval*1000:.3f}мс)")
            self.log(f"Оптимизация: {'ВКЛ' if optimization else 'ВЫКЛ'}")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось запустить кликер: {str(e)}")
    
    def stop_clicker(self):
        self.clicker_active = False
        if self.clicker_thread.is_alive():
            self.clicker_thread.join(timeout=1.0)
        
        try:
            keyboard.unhook_all()
        except:
            pass
        
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("Кликер остановлен")
        self.status_label.setStyleSheet("color: #cf6679; font-weight: bold; padding: 10px;")
        self.log("Автокликер остановлен")
    
    def toggle_left_clicker(self):
        if self.left_clicker:
            self.left_clicker.active = not self.left_clicker.active
            status = "ВКЛ" if self.left_clicker.active else "ВЫКЛ"
            self.log(f"ЛКМ {status}")
    
    def toggle_right_clicker(self):
        if self.right_clicker:
            self.right_clicker.active = not self.right_clicker.active
            status = "ВКЛ" if self.right_clicker.active else "ВЫКЛ"
            self.log(f"ПКМ {status}")
    
    def reset_acceleration(self):
        if self.left_clicker:
            self.left_clicker.reset_interval()
        if self.right_clicker:
            self.right_clicker.reset_interval()
        self.log("Ускорение сброшено!")
    
    def clicker_loop(self, optimization):
        while self.clicker_active:
            try:
                if self.left_clicker and self.left_clicker.active:
                    self.left_clicker.click()
                if self.right_clicker and self.right_clicker.active:
                    self.right_clicker.click()
                
                if optimization:
                    time.sleep(0.001)
                else:
                    time.sleep(0.0001)
            except Exception as e:
                self.log(f"Ошибка в цикле кликера: {str(e)}")
                break

class Clicker:
    def __init__(self, button, acceleration, base_interval, start_interval, min_interval):
        self.button = button
        self.acceleration = acceleration
        self.base_interval = base_interval
        self.start_interval = start_interval
        self.min_interval = min_interval
        self.current_interval = start_interval
        self.active = False

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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = BeautifulAutoClicker()
    window.show()
    sys.exit(app.exec_())
