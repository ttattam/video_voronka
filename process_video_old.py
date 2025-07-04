#!/usr/bin/env python3
import subprocess
import logging
import tempfile
from pathlib import Path
import config
import utils

def run_ffmpeg_command(cmd, description=""):
    """Выполнение команды FFmpeg с логированием"""
    logging.info(f"Выполняется: {description}")
    
    # Используем локальный ffmpeg если он есть
    if cmd[0] == 'ffmpeg':
        ffmpeg_path = Path(__file__).parent / 'ffmpeg'
        if ffmpeg_path.exists():
            cmd[0] = str(ffmpeg_path)
    
    logging.debug(f"Команда: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logging.error(f"Ошибка FFmpeg: {result.stderr}")
            return False
        
        logging.info(f"Успешно: {description}")
        return True
        
    except Exception as e:
        logging.error(f"Ошибка выполнения команды: {e}")
        return False

def create_test_fragment(input_path, output_path, video_info):
    """Создание тестового фрагмента из центра видео"""
    start_time = utils.calculate_test_fragment_time(video_info['duration'])
    duration = config.TEST_FRAGMENT['duration']
    
    cmd = [
        'ffmpeg',
        '-i', str(input_path),
        '-ss', str(start_time),
        '-t', str(duration),
        '-c', 'copy',
        '-y',
        str(output_path)
    ]
    
    return run_ffmpeg_command(cmd, f"Создание тестового фрагмента ({duration}с с {start_time:.2f}с)")

def crop_game_area(input_path, output_path, use_test_fragment=False):
    """Обрезка игровой области"""
    game = config.GAME_AREA
    
    # Базовая команда
    cmd = ['ffmpeg', '-i', str(input_path)]
    
    # Если используется тестовый фрагмент, добавляем параметры времени
    if use_test_fragment:
        video_info = utils.get_video_info(input_path)
        if video_info:
            start_time = utils.calculate_test_fragment_time(video_info['duration'])
            cmd.extend(['-ss', str(start_time), '-t', str(config.TEST_FRAGMENT['duration'])])
    
    # Добавляем фильтр кропа
    cmd.extend([
        '-filter:v', f"crop={game['width']}:{game['height']}:{game['x']}:{game['y']}",
        '-c:a', 'copy',
        '-y',
        str(output_path)
    ])
    
    return run_ffmpeg_command(cmd, "Обрезка игровой области")

def crop_camera_area(input_path, output_path, use_test_fragment=False):
    """Обрезка области с камерой"""
    camera = config.CAMERA_AREA
    
    # Базовая команда
    cmd = ['ffmpeg', '-i', str(input_path)]
    
    # Если используется тестовый фрагмент, добавляем параметры времени
    if use_test_fragment:
        video_info = utils.get_video_info(input_path)
        if video_info:
            start_time = utils.calculate_test_fragment_time(video_info['duration'])
            cmd.extend(['-ss', str(start_time), '-t', str(config.TEST_FRAGMENT['duration'])])
    
    # Добавляем фильтр кропа
    cmd.extend([
        '-filter:v', f"crop={camera['width']}:{camera['height']}:{camera['x']}:{camera['y']}",
        '-c:a', 'copy',
        '-y',
        str(output_path)
    ])
    
    return run_ffmpeg_command(cmd, "Обрезка области с камерой")

def create_vertical_video(game_path, camera_path, output_path):
    """Создание вертикального видео из двух частей"""
    output_config = config.OUTPUT_VIDEO
    layout = config.LAYOUT
    ffmpeg_params = config.FFMPEG_PARAMS
    
    # Создаем сложный фильтр для компоновки
    # Игра занимает 1200px (2/3 от 1920), камера 720px (1/3 от 1920)
    game_height = 1200
    camera_height = 720
    
    filter_complex = f"""
    [0:v]scale={output_config['width']}:{game_height}[game];
    [1:v]scale={output_config['width']}:{camera_height}[camera];
    [game][camera]vstack=inputs=2[final]
    """.strip().replace('\n', '').replace('    ', '')
    
    cmd = [
        'ffmpeg',
        '-i', str(game_path),
        '-i', str(camera_path),
        '-filter_complex', filter_complex,
        '-map', '[final]',
        '-map', '0:a',  # Берем аудио из первого видео (игровой области)
        '-c:v', ffmpeg_params['codec'],
        '-preset', ffmpeg_params['preset'],
        '-crf', str(ffmpeg_params['crf']),
        '-r', str(output_config['fps']),
        '-y',
        str(output_path)
    ]
    
    return run_ffmpeg_command(cmd, "Создание вертикального видео")

def process_video(input_path, test_mode=False):
    """Основная функция обработки видео"""
    logging.info(f"Начинается обработка видео: {input_path}")
    
    # Получаем информацию о видео
    video_info = utils.get_video_info(input_path)
    if not video_info:
        logging.error("Не удалось получить информацию о видео")
        return False
    
    # Проверяем координаты кропа
    if not utils.validate_crop_coordinates(video_info['width'], video_info['height']):
        logging.error("Некорректные координаты кропа")
        return False
    
    # Создаем временные файлы
    temp_files = []
    try:
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as game_temp:
            game_temp_path = Path(game_temp.name)
            temp_files.append(game_temp_path)
        
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as camera_temp:
            camera_temp_path = Path(camera_temp.name)
            temp_files.append(camera_temp_path)
        
        # Обрезаем игровую область
        if not crop_game_area(input_path, game_temp_path, use_test_fragment=test_mode):
            logging.error("Ошибка обрезки игровой области")
            return False
        
        # Обрезаем область с камерой
        if not crop_camera_area(input_path, camera_temp_path, use_test_fragment=test_mode):
            logging.error("Ошибка обрезки области с камерой")
            return False
        
        # Генерируем имя выходного файла
        suffix = "test" if test_mode else ""
        output_path = utils.generate_output_filename(input_path, suffix=suffix)
        
        # Создаем вертикальное видео
        if not create_vertical_video(game_temp_path, camera_temp_path, output_path):
            logging.error("Ошибка создания вертикального видео")
            return False
        
        logging.info(f"Обработка завершена! Результат: {output_path}")
        return True
        
    except Exception as e:
        logging.error(f"Ошибка обработки видео: {e}")
        return False
        
    finally:
        # Очищаем временные файлы
        utils.cleanup_temp_files(temp_files)

def main():
    """Главная функция"""
    # Настройка логирования
    utils.setup_logging()
    
    # Создание необходимых папок
    utils.create_directories()
    
    # Поиск последнего видео
    video_path = utils.find_latest_video()
    if not video_path:
        logging.error("Видео для обработки не найдено")
        return
    
    # Обработка тестового фрагмента (15 секунд)
    success = process_video(video_path, test_mode=True)
    
    if success:
        logging.info("Обработка завершена успешно!")
    else:
        logging.error("Ошибка обработки видео")

if __name__ == "__main__":
    main() 