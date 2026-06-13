import pytest
from core.engine import SimulationEngine
from core.base_engine import EngineConfig
from core.registry import EngineRegistry


class SimpleMicrobeEngine:
    """Заглушка движка микробов для тестов Engine"""
    name = "microbe"
    version = "0.1"
    dependencies = []

    def __init__(self, config=None):
        self.config = config or EngineConfig()
        self.enabled = self.config.enabled

    def is_available(self, ws):
        return True

    def initialize(self, ws):
        from core.models import Cell, Organism
        # Создаём одного микроба в случайной водной клетке
        water = ws.get_water_cells()
        if water:
            cell = water[0]
            org = Organism(
                cell=cell,
                organism_type='microbe',
                energy=12.0,
                birth_hour=ws.hour,
                max_age=72,
                run_id=ws.run_id
            )
            ws.add_organism(org)

    def process_hour(self, ws, hour, is_day):
        return []

    def get_statistics(self, ws):
        return {'microbes': ws.count_organisms_by_type('microbe')}


class TestSimulationEngine:
    """Тесты SimulationEngine"""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        EngineRegistry.reset()
        EngineRegistry.register(SimpleMicrobeEngine)
        yield
        EngineRegistry.reset()

    def test_create_engine(self):
        """Создание движка симуляции"""
        configs = {'microbe': EngineConfig(enabled=True)}
        engine = SimulationEngine(run_id=1, engine_configs=configs)
        assert engine.run_id == 1
        assert len(engine.engines) == 1
        assert engine.engines[0].name == 'microbe'

    def test_disabled_engine(self):
        """Отключённый движок не добавляется"""
        configs = {'microbe': EngineConfig(enabled=False)}
        engine = SimulationEngine(run_id=1, engine_configs=configs)
        assert len(engine.engines) == 0

    def test_initialize_world(self, db):
        """Инициализация мира"""
        configs = {'microbe': EngineConfig(enabled=True)}
        engine = SimulationEngine(run_id=1, engine_configs=configs)
        engine.initialize_world(width=10, height=10)

        ws = engine.world_state
        assert ws is not None
        assert ws.hour == 0
        assert ws.is_day == True
        assert len(ws.cells) == 100
        assert ws.chronicler is not None

    def test_water_land_ratio(self, db):
        """Соотношение воды и суши"""
        configs = {}
        engine = SimulationEngine(run_id=1, engine_configs=configs)
        engine.initialize_world(width=10, height=10, water_ratio=0.5)

        ws = engine.world_state
        water_count = len(ws.get_water_cells())
        land_count = len(ws.get_land_cells())

        assert water_count == 50
        assert land_count == 50

    def test_tick_increments_hour(self, db):
        """Тик увеличивает час"""
        configs = {}
        engine = SimulationEngine(run_id=1, engine_configs=configs)
        engine.initialize_world(width=4, height=4)

        ws = engine.tick()
        assert ws.hour == 1

        ws = engine.tick()
        assert ws.hour == 2

    def test_day_night_cycle(self, db):
        """Цикл день/ночь"""
        configs = {}
        engine = SimulationEngine(run_id=1, engine_configs=configs)
        engine.initialize_world(width=4, height=4)

        # День: часы 0-11
        for _ in range(12):
            ws = engine.tick()
        assert ws.is_day == False  # час 12 — ночь

        # Ночь: часы 12-23
        for _ in range(12):
            ws = engine.tick()
        assert ws.is_day == True  # час 24 — день

    def test_nutrients_update(self, db):
        """Обновление питательности"""
        configs = {}
        engine = SimulationEngine(run_id=1, engine_configs=configs)
        engine.initialize_world(width=4, height=4)
        engine.tick()

        ws = engine.world_state
        for cell in ws.get_water_cells():
            assert cell.nutrients > 0

        for cell in ws.get_land_cells():
            assert cell.nutrients == 0.1

    def test_finalize(self, db):
        """Завершение симуляции"""
        configs = {}
        engine = SimulationEngine(run_id=1, engine_configs=configs)
        engine.initialize_world(width=4, height=4)

        for _ in range(10):
            engine.tick()

        summary = engine.finalize()
        assert summary['run_id'] == 1
        assert summary['total_hours'] == 10
        assert 'counters' in summary
        assert 'first_events' in summary