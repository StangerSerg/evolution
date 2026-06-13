from __future__ import annotations

import random
from typing import TYPE_CHECKING

from core.chronicler import Chronicler
from core.registry import EngineRegistry
from core.world_state import WorldState

if TYPE_CHECKING:
    from core.base_engine import EngineConfig


class SimulationEngine:
    """Главный движок симуляции"""

    def __init__(self, run_id: int, engine_configs: dict[str, EngineConfig]):
        self.run_id = run_id
        self.world_state: WorldState | None = None
        self.engines: list = []
        self.chronicler = Chronicler(run_id=run_id)

        # Инициализируем движки
        self._init_engines(engine_configs)

        # Климат
        self._max_temperature = 15.0
        self._max_humidity = 50.0
        self._storm_count = 0

    def _init_engines(self, configs: dict[str, EngineConfig]):
        """Создаём движки из конфига"""
        for name, config in configs.items():
            if config.enabled:
                engine = EngineRegistry.create(name, config)
                self.engines.append(engine)

    def initialize_world(self, width: int = 30, height: int = 20, water_ratio: float = 0.5):
        """Создаёт начальное состояние мира"""
        from core.models import Cell

        # Генерируем карту
        cells: dict[tuple[int, int], Cell] = {}
        total_cells = width * height
        water_count = int(total_cells * water_ratio)

        # Создаём плоский список: сначала вода, потом суша
        terrains = ['water'] * water_count + ['land'] * (total_cells - water_count)

        idx = 0
        for y in range(height):
            for x in range(width):
                terrain = terrains[idx]
                cell = Cell.objects.create(x=x, y=y, terrain=terrain)
                cells[(x, y)] = cell
                idx += 1

        # Создаём WorldState
        ws = WorldState(
            run_id=self.run_id,
            hour=0,
            is_day=True,
            temperature=15.0,
            humidity=50.0,
            cells=cells,
            chronicler=self.chronicler,
        )

        # Инициализируем движки
        for engine in self.engines:
            engine.initialize(ws)

        self.world_state = ws

    def tick(self) -> WorldState:
        """Один час симуляции"""
        ws = self.world_state
        ws.hour += 1
        ws.is_day = (ws.hour % 24) < 12
        ws.events = []
        self.chronicler.set_hour(ws.hour)

        # Обработка движками
        for engine in self.engines:
            if engine.enabled and engine.is_available(ws):
                events = engine.process_hour(ws, ws.hour, ws.is_day)
                ws.events.extend(events)

        # Обновление питательности
        self._update_nutrients()

        # Климат (раз в сутки, в конце дня)
        if ws.hour % 24 == 12:  # конец дня
            self._process_climate()

        # Статистика
        ws.statistics = {}
        for engine in self.engines:
            ws.statistics.update(engine.get_statistics(ws))

        # Сброс логов в БД (каждый час)
        self.chronicler.flush()

        return ws

    def _update_nutrients(self):
        ws = self.world_state
        for cell in ws.cells.values():
            if cell.is_water:
                count = len(ws.get_organisms_in_cell(cell.x, cell.y))
                cell.nutrients = 100.0 / (count / 10.0 + 1)
            else:
                cell.nutrients = 0.1
            cell.save()

    def _process_climate(self):
        """Обработка климата в конце дня"""
        ws = self.world_state

        # Растения на суше повышают влажность
        land_plants = sum(
            1 for o in ws.organisms
            if o.alive and o.organism_type == 'plant' and o.cell and o.cell.is_land
        )
        ws.humidity += land_plants

        # Существа на суше повышают температуру
        land_creatures = sum(
            1 for o in ws.organisms
            if o.alive and o.cell and o.cell.is_land
        )
        ws.temperature += land_creatures

        # Рекорды
        self._max_temperature = max(self._max_temperature, ws.temperature)
        self._max_humidity = max(self._max_humidity, ws.humidity)

        # Проверка бури
        if ws.temperature > 30:
            self._storm()

        # Проверка дождя
        elif ws.humidity > 0 and random.random() < (ws.humidity / 100.0):
            self._rain()

    def _storm(self):
        """Буря!"""
        ws = self.world_state
        self._storm_count += 1

        for organism in ws.organisms:
            if organism.alive and organism.cell and organism.cell.is_land:
                if random.random() < 0.1:  # 10% шанс смерти
                    organism.die(ws.hour, 'storm')
                    ws.log_event('storm_kill', 'climate', organism_id=organism.id,
                                 organism_type=organism.organism_type,
                                 x=organism.cell.x, y=organism.cell.y)

        ws.humidity = 50
        ws.temperature //= 2

        ws.log_event('weather', 'climate',
                     details={'type': 'storm', 'temperature': ws.temperature,
                              'humidity': ws.humidity, 'storm_count': self._storm_count})

    def _rain(self):
        """Дождь"""
        ws = self.world_state

        # Растения на суше восстанавливают резерв
        for organism in ws.organisms:
            if organism.alive and organism.organism_type == 'plant' and organism.cell and organism.cell.is_land:
                organism.reserve = organism.energy

        ws.humidity = 0

        ws.log_event('weather', 'climate',
                     details={'type': 'rain', 'temperature': ws.temperature,
                              'humidity': ws.humidity})

    def finalize(self) -> dict:
        """Завершение симуляции, возвращает сводку"""
        ws = self.world_state
        self.chronicler.flush()

        return {
            'run_id': self.run_id,
            'total_hours': ws.hour,
            'max_temperature': self._max_temperature,
            'max_humidity': self._max_humidity,
            'total_storms': self._storm_count,
            'counters': self.chronicler.counters.copy(),
            'first_events': self.chronicler.first_events.copy(),
        }