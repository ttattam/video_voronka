import os
import logging
import subprocess
from pathlib import Path
from datetime import datetime
import json
import config

def setup_logging():
    """Настройка логирования"""
    logging.basicConfig(
        level=getattr(logging, config.LOGGING['log_level']),
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(config.LOGGING['log_file']),
            logging.StreamHandler()
        ]
    )

def create_directories():
    """Создание необходимых папок"""
    directories = [config.INPUT_DIR, config.OUTPUT_DIR]
    for directory in directories:
        directory.mkdir(exist_ok=True)
        logging.info(f"Папка создана/проверена: {directory}")

def find_latest_video(directory=None):
    """Поиск последнего видео по дате изменения"""
    if directory is None:
        # Ищем только в input папке
        search_dirs = [config.INPUT_DIR]
    else:
        search_dirs = [Path(directory)]
    
    latest_video = None
    latest_time = 0
    
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
            
        for file_path in search_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in config.SUPPORTED_FORMATS:
                # Исключаем обработанные файлы
                if file_path.name.startswith('processed_'):
                    continue
                mtime = file_path.stat().st_mtime
                if mtime > latest_time:
                    latest_time = mtime
                    latest_video = file_path
    
    if latest_video:
        logging.info(f"Найдено последнее видео: {latest_video}")
    else:
        logging.warning("Видео не найдено")
    
    return latest_video

def get_video_info(video_path):
    """Получение информации о видео через ffprobe"""
    try:
        # Используем локальный ffprobe если он есть
        ffprobe_path = Path(__file__).parent / 'ffprobe'
        if ffprobe_path.exists():
            ffprobe_cmd = str(ffprobe_path)
        else:
            ffprobe_cmd = 'ffprobe'
        
        cmd = [
            ffprobe_cmd,
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            str(video_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logging.error(f"Ошибка ffprobe: {result.stderr}")
            return None
        
        info = json.loads(result.stdout)
        
        # Ищем видео поток
        video_stream = None
        for stream in info['streams']:
            if stream['codec_type'] == 'video':
                video_stream = stream
                break
        
        if not video_stream:
            logging.error("Видео поток не найден")
            return None
        
        duration = float(info['format']['duration'])
        width = int(video_stream['width'])
        height = int(video_stream['height'])
        
        logging.info(f"Видео: {width}x{height}, длительность: {duration:.2f}с")
        
        return {
            'duration': duration,
            'width': width,
            'height': height,
            'fps': video_stream.get('r_frame_rate', '30/1')
        }
        
    except Exception as e:
        logging.error(f"Ошибка получения информации о видео: {e}")
        return None

def calculate_test_fragment_time(video_duration):
    """Вычисление времени начала тестового фрагмента из случайного места"""
    import random
    
    test_duration = config.TEST_FRAGMENT['duration']
    
    if video_duration <= test_duration:
        return 0  # Если видео короче тестового фрагмента, начинаем с начала
    
    # Случайное время от 0 до (длительность - тестовый фрагмент)
    max_start_time = video_duration - test_duration
    start_time = random.uniform(0, max_start_time)
    
    logging.info(f"Случайный фрагмент: {start_time:.2f}с - {start_time + test_duration:.2f}с")
    return start_time

def validate_crop_coordinates(video_width, video_height):
    """Проверка корректности координат кропа"""
    game_area = config.GAME_AREA
    camera_area = config.CAMERA_AREA
    
    # Проверяем что координаты не выходят за границы видео
    if (game_area['x'] + game_area['width'] > video_width or
        game_area['y'] + game_area['height'] > video_height):
        logging.error(f"Игровая область выходит за границы видео {video_width}x{video_height}")
        return False
    
    if (camera_area['x'] + camera_area['width'] > video_width or
        camera_area['y'] + camera_area['height'] > video_height):
        logging.error(f"Область камеры выходит за границы видео {video_width}x{video_height}")
        return False
    
    logging.info("Координаты кропа корректны")
    return True

def generate_output_filename(input_path, prefix="processed", suffix=""):
    """Генерация имени выходного файла"""
    input_name = Path(input_path).stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if suffix:
        output_name = f"{prefix}_{input_name}_{suffix}_{timestamp}.{config.OUTPUT_VIDEO['format']}"
    else:
        output_name = f"{prefix}_{input_name}_{timestamp}.{config.OUTPUT_VIDEO['format']}"
    
    return config.OUTPUT_DIR / output_name

def cleanup_temp_files(temp_files):
    """Очистка временных файлов"""
    for temp_file in temp_files:
        try:
            if Path(temp_file).exists():
                Path(temp_file).unlink()
                logging.info(f"Удален временный файл: {temp_file}")
        except Exception as e:
            logging.warning(f"Не удалось удалить временный файл {temp_file}: {e}") 