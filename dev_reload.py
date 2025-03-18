import time
import os
import subprocess
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Путь к вашему основному файлу бота
BOT_FILE = "face_bot/main.py"
# Директории для мониторинга изменений
WATCH_PATHS = ["face_bot/"]

class ChangeHandler(FileSystemEventHandler):
    def __init__(self):
        self.process = None
        self.start_bot()

    def start_bot(self):
        if self.process:
            self.process.terminate()
            self.process.wait()
            print("\n🔄 Бот остановлен для перезапуска...")
            
        print("🚀 Запуск бота через Poetry...")
        
        # Наследуем stdin, stdout и stderr от родительского процесса
        # Это позволит видеть все принты бота в консоли
        self.process = subprocess.Popen(
            ["poetry", "run", "python", BOT_FILE],
            stdout=sys.stdout,  # Перенаправляем вывод бота в консоль
            stderr=sys.stderr,  # Перенаправляем ошибки бота в консоль
            bufsize=1  # Линейная буферизация для мгновенного вывода
        )
        print("✅ Бот запущен! Ожидание изменений...")

    def on_modified(self, event):
        # Фильтруем только изменения Python-файлов
        if event.src_path.endswith('.py'):
            # Исключаем файлы кэша и временные файлы
            ignored_patterns = ['__pycache__', '.pyc', '.#']
            if any(pattern in event.src_path for pattern in ignored_patterns):
                return
                
            # Исключаем сам файл перезагрузки
            if os.path.basename(event.src_path) != os.path.basename(__file__):
                print(f"\n📝 Обнаружено изменение в файле: {event.src_path}")
                self.start_bot()

def main():
    """Функция для запуска через poetry"""
    print("🔍 Запуск системы автоматического перезапуска бота")
    print(f"👀 Отслеживаемые директории: {', '.join(WATCH_PATHS)}")
    print("📋 Вывод бота будет отображаться в консоли")
    print("-" * 50)
    
    event_handler = ChangeHandler()
    observer = Observer()
    
    for path in WATCH_PATHS:
        observer.schedule(event_handler, path, recursive=True)
        
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n⛔ Остановка бота и системы перезапуска...")
        if event_handler.process:
            event_handler.process.terminate()
        observer.stop()
    
    observer.join()
    print("👋 Система перезапуска остановлена.")

# Оставляем для возможности прямого запуска
if __name__ == "__main__":
    main()