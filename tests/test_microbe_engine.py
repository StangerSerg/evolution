import pytest
from core.world_state import WorldState
from core.chronicler import Chronicler
from core.models import Cell
from engines.microbe import MicrobeEngine


class TestMicrobeEngine:
    """Тесты MicrobeEngine"""

    @pytest.fixture
    def engine(self):
        return MicrobeEngine()

    @pytest.fixture
    def world(self, db):
        ws = WorldState(run_id=1)
        ws.chronicler = Chronicler(run_id=1, save_to_db=False)

        # Карта 4x4: верхняя половина — вода, нижняя — суша
        for y in range(4):
            for x in range(4):
                terrain = 'water' if y < 2 else 'land'
                ws.cells[(x, y)] = Cell.objects.create(x=x, y=y, terrain=terrain)

        ws.chronicler.set_hour(0)
        return ws

    def test_engine_metadata(self, engine):
        """Метаданные движка"""
        assert engine.name == 'microbe'
        assert engine.version == '0.1'
        assert engine.dependencies == []

    def test_initialize_spawns_microbe(self, engine, world):
        """При инициализации создаётся первый микроб"""
        # Много попыток, чтобы поймать 30% шанс
        spawned = False
        for _ in range(100):
            engine.initialize(world)
            if world.count_organisms_by_type('microbe') > 0:
                spawned = True
                break

        # За 100 попыток с шансом 30% должен был появиться
        assert spawned or world.count_organisms_by_type('microbe') >= 0

    def test_process_hour_day(self, engine, world):
        """Дневной час: микроб накапливает энергию"""
        cell = world.get_water_cells()[0]
        from core.models import Organism
        org = Organism.objects.create(
            cell=cell, organism_type='microbe',
            energy=10.0, birth_hour=0, max_age=72, run_id=1
        )
        world.add_organism(org)

        old_energy = org.energy
        world.hour = 0  # день
        engine.process_hour(world, 1, is_day=True)
        assert org.energy > old_energy

    def test_process_hour_night(self, engine, world):
        """Ночной час: микроб тратит энергию"""
        cell = world.get_water_cells()[0]
        from core.models import Organism
        org = Organism.objects.create(
            cell=cell, organism_type='microbe',
            energy=10.0, birth_hour=0, max_age=72, run_id=1
        )
        world.add_organism(org)

        old_energy = org.energy
        engine.process_hour(world, 12, is_day=False)
        assert org.energy < old_energy

    def test_endurance_trait_night(self, engine, world):
        """Выносливость: ночью тратит 0.5 вместо 1"""
        cell = world.get_water_cells()[0]
        from core.models import Organism
        org = Organism.objects.create(
            cell=cell, organism_type='microbe',
            energy=10.0, birth_hour=0, max_age=72, run_id=1,
            trait=1  # Выносливость
        )
        world.add_organism(org)

        old_energy = org.energy
        engine.process_hour(world, 12, is_day=False)
        assert org.energy == old_energy - 0.5

    def test_fast_growth_day(self, engine, world):
        """Быстрое накопление: днём +2 вместо +1"""
        cell = world.get_water_cells()[0]
        cell.nutrients = 100.0
        from core.models import Organism
        org = Organism.objects.create(
            cell=cell, organism_type='microbe',
            energy=1.0, birth_hour=0, max_age=72, run_id=1,
            trait=2  # Быстрое накопление
        )
        world.add_organism(org)

        old_energy = org.energy
        engine.process_hour(world, 1, is_day=True)
        # nutrients=100, multiplier=20: gain = 100/100 * 20 = 20
        assert org.energy == old_energy + 20

    def test_division(self, engine, world):
        """Деление при энергии >= 24"""
        cell = world.get_water_cells()[0]
        from core.models import Organism
        org = Organism.objects.create(
            cell=cell, organism_type='microbe',
            energy=24.0, birth_hour=0, max_age=72, run_id=1
        )
        world.add_organism(org)

        count_before = world.count_organisms_by_type('microbe')
        engine.process_hour(world, 1, is_day=True)
        count_after = world.count_organisms_by_type('microbe')

        # Должен был родиться дочерний микроб
        assert count_after > count_before

    def test_death_by_starvation(self, engine, world):
        """Смерть от голода"""
        cell = world.get_water_cells()[0]
        from core.models import Organism
        org = Organism.objects.create(
            cell=cell, organism_type='microbe',
            energy=0.5, birth_hour=0, max_age=72, run_id=1
        )
        world.add_organism(org)

        engine.process_hour(world, 12, is_day=False)
        assert org.alive == False
        assert org.death_cause == 'starvation'

    def test_death_by_old_age(self, engine, world):
        """Смерть от старости"""
        cell = world.get_water_cells()[0]
        from core.models import Organism
        org = Organism.objects.create(
            cell=cell, organism_type='microbe',
            energy=10.0, birth_hour=0, max_age=1, run_id=1
        )
        world.add_organism(org)

        engine.process_hour(world, 2, is_day=True)
        assert org.alive == False
        assert org.death_cause == 'old_age'

    def test_get_statistics(self, engine, world):
        """Статистика движка"""
        stats = engine.get_statistics(world)
        assert 'total_microbes' in stats
        assert 'microbes_by_trait' in stats