import os
from pathlib import Path

# Пути к папкам
PROJECT_ROOT = Path(__file__).parent
INPUT_DIR = PROJECT_ROOT / "input"
OUTPUT_DIR = PROJECT_ROOT / "output"
TEST_DIR = PROJECT_ROOT / "test"

# Параметры кропа (для гонки с розовой машиной)
GAME_AREA = {
    'x': 147,
    'y': 0,
    'width': 985,
    'height': 415
}

CAMERA_AREA = {
    'x': 0,
    'y': 415,
    'width': 270,
    'height': 305
}

# Параметры итогового видео
OUTPUT_VIDEO = {
    'width': 1080,
    'height': 1920,
    'fps': 30,
    'format': 'mp4'
}

# Компоновка в вертикальном видео
LAYOUT = {
    'game_position': {'x': 0, 'y': 0},  # Игра сверху
    'camera_position': {'x': 0, 'y': 447},  # Камера снизу
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