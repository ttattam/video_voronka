#!/bin/bash
echo "🎬 Обработка видео - Video Voronka"
echo "=================================="
echo ""
echo "Ищу видео для обработки..."
python3 process_video.py
echo ""
echo "Результат в папке output/"
echo ""
echo "Для изменения настроек:"
echo "- Координаты кропа: config.py"
echo "- Длительность фрагмента: config.py (TEST_FRAGMENT duration)"
echo "" 