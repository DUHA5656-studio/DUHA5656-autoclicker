# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import time
import threading
import json
from pathlib import Path
from typing import Any, Dict, Optional, List, Tuple
import logging

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
                             QSpinBox, QDoubleSpinBox, QComboBox, QFileDialog)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor
import keyboard
import mouse

# Скрываем консольное окно (для Windows)
if os.name == 'nt':
    import ctypes
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

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

class MacroManager:
    """Менеджер для работы с макросами"""
    
    def __init__(self, macro_dir: str = "macros"):
        self.macro_dir = Path(macro_dir)
        self._ensure_macro_dir()
        
    def _ensure_macro_dir(self) -> None:
        """Создает директорию для макросов, если она не существует"""
        self.macro_dir.mkdir(exist_ok=True, parents=True)
    
    def save_macro(self, events: List[Dict], filename: str) -> bool:
        """Сохраняет макрос в файл"""
        try:
            macro_path = self.macro_dir / filename
            with open(macro_path, 'w', encoding='utf-8') as f:
                json.dump(events, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            logging.error(f"Ошибка сохранения макроса: {e}")
            return False
    
    def load_macro(self, filename: str) -> Optional[List[Dict]]:
        """Загружает макрос из файла"""
        try:
            macro_path = self.macro_dir / filename
            with open(macro_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Ошибка загрузки макроса: {e}")
            return None
    
    def get_macro_list(self) -> list:
        """Возвращает список доступных макросов"""
        macro_files = []
        for file in self.macro_dir.glob("*.json"):
            macro_files.append(file.name)
        return sorted(macro_files)

class MacroRecorder:
    """Класс для записи и воспроизведения макросов"""
    
    def __init__(self):
        self.recording = False
        self.playing = False
        self.paused = False
        self.events = []
        self.start_time = 0
        self.thread = None
    
    def start_recording(self):
        """Начинает запись макроса"""
        self.recording = True
        self.events = []
        self.start_time = time.time()
    
    def stop_recording(self):
        """Останавливает запись макроса"""
        self.recording = False
    
    def record_event(self, event_type: str, button: str = None, x: int = None, y: int = None):
        """Записывает событие мыши"""
        if self.recording:
            timestamp = time.time() - self.start_time
            self.events.append({
                'type': event_type,
                'button': button,
                'x': x,
                'y': y,
                'timestamp': timestamp
            })
    
    def play_macro(self, repeat: bool = False):
        """Воспроизводит записанный макрос"""
        if not self.events:
            return
        
        self.playing = True
        self.paused = False
        
        def play_thread():
            while self.playing and (repeat or not self.paused):
                start_time = time.time()
                for event in self.events:
                    if not self.playing or self.paused:
                        break
                    
                    # Ждем нужное время перед выполнением события
                    while time.time() - start_time < event['timestamp']:
                        if not self.playing or self.paused:
                            break
                        time.sleep(0.001)
                    
                    if not self.playing or self.paused:
                        break
                    
                    # Выполняем событие
                    if event['type'] == 'click':
                        mouse.click(event['button'])
                    elif event['type'] == 'press':
                        mouse.press(event['button'])
                    elif event['type'] == 'release':
                        mouse.release(event['button'])
                    elif event['type'] == 'move':
                        mouse.move(event['x'], event['y'])
                
                if not repeat:
                    break
            
            self.playing = False
            self.paused = False
        
        self.thread = threading.Thread(target=play_thread)
        self.thread.daemon = True
        self.thread.start()
    
    def pause_macro(self):
        """Приостанавливает воспроизведение макроса"""
        self.paused = True
    
    def resume_macro(self):
        """Возобновляет воспроизведение макроса"""
        self.paused = False
    
    def stop_macro(self):
        """Останавливает воспроизведение макроса"""
        self.playing = False
        self.paused = False

class BeautifulAutoClicker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DUHA5656 Autoclicker")
        
        # Устанавливаем минимальный размер окна
        self.setMinimumSize(600, 500)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной layout
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Заголовок
        title = QLabel("DUHA5656 AUTOCLICKER")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
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
        
        # Макрос горячие клавиши
        macro_hotkey_layout = QHBoxLayout()
        macro_hotkey_layout.addWidget(QLabel("Воспроизвести макрос:"))
        self.play_macro_key = QComboBox()
        self.play_macro_key.addItems(["", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12"])
        macro_hotkey_layout.addWidget(self.play_macro_key)
        hotkey_layout.addLayout(macro_hotkey_layout)
        
        pause_macro_layout = QHBoxLayout()
        pause_macro_layout.addWidget(QLabel("Пауза макроса:"))
        self.pause_macro_key = QComboBox()
        self.pause_macro_key.addItems(["", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12"])
        pause_macro_layout.addWidget(self.pause_macro_key)
        hotkey_layout.addLayout(pause_macro_layout)
        
        stop_macro_layout = QHBoxLayout()
        stop_macro_layout.addWidget(QLabel("Остановить макрос:"))
        self.stop_macro_key = QComboBox()
        self.stop_macro_key.addItems(["", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12"])
        stop_macro_layout.addWidget(self.stop_macro_key)
        hotkey_layout.addLayout(stop_macro_layout)
        
        # Горячие клавиши записи макроса
        record_macro_layout = QHBoxLayout()
        record_macro_layout.addWidget(QLabel("Начать запись макроса:"))
        self.record_macro_key = QComboBox()
        self.record_macro_key.addItems(["", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12"])
        record_macro_layout.addWidget(self.record_macro_key)
        hotkey_layout.addLayout(record_macro_layout)
        
        stop_record_layout = QHBoxLayout()
        stop_record_layout.addWidget(QLabel("Остановить запись:"))
        self.stop_record_key = QComboBox()
        self.stop_record_key.addItems(["", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12"])
        stop_record_layout.addWidget(self.stop_record_key)
        hotkey_layout.addLayout(stop_record_layout)
        
        pause_record_layout = QHBoxLayout()
        pause_record_layout.addWidget(QLabel("Пауза записи:"))
        self.pause_record_key = QComboBox()
        self.pause_record_key.addItems(["", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12"])
        pause_record_layout.addWidget(self.pause_record_key)
        hotkey_layout.addLayout(pause_record_layout)
        
        # Оптимизация
        self.optimization = QCheckBox("Включить оптимизацию (меньше КПС, но стабильнее)")
        self.optimization.setChecked(True)
        hotkey_layout.addWidget(self.optimization)
        
        layout.addWidget(hotkey_group)
        
        # Управление макросами
        macro_group = QGroupBox("Управление макросами")
        macro_layout = QVBoxLayout(macro_group)
        
        # Кнопки записи макроса
        record_buttons_layout = QHBoxLayout()
        self.record_start_btn = QPushButton("🔴 Начать запись макроса")
        self.record_start_btn.clicked.connect(self.start_macro_recording)
        record_buttons_layout.addWidget(self.record_start_btn)
        
        self.record_stop_btn = QPushButton("⏹️ Остановить запись")
        self.record_stop_btn.clicked.connect(self.stop_macro_recording)
        self.record_stop_btn.setEnabled(False)
        record_buttons_layout.addWidget(self.record_stop_btn)
        macro_layout.addLayout(record_buttons_layout)
        
        # Кнопки воспроизведения макроса
        play_buttons_layout = QHBoxLayout()
        self.play_macro_btn = QPushButton("▶️ Воспроизвести макрос")
        self.play_macro_btn.clicked.connect(self.play_macro)
        play_buttons_layout.addWidget(self.play_macro_btn)
        
        self.pause_macro_btn = QPushButton("⏸️ Пауза макроса")
        self.pause_macro_btn.clicked.connect(self.pause_macro)
        self.pause_macro_btn.setEnabled(False)
        play_buttons_layout.addWidget(self.pause_macro_btn)
        
        self.stop_macro_btn = QPushButton("⏹️ Остановить макрос")
        self.stop_macro_btn.clicked.connect(self.stop_macro)
        self.stop_macro_btn.setEnabled(False)
        play_buttons_layout.addWidget(self.stop_macro_btn)
        macro_layout.addLayout(play_buttons_layout)
        
        # Сохранение/загрузка макроса
        macro_save_load_layout = QHBoxLayout()
        self.save_macro_btn = QPushButton("💾 Сохранить макрос")
        self.save_macro_btn.clicked.connect(self.save_macro)
        macro_save_load_layout.addWidget(self.save_macro_btn)
        
        self.load_macro_btn = QPushButton("📂 Загрузить макрос")
        self.load_macro_btn.clicked.connect(self.load_macro)
        macro_save_load_layout.addWidget(self.load_macro_btn)
        macro_layout.addLayout(macro_save_load_layout)
        
        layout.addWidget(macro_group)
        
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
        
        # Инициализация кликера
        self.clicker_active = False
        self.left_clicker = None
        self.right_clicker = None
        
        # Хуки для записи мыши
        self.mouse_hooks = []
        
        # Инициализация менеджера конфигураций
        self.config_manager = ConfigManager()
        
        # Инициализация менеджера макросов
        self.macro_manager = MacroManager()
        
        # Инициализация макрорекордера
        self.macro_recorder = MacroRecorder()
        
        # Применяем тему по умолчанию
        self.apply_theme("purple")
        
        # Загрузка конфигурации по умолчанию при запуске
        self.load_default_config()
        
        # Устанавливаем начальную геометрию окна (минимальный размер)
        self.setGeometry(100, 100, 600, 1000)
    
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
        dark_purple_palette.setColor(QPalette.Window, QColor(30, 27, 46))        # Основной фон
        dark_purple_palette.setColor(QPalette.WindowText, QColor(224, 224, 224)) # Текст
        dark_purple_palette.setColor(QPalette.Base, QColor(45, 43, 85))          # Фон полей ввода
        dark_purple_palette.setColor(QPalette.AlternateBase, QColor(59, 48, 84)) # Альтернативный фон
        dark_purple_palette.setColor(QPalette.ToolTipBase, QColor(187, 134, 252))# Подсказки
        dark_purple_palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))      # Текст подсказок
        dark_purple_palette.setColor(QPalette.Text, QColor(224, 224, 224))       # Основной текст
        dark_purple_palette.setColor(QPalette.Button, QColor(59, 48, 84))        # Кнопки
        dark_purple_palette.setColor(QPalette.ButtonText, QColor(224, 224, 224)) # Текст кнопок
        dark_purple_palette.setColor(QPalette.BrightText, QColor(255, 255, 255)) # Яркий текст
        dark_purple_palette.setColor(QPalette.Link, QColor(156, 39, 176))        # Ссылки
        dark_purple_palette.setColor(QPalette.Highlight, QColor(123, 31, 162))   # Выделение
        dark_purple_palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255)) # Текст выделения
        
        QApplication.setPalette(dark_purple_palette)
        
        # Дополнительные стили для приложения
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1b2e;
            }
        """)
    
    def set_pink_white_palette(self):
        """Устанавливает розово-белую цветовую палитру"""
        pink_white_palette = QPalette()
        
        # Основные цвета
        pink_white_palette.setColor(QPalette.Window, QColor(255, 240, 245))      # Основной фон
        pink_white_palette.setColor(QPalette.WindowText, QColor(75, 0, 130))     # Текст
        pink_white_palette.setColor(QPalette.Base, QColor(255, 255, 255))        # Фон полей ввода
        pink_white_palette.setColor(QPalette.AlternateBase, QColor(255, 228, 225)) # Альтернативный фон
        pink_white_palette.setColor(QPalette.ToolTipBase, QColor(255, 182, 193)) # Подсказки
        pink_white_palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))       # Текст подсказок
        pink_white_palette.setColor(QPalette.Text, QColor(75, 0, 130))           # Основной текст
        pink_white_palette.setColor(QPalette.Button, QColor(255, 182, 193))      # Кнопки
        pink_white_palette.setColor(QPalette.ButtonText, QColor(75, 0, 130))     # Текст кнопок
        pink_white_palette.setColor(QPalette.BrightText, QColor(255, 20, 147))   # Яркий текст
        pink_white_palette.setColor(QPalette.Link, QColor(199, 21, 133))         # Ссылки
        pink_white_palette.setColor(QPalette.Highlight, QColor(255, 105, 180))   # Выделение
        pink_white_palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255)) # Текст выделения
        
        QApplication.setPalette(pink_white_palette)
        
        # Дополнительные стили для приложения
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
        # Заголовок
        self.findChild(QLabel, None).setStyleSheet("color: #bb86fc; margin: 10px;")
        
        # Группы
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
        for group in self.findChildren(QGroupBox):
            group.setStyleSheet(group_style)
        
        # Текстовые поля и выпадающие списки
        input_style = """
            QComboBox, QDoubleSpinBox, QTextEdit {
                color: #e0e0e0;
                background-color: #2d2b55;
                border: 1px solid #7b1fa2;
                border-radius: 4px;
                padding: 5px;
            }
            QComboBox QAbstractItemView {
                color: #e0e0e0;
                background-color: #2d2b55;
                selection-background-color: #7b1fa2;
            }
        """
        for widget in self.findChildren((QComboBox, QDoubleSpinBox)):
            widget.setStyleSheet(input_style)
        
        # Чекбоксы
        checkbox_style = "color: #e0e0e0; spacing: 5px;"
        for checkbox in self.findChildren(QCheckBox):
            checkbox.setStyleSheet(checkbox_style)
        
        # Кнопки (без градиента)
        button_style = """
            QPushButton {
                background-color: %s;
                color: %s;
                border: 2px solid %s;
                padding: 8px;
                font-weight: bold;
                border-radius: 6px;
                min-width: 100px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: %s;
                border-color: %s;
            }
            QPushButton:pressed {
                background-color: %s;
                border-color: %s;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
                border-color: #999999;
            }
        """
        
        # Применяем стили к кнопкам
        self.save_config_btn.setStyleSheet(button_style % (
            "#7b1fa2", "#ffffff", "#6a1b9a", 
            "#9c27b0", "#9c27b0", "#6a1b9a", "#6a1b9a"
        ))
        self.load_config_btn.setStyleSheet(button_style % (
            "#9c27b0", "#ffffff", "#7b1fa2",
            "#bb86fc", "#bb86fc", "#7b1fa2", "#7b1fa2"
        ))
        self.start_btn.setStyleSheet(button_style % (
            "#4CAF50", "#ffffff", "#45a049",
            "#66BB6A", "#66BB6A", "#45a049", "#45a049"
        ))
        self.stop_btn.setStyleSheet(button_style % (
            "#f44336", "#ffffff", "#d32f2f",
            "#ef5350", "#ef5350", "#d32f2f", "#d32f2f"
        ))
        self.record_start_btn.setStyleSheet(button_style % (
            "#f44336", "#ffffff", "#d32f2f",
            "#ef5350", "#ef5350", "#d32f2f", "#d32f2f"
        ))
        self.record_stop_btn.setStyleSheet(button_style % (
            "#f44336", "#ffffff", "#d32f2f",
            "#ef5350", "#ef5350", "#d32f2f", "#d32f2f"
        ))
        self.play_macro_btn.setStyleSheet(button_style % (
            "#4CAF50", "#ffffff", "#45a049",
            "#66BB6A", "#66BB6A", "#45a049", "#45a049"
        ))
        self.pause_macro_btn.setStyleSheet(button_style % (
            "#FF9800", "#ffffff", "#F57C00",
            "#FFA726", "#FFA726", "#F57C00", "#F57C00"
        ))
        self.stop_macro_btn.setStyleSheet(button_style % (
            "#f44336", "#ffffff", "#d32f2f",
            "#ef5350", "#ef5350", "#d32f2f", "#d32f2f"
        ))
        self.save_macro_btn.setStyleSheet(button_style % (
            "#2196F3", "#ffffff", "#1976D2",
            "#42A5F5", "#42A5F5", "#1976D2", "#1976D2"
        ))
        self.load_macro_btn.setStyleSheet(button_style % (
            "#2196F3", "#ffffff", "#1976D2",
            "#42A5F5", "#42A5F5", "#1976D2", "#1976D2"
        ))
        
        # Статус
        self.status_label.setStyleSheet("""
            color: #03dac6; 
            font-weight: bold; 
            padding: 8px;
            background-color: #2d2b55;
            border-radius: 6px;
            border: 1px solid #7b1fa2;
        """)
    
    def apply_pink_styles(self):
        """Применяет стили для розовой темы"""
        # Заголовок
        self.findChild(QLabel, None).setStyleSheet("color: #ff69b4; margin: 10px;")
        
        # Группы
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
        for group in self.findChildren(QGroupBox):
            group.setStyleSheet(group_style)
        
        # Текстовые поля и выпадающие списки
        input_style = """
            QComboBox, QDoubleSpinBox, QTextEdit {
                color: #4b0082;
                background-color: #ffffff;
                border: 1px solid #ffb6c1;
                border-radius: 4px;
                padding: 5px;
            }
            QComboBox QAbstractItemView {
                color: #4b0082;
                background-color: #ffffff;
                selection-background-color: #ffb6c1;
            }
        """
        for widget in self.findChildren((QComboBox, QDoubleSpinBox)):
            widget.setStyleSheet(input_style)
        
        # Чекбоксы
        checkbox_style = "color: #4b0082; spacing: 5px;"
        for checkbox in self.findChildren(QCheckBox):
            checkbox.setStyleSheet(checkbox_style)
        
        # Кнопки (без градиента)
        button_style = """
            QPushButton {
                background-color: %s;
                color: %s;
                border: 2px solid %s;
                padding: 8px;
                font-weight: bold;
                border-radius: 6px;
                min-width: 100px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: %s;
                border-color: %s;
            }
            QPushButton:pressed {
                background-color: %s;
                border-color: %s;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
                border-color: #999999;
            }
        """
        
        # Применяем стили к кнопкам
        self.save_config_btn.setStyleSheet(button_style % (
            "#ff69b4", "#ffffff", "#ff1493", 
            "#ff85a2", "#ff85a2", "#ff1493", "#ff1493"
        ))
        self.load_config_btn.setStyleSheet(button_style % (
            "#ff85a2", "#ffffff", "#ff69b4",
            "#ffa7b6", "#ffa7b6", "#ff69b4", "#ff69b4"
        ))
        self.start_btn.setStyleSheet(button_style % (
            "#66BB6A", "#ffffff", "#4CAF50",
            "#81C784", "#81C784", "#4CAF50", "#4CAF50"
        ))
        self.stop_btn.setStyleSheet(button_style % (
            "#ff6b6b", "#ffffff", "#ff4757",
            "#ff8f8f", "#ff8f8f", "#ff4757", "#ff4757"
        ))
        self.record_start_btn.setStyleSheet(button_style % (
            "#ff6b6b", "#ffffff", "#ff4757",
            "#ff8f8f", "#ff8f8f", "#ff4757", "#ff4757"
        ))
        self.record_stop_btn.setStyleSheet(button_style % (
            "#ff6b6b", "#ffffff", "#ff4757",
            "#ff8f8f", "#ff8f8f", "#ff4757", "#ff4757"
        ))
        self.play_macro_btn.setStyleSheet(button_style % (
            "#66BB6A", "#ffffff", "#4CAF50",
            "#81C784", "#81C784", "#4CAF50", "#4CAF50"
        ))
        self.pause_macro_btn.setStyleSheet(button_style % (
            "#FFA726", "#ffffff", "#FF9800",
            "#FFB74D", "#FFB74D", "#FF9800", "#FF9800"
        ))
        self.stop_macro_btn.setStyleSheet(button_style % (
            "#ff6b6b", "#ffffff", "#ff4757",
            "#ff8f8f", "#ff8f8f", "#ff4757", "#ff4757"
        ))
        self.save_macro_btn.setStyleSheet(button_style % (
            "#42A5F5", "#ffffff", "#2196F3",
            "#64B5F6", "#64B5F6", "#2196F3", "#2196F3"
        ))
        self.load_macro_btn.setStyleSheet(button_style % (
            "#42A5F5", "#ffffff", "#2196F3",
            "#64B5F6", "#64B5F6", "#2196F3", "#2196F3"
        ))
        
        # Статус
        self.status_label.setStyleSheet("""
            color: #ff1493; 
            font-weight: bold; 
            padding: 8px;
            background-color: #ffffff;
            border-radius: 6px;
            border: 1px solid #ffb6c1;
        """)
    
    def change_theme(self):
        """Обработчик изменения темы"""
        theme_data = self.theme_combo.currentData()
        if theme_data:
            self.apply_theme(theme_data)
    
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
            "play_macro_key": self.play_macro_key.currentText(),
            "pause_macro_key": self.pause_macro_key.currentText(),
            "stop_macro_key": self.stop_macro_key.currentText(),
            "record_macro_key": self.record_macro_key.currentText(),
            "stop_record_key": self.stop_record_key.currentText(),
            "pause_record_key": self.pause_record_key.currentText(),
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
            # Тема оформления
            theme = config_data.get("theme", "purple")
            self.apply_theme(theme)
            
            # Устанавливаем выбранную тему в комбобокс
            index = self.theme_combo.findData(theme)
            if index >= 0:
                self.theme_combo.setCurrentIndex(index)
            
            # Основные настройки
            self.accel_checkbox.setChecked(config_data.get("acceleration", False))
            self.start_interval.setValue(config_data.get("start_interval", 500))
            self.min_interval.setValue(config_data.get("min_interval", 10))
            self.base_interval.setValue(config_data.get("base_interval", 100))
            
            # Клавиши
            reset_key = config_data.get("reset_key", "")
            if reset_key in [self.reset_key.itemText(i) for i in range(self.reset_key.count())]:
                self.reset_key.setCurrentText(reset_key)
            
            lkm_key = config_data.get("lkm_key", "F6")
            if lkm_key in [self.lkm_key.itemText(i) for i in range(self.lkm_key.count())]:
                self.lkm_key.setCurrentText(lkm_key)
            
            pkm_key = config_data.get("pkm_key", "F7")
            if pkm_key in [self.pkm_key.itemText(i) for i in range(self.pkm_key.count())]:
                self.pkm_key.setCurrentText(pkm_key)
            
            # Макрос клавиши
            play_macro_key = config_data.get("play_macro_key", "")
            if play_macro_key in [self.play_macro_key.itemText(i) for i in range(self.play_macro_key.count())]:
                self.play_macro_key.setCurrentText(play_macro_key)
            
            pause_macro_key = config_data.get("pause_macro_key", "")
            if pause_macro_key in [self.pause_macro_key.itemText(i) for i in range(self.pause_macro_key.count())]:
                self.pause_macro_key.setCurrentText(pause_macro_key)
            
            stop_macro_key = config_data.get("stop_macro_key", "")
            if stop_macro_key in [self.stop_macro_key.itemText(i) for i in range(self.stop_macro_key.count())]:
                self.stop_macro_key.setCurrentText(stop_macro_key)
            
            # Клавиши записи макроса
            record_macro_key = config_data.get("record_macro_key", "")
            if record_macro_key in [self.record_macro_key.itemText(i) for i in range(self.record_macro_key.count())]:
                self.record_macro_key.setCurrentText(record_macro_key)
            
            stop_record_key = config_data.get("stop_record_key", "")
            if stop_record_key in [self.stop_record_key.itemText(i) for i in range(self.stop_record_key.count())]:
                self.stop_record_key.setCurrentText(stop_record_key)
            
            pause_record_key = config_data.get("pause_record_key", "")
            if pause_record_key in [self.pause_record_key.itemText(i) for i in range(self.pause_record_key.count())]:
                self.pause_record_key.setCurrentText(pause_record_key)
            
            # Оптимизация
            self.optimization.setChecked(config_data.get("optimization", True))
            
            # Геометрия окна (опционально)
            geometry = config_data.get("window_geometry")
            if geometry:
                self.setGeometry(
                    geometry.get("x", 100),
                    geometry.get("y", 100),
                    geometry.get("width", 600),
                    geometry.get("height", 500)
                )
            
            return True
            
        except Exception as e:
            return False
    
    def save_config(self):
        """Сохраняет текущую конфигурацию в файл"""
        try:
            config_data = self.get_current_config()
            
            # Запрос имени файла у пользователя
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
                    QMessageBox.information(self, "Успех", "Конфигурация успешно сохранена!")
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось сохранить конфигурацию")
                    
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить конфигурацию: {str(e)}")
    
    def load_config(self):
        """Загружает конфигурацию из файла"""
        try:
            # Получаем список доступных конфигураций
            config_files = self.config_manager.get_config_list()
            
            if not config_files:
                QMessageBox.information(self, "Информация", "Нет сохраненных конфигураций")
                return
            
            # Запрос файла у пользователя
            filename, _ = QFileDialog.getOpenFileName(
                self, "Загрузить конфигурацию", 
                str(self.config_manager.config_dir),
                "JSON Files (*.json)"
            )
            
            if filename:
                config_data = self.config_manager.load_config(Path(filename).name)
                if config_data:
                    if self.apply_config(config_data):
                        QMessageBox.information(self, "Успех", "Конфигурация успешно загружена!")
                    else:
                        QMessageBox.warning(self, "Ошибка", "Не удалось применить конфигурацию")
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось загрузить конфигурацию")
                    
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить конфигурацию: {str(e)}")
    
    def load_default_config(self):
        """Загружает конфигурацию по умолчанию при запуске"""
        config_data = self.config_manager.load_config()
        if config_data:
            self.apply_config(config_data)
    
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
            
            # Макрос горячие клавиши
            play_macro_key = self.play_macro_key.currentText()
            pause_macro_key = self.pause_macro_key.currentText()
            stop_macro_key = self.stop_macro_key.currentText()
            
            # Горячие клавиши записи макроса
            record_macro_key = self.record_macro_key.currentText()
            stop_record_key = self.stop_record_key.currentText()
            pause_record_key = self.pause_record_key.currentText()
            
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
            
            # Макрос горячие клавиши
            if play_macro_key:
                keyboard.add_hotkey(play_macro_key, self.play_macro)
            if pause_macro_key:
                keyboard.add_hotkey(pause_macro_key, self.pause_macro)
            if stop_macro_key:
                keyboard.add_hotkey(stop_macro_key, self.stop_macro)
            
            # Горячие клавиши записи макроса
            if record_macro_key:
                keyboard.add_hotkey(record_macro_key, self.start_macro_recording)
            if stop_record_key:
                keyboard.add_hotkey(stop_record_key, self.stop_macro_recording)
            if pause_record_key:
                keyboard.add_hotkey(pause_record_key, self.toggle_macro_recording)
            
            self.clicker_active = True
            self.clicker_thread = threading.Thread(target=self.clicker_loop, args=(optimization,))
            self.clicker_thread.daemon = True
            self.clicker_thread.start()
            
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.status_label.setText("Кликер активен")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось запустить кликер: {str(e)}")
    
    def stop_clicker(self):
        self.clicker_active = False
        if hasattr(self, 'clicker_thread') and self.clicker_thread.is_alive():
            self.clicker_thread
        
        try:
            keyboard.unhook_all()
        except:
            pass
        
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("Кликер остановлен")
    
    def toggle_left_clicker(self):
        if self.left_clicker:
            self.left_clicker.active = not self.left_clicker.active
            status = "ВКЛ" if self.left_clicker.active else "ВЫКЛ"
            self.status_label.setText(f"ЛКМ {status}")
    
    def toggle_right_clicker(self):
        if self.right_clicker:
            self.right_clicker.active = not self.right_clicker.active
            status = "ВКЛ" if self.right_clicker.active else "ВЫКЛ"
            self.status_label.setText(f"ПКМ {status}")
    
    def reset_acceleration(self):
        if self.left_clicker:
            self.left_clicker.reset_interval()
        if self.right_clicker:
            self.right_clicker.reset_interval()
        self.status_label.setText("Ускорение сброшено")
    
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
            except:
                break
    
    def start_macro_recording(self):
        """Начинает запись макроса"""
        try:
            if self.macro_recorder.recording:
                return
                
            self.macro_recorder.start_recording()
            
            # Устанавливаем хуки для записи мыши
            self.mouse_hooks = [
                mouse.hook(self.mouse_callback)
            ]
            
            self.record_start_btn.setEnabled(False)
            self.record_stop_btn.setEnabled(True)
            self.status_label.setText("Запись макроса...")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось начать запись: {str(e)}")
    
    def stop_macro_recording(self):
        """Останавливает запись макроса"""
        try:
            if not self.macro_recorder.recording:
                return
                
            self.macro_recorder.stop_recording()
            
            # Убираем хуки
            for hook in self.mouse_hooks:
                mouse.unhook(hook)
            self.mouse_hooks = []
            
            self.record_start_btn.setEnabled(True)
            self.record_stop_btn.setEnabled(False)
            self.status_label.setText("Запись завершена")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось остановить запись: {str(e)}")
    
    def toggle_macro_recording(self):
        """Переключает запись макроса (старт/стоп)"""
        if self.macro_recorder.recording:
            self.stop_macro_recording()
        else:
            self.start_macro_recording()
    
    def mouse_callback(self, event):
        """Callback для записи событий мыши"""
        if isinstance(event, mouse.ButtonEvent):
            if event.event_type == 'down':
                self.macro_recorder.record_event('press', event.button.name)
            elif event.event_type == 'up':
                self.macro_recorder.record_event('release', event.button.name)
        elif isinstance(event, mouse.MoveEvent):
            self.macro_recorder.record_event('move', x=event.x, y=event.y)
        elif isinstance(event, mouse.WheelEvent):
            # Пропускаем события колесика для простоты
            pass
    
    def play_macro(self):
        """Воспроизводит записанный макрос"""
        try:
            if not self.macro_recorder.events:
                QMessageBox.warning(self, "Предупреждение", "Нет записанных событий для воспроизведения")
                return
            
            self.macro_recorder.play_macro()
            
            self.play_macro_btn.setEnabled(False)
            self.pause_macro_btn.setEnabled(True)
            self.stop_macro_btn.setEnabled(True)
            self.status_label.setText("Воспроизведение макроса")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось воспроизвести макрос: {str(e)}")
    
    def pause_macro(self):
        """Приостанавливает воспроизведение макроса"""
        try:
            if self.macro_recorder.paused:
                self.macro_recorder.resume_macro()
                self.status_label.setText("Воспроизведение макроса")
                self.pause_macro_btn.setText("⏸️ Пауза макроса")
            else:
                self.macro_recorder.pause_macro()
                self.status_label.setText("Макрос на паузе")
                self.pause_macro_btn.setText("▶️ Возобновить")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось приостановить макрос: {str(e)}")
    
    def stop_macro(self):
        """Останавливает воспроизведение макроса"""
        try:
            self.macro_recorder.stop_macro()
            
            self.play_macro_btn.setEnabled(True)
            self.pause_macro_btn.setEnabled(False)
            self.stop_macro_btn.setEnabled(False)
            self.pause_macro_btn.setText("⏸️ Пауза макроса")
            self.status_label.setText("Макрос остановлен")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось остановить макрос: {str(e)}")
    
    def save_macro(self):
        """Сохраняет макрос в файл"""
        try:
            if not self.macro_recorder.events:
                QMessageBox.warning(self, "Предупреждение", "Нет записанных событий для сохранения")
                return
            
            filename, _ = QFileDialog.getSaveFileName(
                self, "Сохранить макрос", 
                str(self.macro_manager.macro_dir),
                "JSON Files (*.json)"
            )
            
            if filename:
                if not filename.endswith('.json'):
                    filename += '.json'
                
                if self.macro_manager.save_macro(self.macro_recorder.events, Path(filename).name):
                    QMessageBox.information(self, "Успех", "Макрос успешно сохранен!")
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось сохранить макрос")
                    
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить макрос: {str(e)}")
    
    def load_macro(self):
        """Загружает макрос из файла"""
        try:
            filename, _ = QFileDialog.getOpenFileName(
                self, "Загрузить макрос", 
                str(self.macro_manager.macro_dir),
                "JSON Files (*.json)"
            )
            
            if filename:
                events = self.macro_manager.load_macro(Path(filename).name)
                if events is not None:
                    self.macro_recorder.events = events
                    QMessageBox.information(self, "Успех", "Макрос успешно загружен!")
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось загрузить макрос")
                    
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить макрос: {str(e)}")

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
