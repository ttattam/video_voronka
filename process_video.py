#!/usr/bin/env python3
import subprocess
import logging
import tempfile
import random
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

def find_background_image():
    """Поиск фонового изображения"""
    bg_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
    search_dirs = [Path('.'), Path('./input'), Path('./test')]
    
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        for file_path in search_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in bg_extensions:
                # Проверяем что это не скриншот
                if 'снимок' not in file_path.name.lower() and 'screenshot' not in file_path.name.lower():
                    logging.info(f"Найден фон: {file_path}")
                    return file_path
    
    logging.warning("Фоновое изображение не найдено, будет использован серый фон")
    return None

def create_time_fragment(input_path, output_path, start_time, duration):
    """Создание временного фрагмента из исходного видео"""
    cmd = [
        'ffmpeg',
        '-ss', str(start_time),
        '-i', str(input_path),
        '-t', str(duration),
        '-c', 'copy',
        '-y',
        str(output_path)
    ]
    
    return run_ffmpeg_command(cmd, f"Создание временного фрагмента ({duration}с с {start_time:.2f}с)")

def crop_area(input_path, output_path, area_config, area_name):
    """Обрезка области из уже временного фрагмента"""
    ffmpeg_params = config.FFMPEG_PARAMS
    cmd = [
        'ffmpeg',
        '-i', str(input_path),
        '-filter:v', f"crop={area_config['width']}:{area_config['height']}:{area_config['x']}:{area_config['y']}",
        '-c:v', ffmpeg_params['codec'],
        '-preset', ffmpeg_params['preset'],
        '-crf', str(ffmpeg_params['crf']),
        '-c:a', 'copy',
        '-y',
        str(output_path)
    ]
    
    return run_ffmpeg_command(cmd, f"Обрезка области: {area_name}")

def create_vertical_video(game_path, camera_path, subtitles_path, output_path):
    """Создание вертикального видео из трех частей с фоном - основная функция"""
    output_config = config.OUTPUT_VIDEO
    ffmpeg_params = config.FFMPEG_PARAMS
    layout = config.LAYOUT
    
    # Вычисляем правильные размеры с сохранением пропорций
    camera_original_ratio = config.CAMERA_AREA['width'] / config.CAMERA_AREA['height']  # 479/265 = 1.81
    camera_width = output_config['width']  # 1080px
    camera_height = int(camera_width / camera_original_ratio)  # 596px
    
    game_original_height = config.GAME_AREA['height']  # 455px
    subtitles_height = config.SUBTITLES_AREA['height']  # 265px
    subtitles_width = output_config['width']  # 1080px
    
    # Ищем фоновое изображение
    bg_image = find_background_image()
    
    if bg_image:
        # С фоновым изображением пушок
        cmd = [
            'ffmpeg',
            '-loop', '1', '-i', str(bg_image),  # Фоновое изображение
            '-i', str(game_path),               # Игра
            '-i', str(camera_path),             # Камера
            '-i', str(subtitles_path),          # Субтитры
            '-filter_complex', f"""
            [0:v]scale={output_config['width']}:{output_config['height']}:force_original_aspect_ratio=disable[bg];
            [1:v]fps={output_config['fps']}[game];
            [2:v]fps={output_config['fps']},scale={camera_width}:{camera_height}:force_original_aspect_ratio=disable[camera];
            [3:v]fps={output_config['fps']},scale={subtitles_width}:{subtitles_height}:force_original_aspect_ratio=disable[subtitles];
            [bg][camera]overlay={layout['camera_position']['x']}:{layout['camera_position']['y']}:shortest=1[bg_with_camera];
            [bg_with_camera][subtitles]overlay={layout['subtitles_position']['x']}:{layout['subtitles_position']['y']}:shortest=1[bg_with_camera_subs];
            [bg_with_camera_subs][game]overlay={layout['game_position']['x']}:{layout['game_position']['y']}:shortest=1[final]
            """.strip().replace('\n', '').replace('    ', ''),
            '-map', '[final]',
            '-map', '1:a',  # Аудио из игрового видео
            '-c:v', ffmpeg_params['codec'],
            '-preset', 'fast',
            '-crf', str(ffmpeg_params['crf']),
            '-r', str(output_config['fps']),
            '-avoid_negative_ts', 'make_zero',
            '-fflags', '+genpts',
            '-shortest',  # Заканчиваем когда кончается самое короткое видео
            '-y',
            str(output_path)
        ]
    else:
        # Без фонового изображения - серый фон
        filter_complex = f"""
        [0:v]fps={output_config['fps']}[game];
        [1:v]fps={output_config['fps']},scale={camera_width}:{camera_height}:force_original_aspect_ratio=disable[camera];
        [2:v]fps={output_config['fps']},scale={subtitles_width}:{subtitles_height}:force_original_aspect_ratio=disable[subtitles];
        color=c=#808080:size={output_config['width']}x{output_config['height']}:rate={output_config['fps']}[bg];
        [bg][camera]overlay={layout['camera_position']['x']}:{layout['camera_position']['y']}:shortest=1[bg_with_camera];
        [bg_with_camera][subtitles]overlay={layout['subtitles_position']['x']}:{layout['subtitles_position']['y']}:shortest=1[bg_with_camera_subs];
        [bg_with_camera_subs][game]overlay={layout['game_position']['x']}:{layout['game_position']['y']}:shortest=1[final]
        """.strip().replace('\n', '').replace('    ', '')
        
        cmd = [
            'ffmpeg',
            '-i', str(game_path),
            '-i', str(camera_path),
            '-i', str(subtitles_path),
            '-filter_complex', filter_complex,
            '-map', '[final]',
            '-map', '0:a',
            '-c:v', ffmpeg_params['codec'],
            '-preset', 'fast',
            '-crf', str(ffmpeg_params['crf']),
            '-r', str(output_config['fps']),
            '-avoid_negative_ts', 'make_zero',
            '-fflags', '+genpts',
            '-shortest',  # Заканчиваем когда кончается самое короткое видео
            '-y',
            str(output_path)
        ]
    
    return run_ffmpeg_command(cmd, "Создание вертикального видео с пушком")

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
        # Временный фрагмент по времени
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as time_fragment:
            time_fragment_path = Path(time_fragment.name)
            temp_files.append(time_fragment_path)
        
        # Обрезанная игровая область
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as game_temp:
            game_temp_path = Path(game_temp.name)
            temp_files.append(game_temp_path)
        
        # Обрезанная область камеры
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as camera_temp:
            camera_temp_path = Path(camera_temp.name)
            temp_files.append(camera_temp_path)
        
        # Обрезанная область субтитров
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as subtitles_temp:
            subtitles_temp_path = Path(subtitles_temp.name)
            temp_files.append(subtitles_temp_path)
        
        # ШАГ 1: Создаем временной фрагмент из оригинального видео
        if test_mode:
            start_time = utils.calculate_test_fragment_time(video_info['duration'])
            duration = config.TEST_FRAGMENT['duration']
        else:
            start_time = 0
            duration = video_info['duration']
        
        if not create_time_fragment(input_path, time_fragment_path, start_time, duration):
            logging.error("Ошибка создания временного фрагмента")
            return False
        
        # ШАГ 2: Обрезаем игровую область из временного фрагмента
        if not crop_area(time_fragment_path, game_temp_path, config.GAME_AREA, "игровая"):
            logging.error("Ошибка обрезки игровой области")
            return False
        
        # ШАГ 3: Обрезаем область с камерой из временного фрагмента
        if not crop_area(time_fragment_path, camera_temp_path, config.CAMERA_AREA, "камера"):
            logging.error("Ошибка обрезки области с камерой")
            return False
        
        # ШАГ 4: Обрезаем область субтитров из временного фрагмента
        if not crop_area(time_fragment_path, subtitles_temp_path, config.SUBTITLES_AREA, "субтитры"):
            logging.error("Ошибка обрезки области субтитров")
            return False
        
        # ШАГ 5: Создаем вертикальное видео из трех обрезанных частей
        suffix = "test" if test_mode else ""
        output_path = utils.generate_output_filename(input_path, suffix=suffix)
        
        if not create_vertical_video(game_temp_path, camera_temp_path, subtitles_temp_path, output_path):
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

def create_multiple_clips(input_path, num_clips=20, clip_duration=15):
    """Создание множественных клипов из рандомных мест видео"""
    logging.info(f"Начинается создание {num_clips} клипов по {clip_duration}с каждый")
    
    # Получаем информацию о видео
    video_info = utils.get_video_info(input_path)
    if not video_info:
        logging.error("Не удалось получить информацию о видео")
        return False
    
    # Проверяем координаты кропа
    if not utils.validate_crop_coordinates(video_info['width'], video_info['height']):
        logging.error("Некорректные координаты кропа")
        return False
    
    total_duration = video_info['duration']
    
    # Проверяем что видео достаточно длинное для создания клипов
    if total_duration < clip_duration:
        logging.error(f"Видео слишком короткое ({total_duration}с) для создания клипов по {clip_duration}с")
        return False
    
    # Генерируем рандомные стартовые времена
    max_start_time = total_duration - clip_duration
    start_times = []
    
    for i in range(num_clips):
        start_time = random.uniform(0, max_start_time)
        start_times.append(start_time)
    
    # Сортируем времена для удобства
    start_times.sort()
    
    logging.info(f"Сгенерированы стартовые времена: {[f'{t:.2f}' for t in start_times]}")
    
    successful_clips = 0
    
    for i, start_time in enumerate(start_times, 1):
        logging.info(f"Создание клипа {i}/{num_clips} (старт: {start_time:.2f}с)")
        
        # Создаем временные файлы для этого клипа
        temp_files = []
        try:
            # Временный фрагмент по времени
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as time_fragment:
                time_fragment_path = Path(time_fragment.name)
                temp_files.append(time_fragment_path)
            
            # Обрезанная игровая область
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as game_temp:
                game_temp_path = Path(game_temp.name)
                temp_files.append(game_temp_path)
            
            # Обрезанная область камеры
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as camera_temp:
                camera_temp_path = Path(camera_temp.name)
                temp_files.append(camera_temp_path)
            
            # Обрезанная область субтитров
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as subtitles_temp:
                subtitles_temp_path = Path(subtitles_temp.name)
                temp_files.append(subtitles_temp_path)
            
            # ШАГ 1: Создаем временной фрагмент из оригинального видео
            if not create_time_fragment(input_path, time_fragment_path, start_time, clip_duration):
                logging.error(f"Ошибка создания временного фрагмента для клипа {i}")
                continue
            
            # ШАГ 2: Обрезаем игровую область из временного фрагмента
            if not crop_area(time_fragment_path, game_temp_path, config.GAME_AREA, "игровая"):
                logging.error(f"Ошибка обрезки игровой области для клипа {i}")
                continue
            
            # ШАГ 3: Обрезаем область с камерой из временного фрагмента
            if not crop_area(time_fragment_path, camera_temp_path, config.CAMERA_AREA, "камера"):
                logging.error(f"Ошибка обрезки области с камерой для клипа {i}")
                continue
            
            # ШАГ 4: Обрезаем область субтитров из временного фрагмента
            if not crop_area(time_fragment_path, subtitles_temp_path, config.SUBTITLES_AREA, "субтитры"):
                logging.error(f"Ошибка обрезки области субтитров для клипа {i}")
                continue
            
            # ШАГ 5: Создаем вертикальное видео из трех обрезанных частей
            suffix = f"clip_{i:02d}"
            output_path = utils.generate_output_filename(input_path, suffix=suffix)
            
            if not create_vertical_video_clip(game_temp_path, camera_temp_path, subtitles_temp_path, output_path, clip_duration):
                logging.error(f"Ошибка создания вертикального видео для клипа {i}")
                continue
            
            successful_clips += 1
            logging.info(f"Клип {i} готов: {output_path}")
            
        except Exception as e:
            logging.error(f"Ошибка создания клипа {i}: {e}")
            continue
            
        finally:
            # Очищаем временные файлы
            utils.cleanup_temp_files(temp_files)
    
    logging.info(f"Создание клипов завершено! Успешно создано: {successful_clips}/{num_clips}")
    return successful_clips > 0

def create_vertical_video_clip(game_path, camera_path, subtitles_path, output_path, duration):
    """Создание вертикального видео из трех частей с фоном (для клипов)"""
    output_config = config.OUTPUT_VIDEO
    ffmpeg_params = config.FFMPEG_PARAMS
    layout = config.LAYOUT
    
    # Размеры областей
    camera_height = 800
    game_original_height = config.GAME_AREA['height']  # 415px - оригинальный размер
    subtitles_height = 290  # Как в области кропа
    
    # Ширина всех областей - полная ширина экрана
    camera_width = output_config['width']  # 1080px
    subtitles_width = output_config['width']  # 1080px
    
    # Ищем фоновое изображение
    bg_image = find_background_image()
    
    if bg_image:
        # С фоновым изображением пушок
        cmd = [
            'ffmpeg',
            '-i', str(game_path),               # Игра
            '-i', str(camera_path),             # Камера
            '-i', str(subtitles_path),          # Субтитры  
            '-loop', '1', '-i', str(bg_image),  # Фоновое изображение
            '-filter_complex', f"""
            [3:v]scale={output_config['width']}:{output_config['height']}[bg];
            [0:v]scale={output_config['width']}:{game_original_height}[game];
            [1:v]scale={camera_width}:{camera_height}[camera];
            [2:v]scale={subtitles_width}:{subtitles_height}[subtitles];
            [bg][camera]overlay={layout['camera_position']['x']}:{layout['camera_position']['y']}[bg_with_camera];
            [bg_with_camera][subtitles]overlay={layout['subtitles_position']['x']}:{layout['subtitles_position']['y']}[bg_with_camera_subs];
            [bg_with_camera_subs][game]overlay={layout['game_position']['x']}:{layout['game_position']['y']}[final]
            """.strip().replace('\n', '').replace('    ', ''),
            '-map', '[final]',
            '-map', '0:a',  # Аудио из игрового видео
            '-c:v', ffmpeg_params['codec'],
            '-c:a', 'copy',
            '-preset', 'fast',
            '-crf', str(ffmpeg_params['crf']),
            '-r', str(output_config['fps']),
            '-t', str(duration),
            '-shortest',
            '-y',
            str(output_path)
        ]
    else:
        # Без фонового изображения - серый фон с правильной длительностью
        filter_complex = f"""
        [0:v]scale={output_config['width']}:{game_original_height}[game];
        [1:v]scale={camera_width}:{camera_height}[camera];
        [2:v]scale={subtitles_width}:{subtitles_height}[subtitles];
        color=c=#808080:size={output_config['width']}x{output_config['height']}:duration={duration}:rate={output_config['fps']}[bg];
        [bg][camera]overlay={layout['camera_position']['x']}:{layout['camera_position']['y']}:shortest=1[bg_with_camera];
        [bg_with_camera][subtitles]overlay={layout['subtitles_position']['x']}:{layout['subtitles_position']['y']}:shortest=1[bg_with_camera_subs];
        [bg_with_camera_subs][game]overlay={layout['game_position']['x']}:{layout['game_position']['y']}:shortest=1[final]
        """.strip().replace('\n', '').replace('    ', '')
        
        cmd = [
            'ffmpeg',
            '-i', str(game_path),
            '-i', str(camera_path),
            '-i', str(subtitles_path),
            '-filter_complex', filter_complex,
            '-map', '[final]',
            '-map', '0:a',
            '-c:v', ffmpeg_params['codec'],
            '-c:a', 'aac',
            '-preset', 'fast',
            '-crf', str(ffmpeg_params['crf']),
            '-r', str(output_config['fps']),
            '-t', str(duration),
            '-shortest',
            '-y',
            str(output_path)
        ]
    
    return run_ffmpeg_command(cmd, f"Создание вертикального видео клипа ({duration}с)")

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
    
    # Спрашиваем у пользователя что делать
    print("\nВыберите режим:")
    print("1. Создать один тестовый клип (15 сек)")
    print("2. Создать 20 случайных клипов (по 15 сек каждый)")
    print("3. Обработать все видео целиком")
    
    choice = input("Ваш выбор (1-3): ").strip()
    
    if choice == '1':
        # Обработка тестового фрагмента (15 секунд)
        success = process_video(video_path, test_mode=True)
        if success:
            logging.info("Тестовый клип создан успешно!")
        else:
            logging.error("Ошибка создания тестового клипа")
    
    elif choice == '2':
        # Создание 20 случайных клипов
        success = create_multiple_clips(video_path, num_clips=20, clip_duration=15)
        if success:
            logging.info("Случайные клипы созданы успешно!")
        else:
            logging.error("Ошибка создания случайных клипов")
    
    elif choice == '3':
        # Обработка всего видео
        success = process_video(video_path, test_mode=False)
        if success:
            logging.info("Полная обработка завершена успешно!")
        else:
            logging.error("Ошибка полной обработки видео")
    
    else:
        print("Неверный выбор. Завершение.")
        return

if __name__ == "__main__":
    main()
