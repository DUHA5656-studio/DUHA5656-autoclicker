# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import time
import threading
import json
from pathlib import Path
from typing import Any, Dict, Optional
import logging

# Функция для установки библиотек
def install_packages():
    required_packages = ['pyqt5', 'evdev', 'python-xlib']
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
                             QSpinBox, QDoubleSpinBox, QComboBox, QFileDialog)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor

# Linux-специфичные импорты
try:
    from evdev import InputDevice, list_devices, ecodes
    import Xlib.display
    LINUX_SUPPORT = True
except ImportError:
    LINUX_SUPPORT = False
    print("Предупреждение: Linux-специфичные библиотеки не установлены")

class LinuxMouseController:
    """Контроллер мыши для Linux"""
    
    def __init__(self):
        self.display = Xlib.display.Display()
        self.screen = self.display.screen()
        self.root = self.screen.root
        
    def click(self, button=1):
        """Эмулирует клик мыши"""
        try:
            # Нажатие
            self.root.press_button(button)
            self.display.sync()
            time.sleep(0.01)
            
            # Отпускание
            self.root.release_button(button)
            self.display.sync()
            
        except Exception as e:
            print(f"Ошибка эмуляции клика: {e}")
    
    def get_position(self):
        """Возвращает текущую позицию мыши"""
        try:
            query = self.root.query_pointer()
            return query.root_x, query.root_y
        except:
            return 0, 0
    
    def move_to(self, x, y):
        """Перемещает мышь в указанные координаты"""
        try:
            self.root.warp_pointer(x, y)
            self.display.sync()
        except Exception as e:
            print(f"Ошибка перемещения мыши: {e}")

class LinuxKeyboardListener:
    """Слушатель клавиатуры для Linux"""
    
    def __init__(self, callback):
        self.callback = callback
        self.running = False
        self.thread = None
        
    def start(self):
        """Запускает слушатель клавиатуры"""
        if not LINUX_SUPPORT:
            return False
            
        self.running = True
        self.thread = threading.Thread(target=self._listen)
        self.thread.daemon = True
        self.thread.start()
        return True
    
    def stop(self):
        """Останавливает слушатель"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
    
    def _listen(self):
        """Основной цикл прослушивания клавиатуры"""
        try:
            devices = [InputDevice(path) for path in list_devices()]
            keyboard_devices = []
            
            for device in devices:
                if 'keyboard' in device.name.lower() or 'key' in device.name.lower():
                    keyboard_devices.append(device)
            
            if not keyboard_devices:
                print("Клавиатурные устройства не найдены")
                return
            
            # Используем первое найденное клавиатурное устройство
            device = keyboard_devices[0]
            device.grab()
            
            print(f"Прослушивание клавиатуры: {device.name}")
            
            while self.running:
                try:
                    for event in device.read():
                        if event.type == ecodes.EV_KEY and event.value == 1:  # Key press
                            key_code = event.code
                            self.callback(key_code)
                except BlockingIOError:
                    time.sleep(0.01)
                except Exception as e:
                    print(f"Ошибка чтения клавиатуры: {e}")
                    time.sleep(1)
                    
        except Exception as e:
            print(f"Ошибка инициализации клавиатуры: {e}")

class ConfigManager:
    """
    Менеджер конфигураций для сохранения и загрузки настроек в формате JSON
    """
    
    def __init__(self, config_dir: str = "config", default_filename: str = "autoclicker_config.json"):
        self.config_dir = Path(config_dir)
        self.default_filename = default_filename
        self.config_path = self.config_dir / default_filename
        self._ensure_config_dir()
        
        # Настройка логирования
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _ensure_config_dir(self) -> None:
        """Создает директорию для конфигураций, если она не существует"""
        self.config_dir.mkdir(exist_ok=True, parents=True)
    
    def save_config(self, config_data: Dict[str, Any], filename: Optional[str] = None) -> bool:
        """
        Сохраняет конфигурацию в JSON файл
        
        Args:
            config_data: Словарь с данными конфигурации
            filename: Имя файла (если None, используется имя по умолчанию)
        
        Returns:
            bool: True если сохранение успешно, False в противном случае
        """
        try:
            config_path = self.config_dir / (filename or self.default_filename)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
            
            self.logger.info(f"Конфигурация сохранена: {config_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка сохранения конфигурации: {e}")
            return False
    
    def load_config(self, filename: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Загружает конфигурацию из JSON файла
        
        Args:
            filename: Имя файла (если None, используется имя по умолчанию)
        
        Returns:
            Optional[Dict]: Словарь с данными конфигурации или None при ошибке
        """
        try:
            config_path = self.config_dir / (filename or self.default_filename)
            
            if not config_path.exists():
                self.logger.warning(f"Файл конфигурации не найден: {config_path}")
                return None
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            self.logger.info(f"Конфигурация загружена: {config_path}")
            return config_data
            
        except Exception as e:
            self.logger.error(f"Ошибка загрузки конфигурации: {e}")
            return None
    
    def get_config_list(self) -> list:
        """Возвращает список доступных конфигурационных файлов"""
        config_files = []
        for file in self.config_dir.glob("*.json"):
            config_files.append(file.name)
        return sorted(config_files)

class BeautifulAutoClicker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DUHA5656 Autoclicker - Linux")
        self.setGeometry(100, 100, 800, 700)
        
        # Инициализация менеджера конфигураций
        self.config_manager = ConfigManager()
        
        # Инициализация Linux-компонентов
        self.linux_mouse = LinuxMouseController() if LINUX_SUPPORT else None
        self.keyboard_listener = None
        self.hotkeys = {}
        
        # Текущая тема (по умолчанию фиолетовая)
        self.current_theme = "purple"
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной layout
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Заголовок
        title = QLabel("DUHA5656 AUTOCLICKER - LINUX")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        if not LINUX_SUPPORT:
            warning_label = QLabel("⚠️ Требуются дополнительные библиотеки: evdev, python-xlib")
            warning_label.setStyleSheet("color: red; font-weight: bold;")
            layout.addWidget(warning_label)
        
        # Группа переключения темы
        theme_group = QGroupBox("Тема оформления")
        theme_layout = QHBoxLayout(theme_group)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Фиолетово-чёрная", "purple")
        self.theme_combo.addItem("Розово-белая", "pink")
        self.theme_combo.currentIndexChanged.connect(self.change_theme)
        theme_layout.addWidget(QLabel("Тема:"))
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        
        layout.addWidget(theme_group)
        
        # Группа настроек
        settings_group = QGroupBox("Настройки кликера")
        settings_layout = QVBoxLayout(settings_group)
        
        # Настройка ускорения
        self.accel_checkbox = QCheckBox("Включить ускорение кликов")
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
        interval_layout.addWidget(self.start_interval)
        
        interval_layout.addWidget(QLabel("Мин. интервал (мс):"))
        self.min_interval = QDoubleSpinBox()
        self.min_interval.setRange(0.001, 1000)
        self.min_interval.setValue(10)
        self.min_interval.setSuffix(" мс")
        self.min_interval.setDecimals(3)
        self.min_interval.setSingleStep(0.001)
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
        base_layout.addWidget(self.base_interval)
        settings_layout.addLayout(base_layout)
        
        # Клавиша сброса ускорения
        reset_layout = QHBoxLayout()
        reset_layout.addWidget(QLabel("Клавиша сброса ускорения:"))
        self.reset_key = QComboBox()
        self.reset_key.addItems(["", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12"])
        reset_layout.addWidget(self.reset_key)
        settings_layout.addLayout(reset_layout)
        
        layout.addWidget(settings_group)
        
        # Горячие клавиши
        hotkey_group = QGroupBox("Горячие клавиши")
        hotkey_layout = QVBoxLayout(hotkey_group)
        
        lkm_layout = QHBoxLayout()
        lkm_layout.addWidget(QLabel("ЛКМ:"))
        self.lkm_key = QComboBox()
        self.lkm_key.addItems(["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12"])
        self.lkm_key.setCurrentText("F6")
        lkm_layout.addWidget(self.lkm_key)
        hotkey_layout.addLayout(lkm_layout)
        
        pkm_layout = QHBoxLayout()
        pkm_layout.addWidget(QLabel("ПКМ:"))
        self.pkm_key = QComboBox()
        self.pkm_key.addItems(["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12"])
        self.pkm_key.setCurrentText("F7")
        pkm_layout.addWidget(self.pkm_key)
        hotkey_layout.addLayout(pkm_layout)
        
        # Оптимизация
        self.optimization = QCheckBox("Включить оптимизацию (меньше КПС, но стабильнее)")
        self.optimization.setChecked(True)
        hotkey_layout.addWidget(self.optimization)
        
        layout.addWidget(hotkey_group)
        
        # Кнопки управления конфигурациями
        config_layout = QHBoxLayout()
        
        self.save_config_btn = QPushButton("💾 Сохранить конфиг")
        self.save_config_btn.clicked.connect(self.save_config)
        config_layout.addWidget(self.save_config_btn)
        
        self.load_config_btn = QPushButton("📂 Загрузить конфиг")
        self.load_config_btn.clicked.connect(self.load_config)
        config_layout.addWidget(self.load_config_btn)
        
        layout.addLayout(config_layout)
        
        # Кнопки управления
        button_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("🚀 Запуск кликера")
        self.start_btn.clicked.connect(self.start_clicker)
        button_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("⏹️ Остановить")
        self.stop_btn.clicked.connect(self.stop_clicker)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn)
        
        layout.addLayout(button_layout)
        
        # Статус
        self.status_label = QLabel("Готов к работе")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Лог
        log_group = QGroupBox("Лог действий")
        log_layout = QVBoxLayout(log_group)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 10))
        log_layout.addWidget(self.log_text)
        layout.addWidget(log_group)
        
        # Инициализация кликера
        self.clicker_active = False
        self.left_clicker = None
        self.right_clicker = None
        
        # Применяем тему по умолчанию
        self.apply_theme("purple")
        
        # Загрузка конфигурации по умолчанию при запуске
        self.load_default_config()
        
        self.log("Программа инициализирована. Настройте параметры и нажмите 'Запуск кликера'")
        
        # Таблица соответствия клавиш F-ряда для Linux
        self.f_key_mapping = {
            'F1': 59, 'F2': 60, 'F3': 61, 'F4': 62, 'F5': 63, 'F6': 64,
            'F7': 65, 'F8': 66, 'F9': 67, 'F10': 68, 'F11': 87, 'F12': 88
        }
    
    def apply_theme(self, theme_name):
        """Применяет выбранную тему оформления"""
        self.current_theme = theme_name
        
        if theme_name == "purple":
            self.set_dark_purple_palette()
        elif theme_name == "pink":
            self.set_pink_white_palette()
        
        # Обновляем стили элементов
        self.update_widget_styles()
    
    def set_dark_purple_palette(self):
        """Устанавливает тёмно-фиолетовую цветовую палитру"""
        dark_purple_palette = QPalette()
        
        # Основные цвета
        dark_purple_palette.setColor(QPalette.Window, QColor(30, 27, 46))
        dark_purple_palette.setColor(QPalette.WindowText, QColor(224, 224, 224))
        dark_purple_palette.setColor(QPalette.Base, QColor(45, 43, 85))
        dark_purple_palette.setColor(QPalette.AlternateBase, QColor(59, 48, 84))
        dark_purple_palette.setColor(QPalette.Text, QColor(224, 224, 224))
        dark_purple_palette.setColor(QPalette.Button, QColor(59, 48, 84))
        dark_purple_palette.setColor(QPalette.ButtonText, QColor(224, 224, 224))
        dark_purple_palette.setColor(QPalette.Highlight, QColor(123, 31, 162))
        dark_purple_palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        
        QApplication.setPalette(dark_purple_palette)
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1b2e;
            }
        """)
    
    def set_pink_white_palette(self):
        """Устанавливает розово-белую цветовую палитру"""
        pink_white_palette = QPalette()
        
        pink_white_palette.setColor(QPalette.Window, QColor(255, 240, 245))
        pink_white_palette.setColor(QPalette.WindowText, QColor(75, 0, 130))
        pink_white_palette.setColor(QPalette.Base, QColor(255, 255, 255))
        pink_white_palette.setColor(QPalette.Text, QColor(75, 0, 130))
        pink_white_palette.setColor(QPalette.Button, QColor(255, 182, 193))
        pink_white_palette.setColor(QPalette.ButtonText, QColor(75, 0, 130))
        pink_white_palette.setColor(QPalette.Highlight, QColor(255, 105, 180))
        pink_white_palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        
        QApplication.setPalette(pink_white_palette)
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #fff0f5;
            }
        """)
    
    def update_widget_styles(self):
        """Обновляет стили всех виджетов в соответствии с текущей темой"""
        if self.current_theme == "purple":
            self.apply_purple_styles()
        elif self.current_theme == "pink":
            self.apply_pink_styles()
    
    def apply_purple_styles(self):
        """Применяет стили для фиолетовой темы"""
        group_style = """
            QGroupBox { 
                color: #bb86fc; 
                font-weight: bold; 
                border: 2px solid #7b1fa2;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """
        
        input_style = """
            QComboBox, QDoubleSpinBox, QTextEdit {
                color: #e0e0e0;
                background-color: #2d2b55;
                border: 1px solid #7b1fa2;
                border-radius: 4px;
                padding: 5px;
            }
        """
        
        for group in self.findChildren(QGroupBox):
            group.setStyleSheet(group_style)
        
        for widget in self.findChildren((QComboBox, QDoubleSpinBox, QTextEdit)):
            widget.setStyleSheet(input_style)
        
        for checkbox in self.findChildren(QCheckBox):
            checkbox.setStyleSheet("color: #e0e0e0;")
    
    def apply_pink_styles(self):
        """Применяет стили для розовой темы"""
        group_style = """
            QGroupBox { 
                color: #ff69b4; 
                font-weight: bold; 
                border: 2px solid #ffb6c1;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """
        
        input_style = """
            QComboBox, QDoubleSpinBox, QTextEdit {
                color: #4b0082;
                background-color: #ffffff;
                border: 1px solid #ffb6c1;
                border-radius: 4px;
                padding: 5px;
            }
        """
        
        for group in self.findChildren(QGroupBox):
            group.setStyleSheet(group_style)
        
        for widget in self.findChildren((QComboBox, QDoubleSpinBox, QTextEdit)):
            widget.setStyleSheet(input_style)
        
        for checkbox in self.findChildren(QCheckBox):
            checkbox.setStyleSheet("color: #4b0082;")
    
    def keyboard_callback(self, key_code):
        """Обработчик нажатий клавиш для Linux"""
        for key_name, expected_code in self.f_key_mapping.items():
            if key_code == expected_code:
                if key_name == self.lkm_key.currentText():
                    self.toggle_left_clicker()
                elif key_name == self.pkm_key.currentText():
                    self.toggle_right_clicker()
                elif key_name == self.reset_key.currentText():
                    self.reset_acceleration()
    
    def change_theme(self):
        """Обработчик изменения темы"""
        theme_data = self.theme_combo.currentData()
        if theme_data:
            self.apply_theme(theme_data)
            self.log(f"Тема изменена на: {self.theme_combo.currentText()}")
    
    def get_current_config(self) -> Dict[str, Any]:
        """Возвращает текущие настройки в виде словаря"""
        return {
            "theme": self.current_theme,
            "acceleration": self.accel_checkbox.isChecked(),
            "start_interval": self.start_interval.value(),
            "min_interval": self.min_interval.value(),
            "base_interval": self.base_interval.value(),
            "reset_key": self.reset_key.currentText(),
            "lkm_key": self.lkm_key.currentText(),
            "pkm_key": self.pkm_key.currentText(),
            "optimization": self.optimization.isChecked(),
            "window_geometry": {
                "x": self.x(),
                "y": self.y(),
                "width": self.width(),
                "height": self.height()
            }
        }
    
    def apply_config(self, config_data: Dict[str, Any]) -> bool:
        """Применяет настройки из словаря конфигурации"""
        try:
            theme = config_data.get("theme", "purple")
            self.apply_theme(theme)
            
            index = self.theme_combo.findData(theme)
            if index >= 0:
                self.theme_combo.setCurrentIndex(index)
            
            self.accel_checkbox.setChecked(config_data.get("acceleration", False))
            self.start_interval.setValue(config_data.get("start_interval", 500))
            self.min_interval.setValue(config_data.get("min_interval", 10))
            self.base_interval.setValue(config_data.get("base_interval", 100))
            
            reset_key = config_data.get("reset_key", "")
            if reset_key in [self.reset_key.itemText(i) for i in range(self.reset_key.count())]:
                self.reset_key.setCurrentText(reset_key)
            
            lkm_key = config_data.get("lkm_key", "F6")
            if lkm_key in [self.lkm_key.itemText(i) for i in range(self.lkm_key.count())]:
                self.lkm_key.setCurrentText(lkm_key)
            
            pkm_key = config_data.get("pkm_key", "F7")
            if pkm_key in [self.pkm_key.itemText(i) for i in range(self.pkm_key.count())]:
                self.pkm_key.setCurrentText(pkm_key)
            
            self.optimization.setChecked(config_data.get("optimization", True))
            
            geometry = config_data.get("window_geometry")
            if geometry:
                self.setGeometry(
                    geometry.get("x", 100),
                    geometry.get("y", 100),
                    geometry.get("width", 800),
                    geometry.get("height", 700)
                )
            
            self.log("Конфигурация применена успешно")
            return True
            
        except Exception as e:
            self.log(f"Ошибка применения конфигурации: {str(e)}")
            return False
    
    def save_config(self):
        """Сохраняет текущую конфигурацию в файл"""
        try:
            config_data = self.get_current_config()
            
            filename, _ = QFileDialog.getSaveFileName(
                self, "Сохранить конфигурацию", 
                str(self.config_manager.config_dir / "autoclicker_config.json"),
                "JSON Files (*.json)"
            )
            
            if filename:
                if not filename.endswith('.json'):
                    filename += '.json'
                
                success = self.config_manager.save_config(config_data, Path(filename).name)
                if success:
                    self.log(f"Конфигурация сохранена: {filename}")
                    QMessageBox.information(self, "Успех", "Конфигурация успешно сохранена!")
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось сохранить конфигурацию")
                    
        except Exception as e:
            self.log(f"Ошибка при сохранении конфигурации: {str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить конфигурацию: {str(e)}")
    
    def load_config(self):
        """Загружает конфигурацию из файла"""
        try:
            config_files = self.config_manager.get_config_list()
            
            if not config_files:
                QMessageBox.information(self, "Информация", "Нет сохраненных конфигураций")
                return
            
            filename, _ = QFileDialog.getOpenFileName(
                self, "Загрузить конфигурацию", 
                str(self.config_manager.config_dir),
                "JSON Files (*.json)"
            )
            
            if filename:
                config_data = self.config_manager.load_config(Path(filename).name)
                if config_data:
                    if self.apply_config(config_data):
                        self.log(f"Конфигурация загружена: {filename}")
                        QMessageBox.information(self, "Успех", "Конфигурация успешно загружена!")
                    else:
                        QMessageBox.warning(self, "Ошибка", "Не удалось применить конфигурацию")
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось загрузить конфигурацию")
                    
        except Exception as e:
            self.log(f"Ошибка при загрузке конфигурации: {str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить конфигурацию: {str(e)}")
    
    def load_default_config(self):
        """Загружает конфигурацию по умолчанию при запуске"""
        config_data = self.config_manager.load_config()
        if config_data:
            self.apply_config(config_data)
            self.log("Загружена конфигурация по умолчанию")
        else:
            self.log("Используются настройки по умолчанию")
    
    def log(self, message):
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
    
    def start_clicker(self):
        try:
            if not LINUX_SUPPORT:
                QMessageBox.critical(self, "Ошибка", "Linux-библиотеки не установлены!")
                return
            
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
            
            self.left_clicker = Clicker(
                button="left", 
                acceleration=acceleration, 
                base_interval=base_interval,
                start_interval=start_interval,
                min_interval=min_interval,
                mouse_controller=self.linux_mouse
            )
            self.right_clicker = Clicker(
                button="right", 
                acceleration=acceleration, 
                base_interval=base_interval,
                start_interval=start_interval,
                min_interval=min_interval,
                mouse_controller=self.linux_mouse
            )
            
            # Запускаем слушатель клавиатуры для Linux
            self.keyboard_listener = LinuxKeyboardListener(self.keyboard_callback)
            if not self.keyboard_listener.start():
                QMessageBox.warning(self, "Предупреждение", "Не удалось запустить слушатель клавиатуры")
            
            self.clicker_active = True
            self.clicker_thread = threading.Thread(target=self.clicker_loop, args=(optimization,))
            self.clicker_thread.daemon = True
            self.clicker_thread.start()
            
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.status_label.setText("Кликер активен")
            
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
        
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        
        if hasattr(self, 'clicker_thread') and self.clicker_thread.is_alive():
            self.clicker_thread.join(timeout=1.0)
        
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("Кликер остановлен")
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
                
                time.sleep(0.001 if optimization else 0.0001)
            except Exception as e:
                self.log(f"Ошибка в цикле кликера: {str(e)}")
                break

class Clicker:
    def __init__(self, button, acceleration, base_interval, start_interval, min_interval, mouse_controller):
        self.button = button
        self.acceleration = acceleration
        self.base_interval = base_interval
        self.start_interval = start_interval
        self.min_interval = min_interval
        self.current_interval = start_interval
        self.active = False
        self.mouse_controller = mouse_controller
        self.button_code = 1 if button == "left" else 3  # 1 = left, 3 = right

    def click(self):
        if self.mouse_controller:
            self.mouse_controller.click(self.button_code)
        time.sleep(self.get_interval())
        self.update_interval()

    def get_interval(self):
        return self.current_interval if self.acceleration else self.base_interval

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
    
    # Проверка прав доступа
    if os.geteuid() != 0 and LINUX_SUPPORT:
        print("Предупреждение: Для полной функциональности запустите с sudo")
    
    sys.exit(app.exec_())
