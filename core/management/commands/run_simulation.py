import time
import signal

from django.core.management.base import BaseCommand

from core.engine import SimulationEngine
from core.base_engine import EngineConfig
from core.registry import EngineRegistry
from engines.microbe import MicrobeEngine


class Command(BaseCommand):
    help = 'Запуск эволюционной симуляции'

    def add_arguments(self, parser):
        parser.add_argument('--run-id', type=int, default=1, help='ID запуска')
        parser.add_argument('--width', type=int, default=30, help='Ширина карты')
        parser.add_argument('--height', type=int, default=20, help='Высота карты')
        parser.add_argument('--tick-interval', type=int, default=60, help='Интервал между тиками (сек)')
        parser.add_argument('--max-hours', type=int, default=None, help='Максимум часов (0 = бесконечно)')
        parser.add_argument('--reset', action='store_true', help='Очистить БД перед запуском')

    def handle(self, *args, **options):
        run_id = options['run_id']
        width = options['width']
        height = options['height']
        tick_interval = options['tick_interval']
        max_hours = options['max_hours']
        if options['reset']:
            from core.models import Cell, Organism, DeadOrganism, EventLog
            self.stdout.write('Очистка БД...')
            Organism.objects.all().delete()
            DeadOrganism.objects.all().delete()
            EventLog.objects.all().delete()
            Cell.objects.all().delete()

        # Регистрируем движки
        EngineRegistry.register(MicrobeEngine)

        # Конфигурация движков
        configs = {
            'microbe': EngineConfig(enabled=True),
        }

        # Создаём движок симуляции
        self.stdout.write(f'[Run {run_id}] Инициализация мира {width}x{height}...')
        engine = SimulationEngine(run_id=run_id, engine_configs=configs)
        engine.initialize_world(width=width, height=height)

        ws = engine.world_state
        self.stdout.write(f'[Run {run_id}] Вода: {len(ws.get_water_cells())}, Суша: {len(ws.get_land_cells())}')
        self.stdout.write(f'[Run {run_id}] Микробов: {ws.count_organisms_by_type("microbe")}')
        self.stdout.write(f'[Run {run_id}] Запуск симуляции (интервал: {tick_interval}с)...')
        self.stdout.write('=' * 60)

        running = True
        hour = 0

        def signal_handler(sig, frame):
            nonlocal running
            self.stdout.write('\n[Завершение] Сохраняем состояние...')
            running = False

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            while running:
                if max_hours and hour >= max_hours:
                    break

                ws = engine.tick()
                hour = ws.hour

                # Вывод статистики каждый час
                microbes = ws.count_organisms_by_type('microbe')
                day_night = 'День' if ws.is_day else 'Ночь'
                self.stdout.write(
                    f'[Час {hour:5d}] {day_night} | '
                    f'Микробы: {microbes:4d} | '
                    f'Темп: {ws.temperature:.1f}° | '
                    f'Влаж: {ws.humidity:.1f}%'
                )

                time.sleep(tick_interval)

        except Exception as e:
            self.stderr.write(f'Ошибка: {e}')
        finally:
            summary = engine.finalize()
            self.stdout.write('=' * 60)
            self.stdout.write(f'[Run {run_id}] Симуляция завершена.')
            self.stdout.write(f'Часов: {summary["total_hours"]}')
            self.stdout.write(f'Макс. температура: {summary["max_temperature"]}')
            self.stdout.write(f'Макс. влажность: {summary["max_humidity"]}')
            self.stdout.write(f'Бурь: {summary["total_storms"]}')
            self.stdout.write(f'Рождений: {summary["counters"]["total_births"]}')
            self.stdout.write(f'Смертей: {summary["counters"]["total_deaths"]}')
            self.stdout.write(f'Делений: {summary["counters"]["total_divisions"]}')