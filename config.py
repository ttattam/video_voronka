import os
from pathlib import Path

# Пути к папкам
PROJECT_ROOT = Path(__file__).parent
INPUT_DIR = PROJECT_ROOT / "input"
OUTPUT_DIR = PROJECT_ROOT / "output"
TEST_DIR = PROJECT_ROOT / "test"

# Области для обрезки из горизонтального видео
GAME_AREA = {
    'x': 160, 'y': 0, 'width': 840, 'height': 455
}

CAMERA_AREA = {
    'x': 0, 'y': 455, 'width': 470, 'height': 265
}

SUBTITLES_AREA = {
    'x': 479, 'y': 455, 'width': 801, 'height': 265
}

# Параметры итогового видео - формат соц сетей 9:16
OUTPUT_VIDEO = {
    'width': 1080,
    'height': 1920,  # Стандартный формат соц сетей
    'fps': 30,
    'format': 'mp4'
}

# Расположение областей в вертикальном видео
LAYOUT = {
    'camera_position': {'x': 0, 'y': 0},      # Камера сверху, пропорциональный размер
    'game_position': {'x': 120, 'y': 596},    # Игра под камерой, центрирована (1080-840)/2=120
    'subtitles_position': {'x': 0, 'y': 1051}  # Субтитры внизу (596 + 455)
}

# Параметры FFmpeg
FFMPEG_PARAMS = {
    'preset': 'ultrafast',
    'crf': 0,
    'codec': 'libx264'
}

# Для тестов - берем фрагмент из случайного места
TEST_FRAGMENT = {
    'duration': 15,  # 15 секунд
    'start_offset': 'random'  # начать со случайного места
}

# Поддерживаемые форматы
SUPPORTED_FORMATS = ['.mov', '.mp4', '.avi', '.mkv']

# Логирование
LOGGING = {
    'log_file': PROJECT_ROOT / 'processing.log',
    'log_level': 'INFO'
}
