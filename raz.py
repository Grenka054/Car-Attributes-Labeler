import sys
import pandas as pd
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QComboBox, QPushButton, QLineEdit, QMessageBox, QFileDialog
from PyQt5.QtGui import QPixmap, QImage, QIcon, QStandardItemModel, QStandardItem, QColor
from PyQt5.QtCore import Qt
from PIL import Image
import pyperclip
import os

class ImageLabelerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.csv_path = None
        self.df = None
        self.current_index = 0
        self.changes_made = False

        self.setWindowTitle("Атрибуты ТС")
        self.setGeometry(100, 100, 1000, 600)

        # Центральный виджет и layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(5)

        # Кнопка для открытия CSV
        open_button = QPushButton("Открыть CSV")
        open_button.setStyleSheet("font-size: 12px; padding: 5px;")
        open_button.clicked.connect(self.open_csv)
        main_layout.addWidget(open_button)

        # Изображение
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("border: 1px solid #ccc; padding: 5px;")
        main_layout.addWidget(self.image_label)

        # Путь к изображению
        path_layout = QHBoxLayout()
        self.path_label = QLineEdit("Путь: ")
        self.path_label.setReadOnly(True)
        self.path_label.setStyleSheet("font-size: 12px; padding: 2px;")
        path_layout.addWidget(self.path_label)
        copy_button = QPushButton("Копировать")
        copy_button.setStyleSheet("font-size: 12px; padding: 2px;")
        copy_button.clicked.connect(self.copy_path)
        path_layout.addWidget(copy_button)
        main_layout.addLayout(path_layout)

        # Навигация
        nav_layout = QHBoxLayout()
        self.prev_button = QPushButton("◄")
        self.prev_button.setStyleSheet("font-size: 12px; padding: 2px; width: 30px;")
        self.prev_button.clicked.connect(self.prev_image)
        nav_layout.addWidget(self.prev_button)

        self.index_edit = QLineEdit("1")
        self.index_edit.setStyleSheet("font-size: 12px; padding: 2px; width: 50px;")
        self.index_edit.returnPressed.connect(self.go_to_index)
        nav_layout.addWidget(self.index_edit)

        self.next_button = QPushButton("►")
        self.next_button.setStyleSheet("font-size: 12px; padding: 2px; width: 30px;")
        self.next_button.clicked.connect(self.next_image)
        nav_layout.addWidget(self.next_button)
        nav_layout.addStretch()
        main_layout.addLayout(nav_layout)

        # Атрибуты в 5 столбцах
        attributes_layout = QHBoxLayout()
        self.checkboxes = {}

        # Столбец 1: Ориентация
        orientation_layout = QVBoxLayout()
        orientation_label = QLabel("Ориентация:")
        orientation_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        orientation_layout.addWidget(orientation_label)
        orientation_cols = ['orientation_front', 'orientation_back', 'orientation_side']
        orientation_labels = {
            'orientation_front': 'Передняя',
            'orientation_back': 'Задняя',
            'orientation_side': 'Боковая'
        }
        orientation_tooltips = {
            'orientation_front': "Передняя часть: видны фары, решётка радиатора, капот.",
            'orientation_back': "Задняя часть: видны задние фонари, багажник, задний бампер.",
            'orientation_side': "Боковая часть: видны двери, боковые окна, колёса с одной стороны."
        }
        for col in orientation_cols:
            checkbox = QCheckBox(orientation_labels[col])
            checkbox.stateChanged.connect(lambda state, c=col: self.mark_change())
            checkbox.setToolTip(orientation_tooltips[col])
            self.checkboxes[col] = checkbox
            checkbox.setStyleSheet("""
                QCheckBox {
                    spacing: 5px;
                    font-size: 12px;
                    color: #333;
                }
                QCheckBox::indicator {
                    width: 16px;
                    height: 16px;
                }
                QCheckBox::indicator:checked {
                    background-color: #4CAF50;
                    border: 2px solid #388E3C;
                    border-radius: 3px;
                }
                QCheckBox::indicator:unchecked {
                    background-color: #ffffff;
                    border: 2px solid #999;
                    border-radius: 3px;
                }
            """)
            orientation_layout.addWidget(checkbox)
        attributes_layout.addLayout(orientation_layout)

        # Столбец 2: Спецтранспорт
        special_layout = QVBoxLayout()
        special_label = QLabel("Спецтранспорт:")
        special_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        special_layout.addWidget(special_label)
        special_cols = ['special_police', 'special_ambulance', 'special_fire', 'special_military', 'special_rescue', 'special_rosgvardia']
        special_labels = {
            'special_police': 'Полиция',
            'special_ambulance': 'Скорая помощь',
            'special_fire': 'Пожарная охрана',
            'special_military': 'Военная полиция',
            'special_rescue': 'Аварийно-спасательная',
            'special_rosgvardia': 'Росгвардия'
        }
        special_tooltips = {
            'special_police': "Белые или синие машины с синими полосами, надписями «Полиция», «ДПС», «ГИБДД».",
            'special_ambulance': "Машины с красными полосами и крестами, надписями «Скорая помощь» или «Реанимация».",
            'special_fire': "Ярко-красные с белыми полосами машины служб пожарной охраны.",
            'special_military': "Зелёные машины с красными полосами и надписями «Военная полиция».",
            'special_rescue': "Машины с оранжево-синей или красной разметкой, надписями «Спасатели», «МЧС» и др.",
            'special_rosgvardia': "Транспорт с тёмно-красными полосами и надписями «Росгвардия»."
        }
        special_colors = {
            'special_police': ('#2196F3', '#1976D2'),  # Синий
            'special_ambulance': ('#F44336', '#D32F2F'),  # Красный
            'special_fire': ('#FF5722', '#E64A19'),  # Оранжевый
            'special_military': ('#388E3C', '#2E7D32'),  # Тёмно-зелёный
            'special_rescue': ('#00BCD4', '#0097A7'),  # Голубой
            'special_rosgvardia': ('#3F51B5', '#303F9F')  # Тёмно-синий
        }
        for col in special_cols:
            checkbox = QCheckBox(special_labels[col])
            checkbox.stateChanged.connect(lambda state, c=col: self.mark_change())
            checkbox.setToolTip(special_tooltips[col])
            self.checkboxes[col] = checkbox
            bg_color, border_color = special_colors[col]
            checkbox.setStyleSheet(f"""
                QCheckBox {{
                    spacing: 5px;
                    font-size: 12px;
                    color: #333;
                }}
                QCheckBox::indicator {{
                    width: 16px;
                    height: 16px;
                }}
                QCheckBox::indicator:checked {{
                    background-color: {bg_color};
                    border: 2px solid {border_color};
                    border-radius: 3px;
                }}
                QCheckBox::indicator:unchecked {{
                    background-color: #ffffff;
                    border: 2px solid #999;
                    border-radius: 3px;
                }}
            """)
            special_layout.addWidget(checkbox)
        attributes_layout.addLayout(special_layout)

        # Столбец 3: Коммерческий транспорт
        commercial_layout = QVBoxLayout()
        commercial_label = QLabel("Коммерческий транспорт:")
        commercial_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        commercial_layout.addWidget(commercial_label)
        commercial_cols = ['commercial_carsharing', 'commercial_taxi', 'commercial_advertisement']
        commercial_labels = {
            'commercial_carsharing': 'Каршеринг',
            'commercial_taxi': 'Такси',
            'commercial_advertisement': 'Реклама'
        }
        commercial_tooltips = {
            'commercial_carsharing': "Машины с наклейками «Яндекс.Драйв», «Делимобиль» или других сервисов аренды.",
            'commercial_taxi': "Машины с наклейками «Такси», шашечками или световым коробом на крыше.",
            'commercial_advertisement': "Машины с рекламными элементами — наклейки, логотипы компаний, изображения товаров."
        }
        commercial_colors = {
            'commercial_carsharing': ('#9C27B0', '#7B1FA2'),  # Фиолетовый
            'commercial_taxi': ('#FFEB3B', '#FBC02D'),  # Жёлтый
            'commercial_advertisement': ('#E91E63', '#C2185B')  # Розовый
        }
        for col in commercial_cols:
            checkbox = QCheckBox(commercial_labels[col])
            checkbox.stateChanged.connect(lambda state, c=col: self.mark_change())
            checkbox.setToolTip(commercial_tooltips[col])
            self.checkboxes[col] = checkbox
            bg_color, border_color = commercial_colors[col]
            checkbox.setStyleSheet(f"""
                QCheckBox {{
                    spacing: 5px;
                    font-size: 12px;
                    color: #333;
                }}
                QCheckBox::indicator {{
                    width: 16px;
                    height: 16px;
                }}
                QCheckBox::indicator:checked {{
                    background-color: {bg_color};
                    border: 2px solid {border_color};
                    border-radius: 3px;
                }}
                QCheckBox::indicator:unchecked {{
                    background-color: #ffffff;
                    border: 2px solid #999;
                    border-radius: 3px;
                }}
            """)
            commercial_layout.addWidget(checkbox)
        attributes_layout.addLayout(commercial_layout)

        # Столбец 4: Повреждения
        damage_layout = QVBoxLayout()
        damage_label = QLabel("Повреждения:")
        damage_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        damage_layout.addWidget(damage_label)
        damage_cols = ['damage_wing', 'damage_headlight', 'damage_bumper', 'damage_glass', 'damage_door', 'damage_hood', 'damage_trunk']
        damage_labels = {
            'damage_wing': 'Крыло',
            'damage_headlight': 'Фара',
            'damage_bumper': 'Бампер',
            'damage_glass': 'Стекло',
            'damage_door': 'Дверь',
            'damage_hood': 'Капот',
            'damage_trunk': 'Багажник'
        }
        damage_tooltips = {
            'damage_wing': "Часть кузова над колёсами (передними или задними).",
            'damage_headlight': "Передние или задние фонари.",
            'damage_bumper': "Пластиковая или металлическая деталь спереди или сзади машины.",
            'damage_glass': "Лобовое, заднее или боковые окна.",
            'damage_door': "Боковые двери (передние или задние).",
            'damage_hood': "Крышка спереди, закрывает двигатель.",
            'damage_trunk': "Задняя часть, где хранится груз."
        }
        for col in damage_cols:
            checkbox = QCheckBox(damage_labels[col])
            checkbox.stateChanged.connect(lambda state, c=col: self.mark_change())
            checkbox.setToolTip(damage_tooltips[col])
            self.checkboxes[col] = checkbox
            checkbox.setStyleSheet("""
                QCheckBox {
                    spacing: 5px;
                    font-size: 12px;
                    color: #333;
                }
                QCheckBox::indicator {
                    width: 16px;
                    height: 16px;
                }
                QCheckBox::indicator:checked {
                    background-color: #795548;
                    border: 2px solid #5D4037;
                    border-radius: 3px;
                }
                QCheckBox::indicator:unchecked {
                    background-color: #ffffff;
                    border: 2px solid #999;
                    border-radius: 3px;
                }
            """)
            damage_layout.addWidget(checkbox)
        attributes_layout.addLayout(damage_layout)

        # Столбец 5: Остальные атрибуты
        other_layout = QVBoxLayout()
        # ГРЗ и фары
        single_checks_layout = QHBoxLayout()
        license_checkbox = QCheckBox("ГРЗ")
        license_checkbox.stateChanged.connect(lambda state: self.mark_change())
        license_checkbox.setToolTip("Присутствует: номерной знак виден полностью или частично. Отсутствует: номера нет, он закрыт, снят или не виден из-за ракурса.")
        self.checkboxes['license_plate'] = license_checkbox
        license_checkbox.setStyleSheet("""
            QCheckBox {
                spacing: 5px;
                font-size: 12px;
                color: #333;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QCheckBox::indicator:checked {
                background-color: #607D8B;
                border: 2px solid #455A64;
                border-radius: 3px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #ffffff;
                border: 2px solid #999;
                border-radius: 3px;
            }
        """)
        single_checks_layout.addWidget(license_checkbox)

        headlights_checkbox = QCheckBox("Фары включены")
        headlights_checkbox.stateChanged.connect(lambda state: self.mark_change())
        headlights_checkbox.setToolTip("Присутствует: фары включены. Отсутствует: одна или обе не работают.")
        self.checkboxes['headlights_on'] = headlights_checkbox
        headlights_checkbox.setStyleSheet("""
            QCheckBox {
                spacing: 5px;
                font-size: 12px;
                color: #333;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QCheckBox::indicator:checked {
                background-color: #607D8B;
                border: 2px solid #455A64;
                border-radius: 3px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #ffffff;
                border: 2px solid #999;
                border-radius: 3px;
            }
        """)
        single_checks_layout.addWidget(headlights_checkbox)
        other_layout.addLayout(single_checks_layout)

        # Цвет
        color_layout = QHBoxLayout()
        color_label = QLabel("Цвет:")
        color_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        color_layout.addWidget(color_label)
        self.color_combo = QComboBox()
        colors = ['Черный', 'Синий', 'Зеленый', 'Красный', 'Белый', 'Желтый', 'Серый', 'Фиолетовый', 'Бежевый', 'Коричневый', 'Оранжевый']
        color_values = ['#000000', '#0000FF', '#008000', '#FF0000', '#FFFFFF', '#FFFF00', '#808080', '#800080', '#F5F5DC', '#A52A2A', '#FFA500']
        model = QStandardItemModel()
        for color, color_value in zip(colors, color_values):
            item = QStandardItem(color)
            pixmap = QPixmap(16, 16)
            pixmap.fill(QColor(color_value))
            item.setIcon(QIcon(pixmap))
            model.appendRow(item)
        self.color_combo.setModel(model)
        self.color_combo.currentTextChanged.connect(lambda text: self.mark_change())
        self.color_combo.setToolTip("Выберите основной цвет кузова. Если сложно определить, ориентируйтесь на освещение и сравнивайте с примерами (например, auto.ru).")
        color_layout.addWidget(self.color_combo)
        other_layout.addLayout(color_layout)

        # Тип кузова с иконками
        body_layout = QHBoxLayout()
        body_label = QLabel("Тип кузова:")
        body_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        body_layout.addWidget(body_label)
        self.body_combo = QComboBox()
        body_types = ['Седан', 'Хэтчбэк', 'Лифтбэк', 'Внедорожник', 'Универсал', 'Купе', 'Минивэн', 'Пикап', 'Лимузин', 'Фургон', 'Кабриолет']
        body_icons = ['sedan.png', 'hatchback.png', 'liftback.png', 'suv.png', 'wagon.png', 'coupe.png', 'minivan.png', 'pickup-truck.png', 'limousine.png', 'delivery-van.png', 'cabriolet.png']
        model = QStandardItemModel()
        for body_type, icon_name in zip(body_types, body_icons):
            item = QStandardItem(body_type)
            icon_path = os.path.join("icons", icon_name)
            if os.path.exists(icon_path):
                pixmap = QPixmap(icon_path)
                item.setIcon(QIcon(pixmap))
            else:
                QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить иконку: {icon_path}")
            model.appendRow(item)
        self.body_combo.setModel(model)
        self.body_combo.currentTextChanged.connect(lambda text: self.mark_change())
        self.body_combo.setToolTip("Выберите тип кузова. Если не уверены, выберите наиболее подходящий вариант.")
        body_layout.addWidget(self.body_combo)
        other_layout.addLayout(body_layout)

        # Марка и модель
        make_model_layout = QHBoxLayout()
        make_model_label = QLabel("Марка и модель:")
        make_model_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        make_model_layout.addWidget(make_model_label)
        self.make_model_edit = QLineEdit()
        self.make_model_edit.setReadOnly(True)
        self.make_model_edit.setToolTip("Выделите текст для копирования (Ctrl+C).")
        make_model_layout.addWidget(self.make_model_edit)
        other_layout.addLayout(make_model_layout)

        attributes_layout.addLayout(other_layout)
        main_layout.addLayout(attributes_layout)

        # Запуск выбора файла при старте
        self.open_csv()

    def open_csv(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Открыть CSV файл", "", "CSV Files (*.csv)")
        if file_name:
            try:
                self.csv_path = file_name
                bool_cols = [
                    'orientation_front', 'orientation_back', 'orientation_side',
                    'license_plate',
                    'damage_wing', 'damage_headlight', 'damage_bumper', 'damage_glass',
                    'damage_door', 'damage_hood', 'damage_trunk', 'headlights_on',
                    'special_police', 'special_ambulance', 'special_fire', 'special_military',
                    'special_rescue', 'special_rosgvardia',
                    'commercial_carsharing', 'commercial_taxi', 'commercial_advertisement'
                ]
                self.df = pd.read_csv(file_name, dtype={'color': str, 'body_type': str, 'make': str, 'model': str})
                for col in bool_cols:
                    if col in self.df.columns:
                        self.df[col] = self.df[col].fillna(False).astype(bool)
                self.df['color'] = self.df['color'].fillna('Черный')
                self.df['body_type'] = self.df['body_type'].fillna('Седан')
                if 'make' in self.df.columns:
                    self.df['make'] = self.df['make'].fillna('Не указано')
                if 'model' in self.df.columns:
                    self.df['model'] = self.df['model'].fillna('Не указано')
                self.current_index = 0
                self.update_display()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось открыть файл: {str(e)}")
                self.csv_path = None
                self.df = None
        else:
            QMessageBox.warning(self, "Предупреждение", "Файл не выбран. Пожалуйста, выберите CSV файл.")

    def pil_to_qimage(self, pil_image):
        if pil_image.mode == "RGB":
            pil_image = pil_image.convert("RGBA")
        data = pil_image.tobytes("raw", pil_image.mode)
        qim = QImage(data, pil_image.width, pil_image.height, QImage.Format_RGBA8888 if pil_image.mode == "RGBA" else QImage.Format_RGB888)
        return qim

    def update_display(self):
        if self.df is None:
            self.image_label.setText("Пожалуйста, откройте CSV файл")
            return

        row = self.df.iloc[self.current_index]
        image_path = row['image_path']

        try:
            # Получаем директорию CSV-файла
            csv_dir = os.path.dirname(self.csv_path)
            # Формируем полный путь к изображению
            full_image_path = os.path.join(csv_dir, image_path)
            # Нормализуем путь (для кроссплатформенности)
            full_image_path = os.path.normpath(full_image_path)

            # Проверяем существование файла
            if not os.path.exists(full_image_path):
                raise FileNotFoundError(f"Изображение не найдено по пути: {full_image_path}")

            img = Image.open(full_image_path)
            original_width, original_height = img.size
            max_width = 800
            max_height = 400
            scale = min(max_width / original_width, max_height / original_height)
            new_width = int(original_width * scale)
            new_height = int(original_height * scale)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            qim = self.pil_to_qimage(img)
            pixmap = QPixmap.fromImage(qim)
            self.image_label.setPixmap(pixmap)
            self.image_label.setAlignment(Qt.AlignCenter)

            for col, checkbox in self.checkboxes.items():
                value = row[col]
                checkbox.blockSignals(True)
                checkbox.setChecked(bool(value))
                checkbox.blockSignals(False)

            color_value = str(row['color'])
            self.color_combo.blockSignals(True)
            self.color_combo.setCurrentText(color_value)
            self.color_combo.blockSignals(False)

            body_value = str(row['body_type'])
            self.body_combo.blockSignals(True)
            self.body_combo.setCurrentText(body_value)
            self.body_combo.blockSignals(False)

            make = str(row.get('make', 'Не указано'))
            model = str(row.get('model', 'Не указано'))
            make_model_text = "Неизвестно" if make == "Не указано" and model == "Не указано" else f"{make} {model}".strip()
            self.make_model_edit.setText(make_model_text)

            self.path_label.setText(f"Путь: {full_image_path}")
            self.index_edit.setText(str(self.current_index + 1))
            self.changes_made = False

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить изображение: {str(e)}")

    def mark_change(self):
        self.changes_made = True

    def save_changes(self):
        if self.changes_made and self.df is not None:
            row = self.df.iloc[self.current_index].copy()
            for col, checkbox in self.checkboxes.items():
                row[col] = checkbox.isChecked()
            row['color'] = self.color_combo.currentText()
            row['body_type'] = self.body_combo.currentText()
            self.df.iloc[self.current_index] = row
            self.df.to_csv(self.csv_path, index=False)
            self.changes_made = False

    def next_image(self):
        if self.df is not None and self.current_index < len(self.df) - 1:
            self.save_changes()
            self.current_index += 1
            self.update_display()

    def prev_image(self):
        if self.df is not None and self.current_index > 0:
            self.save_changes()
            self.current_index -= 1
            self.update_display()

    def go_to_index(self):
        if self.df is None:
            return
        try:
            new_index = int(self.index_edit.text()) - 1
            if 0 <= new_index < len(self.df):
                self.save_changes()
                self.current_index = new_index
                self.update_display()
            else:
                QMessageBox.warning(self, "Ошибка", "Номер изображения вне диапазона!")
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Введите корректный номер изображения!")

    def copy_path(self):
        path = self.path_label.text().replace("Путь: ", "")
        pyperclip.copy(path)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Right:
            self.next_image()
        elif event.key() == Qt.Key_Left:
            self.prev_image()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ImageLabelerApp()
    window.show()
    sys.exit(app.exec_())