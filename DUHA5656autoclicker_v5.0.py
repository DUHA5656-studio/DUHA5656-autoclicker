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

class BeautifulAutoClicker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DUHA5656 Autoclicker")
        self.setGeometry(100, 100, 800, 700)
        
        # Инициализация менеджера конфигураций
        self.config_manager = ConfigManager()
        
        # Настройка тёмно-фиолетовой темы
        self.set_dark_purple_palette()
        
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
        settings_group.setStyleSheet("""
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
        """)
        layout.addWidget(settings_group)
        
        settings_layout = QVBoxLayout(settings_group)
        
        # Настройка ускорения
        self.accel_checkbox = QCheckBox("Включить ускорение кликов")
        self.accel_checkbox.setStyleSheet("color: #e0e0e0;")
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
        self.start_interval.setStyleSheet("""
            QDoubleSpinBox {
                color: #e0e0e0;
                background-color: #2d2b55;
                border: 1px solid #7b1fa2;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        interval_layout.addWidget(self.start_interval)
        
        interval_layout.addWidget(QLabel("Мин. интервал (мс):"))
        self.min_interval = QDoubleSpinBox()
        self.min_interval.setRange(0.001, 1000)
        self.min_interval.setValue(10)
        self.min_interval.setSuffix(" мс")
        self.min_interval.setDecimals(3)
        self.min_interval.setSingleStep(0.001)
        self.min_interval.setStyleSheet("""
            QDoubleSpinBox {
                color: #e0e0e0;
                background-color: #2d2b55;
                border: 1px solid #7b1fa2;
                border-radius: 4px;
                padding: 5px;
            }
        """)
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
        self.base_interval.setStyleSheet("""
            QDoubleSpinBox {
                color: #e0e0e0;
                background-color: #2d2b55;
                border: 1px solid #7b1fa2;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        base_layout.addWidget(self.base_interval)
        settings_layout.addLayout(base_layout)
        
        # Клавиша сброса ускорения
        reset_layout = QHBoxLayout()
        reset_layout.addWidget(QLabel("Клавиша сброса ускорения:"))
        self.reset_key = QComboBox()
        self.reset_key.addItems(["", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12"])
        self.reset_key.setStyleSheet("""
            QComboBox {
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
        """)
        reset_layout.addWidget(self.reset_key)
        settings_layout.addLayout(reset_layout)
        
        # Горячие клавиши
        hotkey_group = QGroupBox("Горячие клавиши")
        hotkey_group.setStyleSheet("""
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
        """)
        layout.addWidget(hotkey_group)
        
        hotkey_layout = QVBoxLayout(hotkey_group)
        
        lkm_layout = QHBoxLayout()
        lkm_layout.addWidget(QLabel("ЛКМ:"))
        self.lkm_key = QComboBox()
        self.lkm_key.addItems(["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12"])
        self.lkm_key.setCurrentText("F6")
        self.lkm_key.setStyleSheet("""
            QComboBox {
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
        """)
        lkm_layout.addWidget(self.lkm_key)
        hotkey_layout.addLayout(lkm_layout)
        
        pkm_layout = QHBoxLayout()
        pkm_layout.addWidget(QLabel("ПКМ:"))
        self.pkm_key = QComboBox()
        self.pkm_key.addItems(["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12"])
        self.pkm_key.setCurrentText("F7")
        self.pkm_key.setStyleSheet("""
            QComboBox {
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
        """)
        pkm_layout.addWidget(self.pkm_key)
        hotkey_layout.addLayout(pkm_layout)
        
        # Оптимизация
        self.optimization = QCheckBox("Включить оптимизацию (меньше КПС, но стабильнее)")
        self.optimization.setChecked(True)
        self.optimization.setStyleSheet("color: #e0e0e0;")
        hotkey_layout.addWidget(self.optimization)
        
        # Кнопки управления конфигурациями
        config_layout = QHBoxLayout()
        
        self.save_config_btn = QPushButton("💾 Сохранить конфиг")
        self.save_config_btn.setStyleSheet(self.get_purple_button_style("#7b1fa2"))
        self.save_config_btn.clicked.connect(self.save_config)
        config_layout.addWidget(self.save_config_btn)
        
        self.load_config_btn = QPushButton("📂 Загрузить конфиг")
        self.load_config_btn.setStyleSheet(self.get_purple_button_style("#9c27b0"))
        self.load_config_btn.clicked.connect(self.load_config)
        config_layout.addWidget(self.load_config_btn)
        
        layout.addLayout(config_layout)
        
        # Кнопки управления
        button_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("🚀 Запуск кликера")
        self.start_btn.setStyleSheet(self.get_purple_button_style("#bb86fc"))
        self.start_btn.clicked.connect(self.start_clicker)
        button_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("⏹️ Остановить")
        self.stop_btn.setStyleSheet(self.get_purple_button_style("#f44336"))
        self.stop_btn.clicked.connect(self.stop_clicker)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn)
        
        layout.addLayout(button_layout)
        
        # Статус
        self.status_label = QLabel("Готов к работе")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            color: #03dac6; 
            font-weight: bold; 
            padding: 10px;
            background-color: #2d2b55;
            border-radius: 8px;
            border: 1px solid #7b1fa2;
        """)
        layout.addWidget(self.status_label)
        
        # Лог
        log_group = QGroupBox("Лог действий")
        log_group.setStyleSheet("""
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
        """)
        layout.addWidget(log_group)
        
        log_layout = QVBoxLayout(log_group)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                color: #e0e0e0;
                background-color: #1e1b2e;
                border: 1px solid #7b1fa2;
                border-radius: 4px;
                font-family: Consolas;
            }
        """)
        self.log_text.setFont(QFont("Consolas", 10))
        log_layout.addWidget(self.log_text)
        
        # Инициализация кликера
        self.clicker_active = False
        self.left_clicker = None
        self.right_clicker = None
        
        # Загрузка конфигурации по умолчанию при запуске
        self.load_default_config()
        
        self.log("Программа инициализирована. Настройте параметры и нажмите 'Запуск кликера'")
    
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
            QLabel {
                color: #e0e0e0;
            }
            QCheckBox {
                color: #e0e0e0;
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 15px;
                height: 15px;
            }
            QCheckBox::indicator:unchecked {
                border: 1px solid #7b1fa2;
                background-color: #2d2b55;
            }
            QCheckBox::indicator:checked {
                background-color: #bb86fc;
                border: 1px solid #7b1fa2;
            }
        """)
    
    def get_purple_button_style(self, color):
        return f"""
            QPushButton {{
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 {color}, stop: 1 #6a1b9a);
                color: white;
                border: none;
                padding: 12px;
                font-weight: bold;
                border-radius: 8px;
                min-width: 120px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #9c27b0, stop: 1 #8e24aa);
            }}
            QPushButton:pressed {{
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #6a1b9a, stop: 1 #4a148c);
            }}
            QPushButton:disabled {{
                background-color: #2d2b55;
                color: #666666;
            }}
        """
    
    def get_current_config(self) -> Dict[str, Any]:
        """Возвращает текущие настройки в виде словаря"""
        return {
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
            
            # Оптимизация
            self.optimization.setChecked(config_data.get("optimization", True))
            
            # Геометрия окна (опционально)
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
            self.status_label.setStyleSheet("""
                color: #03dac6; 
                font-weight: bold; 
                padding: 10px;
                background-color: #2d2b55;
                border-radius: 8px;
                border: 1px solid #7b1fa2;
            """)
            
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
        if hasattr(self, 'clicker_thread') and self.clicker_thread.is_alive():
            self.clicker_thread.join(timeout=1.0)
        
        try:
            keyboard.unhook_all()
        except:
            pass
        
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("Кликер остановлен")
        self.status_label.setStyleSheet("""
            color: #cf6679; 
            font-weight: bold; 
            padding: 10px;
            background-color: #2d2b55;
            border-radius: 8px;
            border: 1px solid #7b1fa2;
        """)
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
