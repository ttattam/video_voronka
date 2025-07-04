import os
from pathlib import Path

# Пути к папкам
PROJECT_ROOT = Path(__file__).parent
INPUT_DIR = PROJECT_ROOT / "input"
OUTPUT_DIR = PROJECT_ROOT / "output"
TEST_DIR = PROJECT_ROOT / "test"

# Параметры кропа (обновленные по просьбе)
GAME_AREA = {
    'x': 207,     # 177 + 30 пикселей слева (обрезаем игру слева)
    'y': 0,
    'width': 895, # 925 - 30 пикселей (компенсируем сдвиг)
    'height': 415
}

# Камера с обрезкой 15 пикселей сверху
CAMERA_AREA = {
    'x': 50,
    'y': 430,     # 415 + 15 пикселей сверху
    'width': 400,
    'height': 290  # 305 - 15 пикселей
}

# Параметры итогового видео - формат соц сетей 9:16
OUTPUT_VIDEO = {
    'width': 1080,
    'height': 1920,  # Стандартный формат соц сетей
    'fps': 30,
    'format': 'mp4'
}

# Компоновка в вертикальном видео
LAYOUT = {
    'camera_position': {'x': 0, 'y': 0},      # Камера сверху
    'game_position': {'x': 0, 'y': 800},      # Игра снизу
    'background_color': 'black'  # Цвет фона для заполнения
}

# Параметры FFmpeg
FFMPEG_PARAMS = {
    'preset': 'medium',
    'crf': 20,
    'codec': 'libx264'
}

# Для тестов - берем фрагмент из центра видео
TEST_FRAGMENT = {
    'duration': 15,  # 15 секунд
    'start_offset': 'center'  # начать с центра видео
}

# Поддерживаемые форматы
SUPPORTED_FORMATS = ['.mov', '.mp4', '.avi', '.mkv']

# Логирование
LOGGING = {
    'log_file': PROJECT_ROOT / 'processing.log',
    'log_level': 'INFO'
}
