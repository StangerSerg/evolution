import pytest
from core.world_state import WorldState
from core.models import Cell, Organism, DeadOrganism


class TestWorldState:
    """Тесты WorldState"""

    @pytest.fixture
    def world_state(self):
        return WorldState(run_id=1)

    @pytest.fixture
    def world_with_cells(self, db):
        ws = WorldState(run_id=1)
        for x in range(3):
            for y in range(2):
                terrain = 'water' if (x + y) % 2 == 0 else 'land'
                ws.cells[(x, y)] = Cell(x=x, y=y, terrain=terrain)
        return ws

    # === Создание ===

    def test_create_world_state(self):
        """Создание состояния мира"""
        ws = WorldState(run_id=42)
        assert ws.run_id == 42
        assert ws.hour == 0
        assert ws.is_day == True
        assert ws.temperature == 15.0
        assert ws.humidity == 50.0
        assert ws.cells == {}
        assert ws.organisms == []
        assert ws.dead_organisms == []

    def test_default_values(self):
        """Значения по умолчанию"""
        ws = WorldState(run_id=1)
        assert ws.chronicler is None
        assert ws.events == []
        assert ws.statistics == {}
        assert ws.metrics == {}

    # === Ячейки ===

    def test_get_cell(self, world_with_cells):
        """Получение ячейки по координатам"""
        cell = world_with_cells.get_cell(0, 0)
        assert cell is not None
        assert cell.x == 0
        assert cell.y == 0

    def test_get_cell_none(self, world_with_cells):
        """Получение несуществующей ячейки"""
        cell = world_with_cells.get_cell(100, 100)
        assert cell is None

    def test_get_water_cells(self, world_with_cells):
        """Все водные ячейки"""
        water = world_with_cells.get_water_cells()
        assert len(water) == 3  # 3x2: клетки с (x+y)%2==0 — вода

    def test_get_land_cells(self, world_with_cells):
        """Все ячейки суши"""
        land = world_with_cells.get_land_cells()
        assert len(land) == 3

    # === Организмы ===

    def test_add_organism(self, world_state):
        """Добавление организма"""
        org = object()
        world_state.add_organism(org)
        assert len(world_state.organisms) == 1

    def test_remove_organism(self, world_state):
        """Удаление организма"""
        org = object()
        world_state.add_organism(org)
        world_state.remove_organism(org)
        assert len(world_state.organisms) == 0

    def test_get_organisms_in_cell(self, db):
        """Получение организмов в ячейке"""
        cell = Cell.objects.create(x=0, y=0, terrain='water')
        ws = WorldState(run_id=1)
        ws.cells[(0, 0)] = cell

        org1 = Organism.objects.create(
            cell=cell, organism_type='microbe', energy=10.0,
            birth_hour=0, max_age=72, run_id=1
        )
        org2 = Organism.objects.create(
            cell=cell, organism_type='microbe', energy=8.0,
            birth_hour=1, max_age=72, run_id=1
        )
        ws.organisms = [org1, org2]

        orgs = ws.get_organisms_in_cell(0, 0)
        assert len(orgs) == 2

    def test_get_organisms_in_cell_only_alive(self, db):
        """Только живые в ячейке"""
        cell = Cell.objects.create(x=0, y=0, terrain='water')
        ws = WorldState(run_id=1)
        ws.cells[(0, 0)] = cell

        org1 = Organism.objects.create(
            cell=cell, organism_type='microbe', energy=10.0,
            birth_hour=0, max_age=72, run_id=1
        )
        org2 = Organism.objects.create(
            cell=cell, organism_type='microbe', energy=8.0,
            birth_hour=1, max_age=72, run_id=1, alive=False
        )
        ws.organisms = [org1, org2]

        alive = ws.get_organisms_in_cell(0, 0, alive_only=True)
        assert len(alive) == 1

    # === Мёртвые ===

    def test_add_dead(self, world_state):
        """Добавление мёртвого"""
        dead = object()
        world_state.add_dead(dead)
        assert len(world_state.dead_organisms) == 1

    def test_get_dead_in_cell(self, db):
        """Получение мёртвых в ячейке"""
        ws = WorldState(run_id=1)
        dead1 = DeadOrganism.objects.create(
            organism_type='microbe', energy=5.0,
            x=0, y=0, cause='starvation', hour_of_death=10, run_id=1
        )
        dead2 = DeadOrganism.objects.create(
            organism_type='microbe', energy=3.0,
            x=0, y=0, cause='old_age', hour_of_death=12, run_id=1, eaten=True
        )
        ws.dead_organisms = [dead1, dead2]

        uneaten = ws.get_dead_in_cell(0, 0, uneaten_only=True)
        assert len(uneaten) == 1
        assert uneaten[0].eaten == False

    # === Подсчёт ===

    def test_count_organisms_by_type(self, db):
        """Подсчёт организмов по типу"""
        cell = Cell.objects.create(x=0, y=0, terrain='water')
        ws = WorldState(run_id=1)

        orgs = [
            Organism.objects.create(
                cell=cell, organism_type='microbe', energy=10.0,
                birth_hour=i, max_age=72, run_id=1
            )
            for i in range(3)
        ]
        orgs.append(
            Organism.objects.create(
                cell=cell, organism_type='plant', energy=20.0,
                birth_hour=4, max_age=500, run_id=1
            )
        )
        ws.organisms = orgs

        assert ws.count_organisms_by_type('microbe') == 3
        assert ws.count_organisms_by_type('plant') == 1
        assert ws.count_organisms_by_type('worm') == 0

    def test_count_all_organisms(self, db):
        """Общее количество организмов"""
        cell = Cell.objects.create(x=0, y=0, terrain='water')
        ws = WorldState(run_id=1)
        ws.organisms = [
            Organism.objects.create(
                cell=cell, organism_type='microbe', energy=10.0,
                birth_hour=i, max_age=72, run_id=1
            )
            for i in range(5)
        ]

        assert ws.count_all_organisms() == 5

    def test_count_only_alive(self, db):
        """Подсчёт только живых"""
        cell = Cell.objects.create(x=0, y=0, terrain='water')
        ws = WorldState(run_id=1)
        ws.organisms = [
            Organism.objects.create(
                cell=cell, organism_type='microbe', energy=10.0,
                birth_hour=0, max_age=72, run_id=1, alive=True
            ),
            Organism.objects.create(
                cell=cell, organism_type='microbe', energy=10.0,
                birth_hour=1, max_age=72, run_id=1, alive=False
            ),
        ]

        assert ws.count_all_organisms(alive_only=True) == 1
        assert ws.count_all_organisms(alive_only=False) == 2

    # === Логирование ===

    def test_log_event_no_chronicler(self, world_state):
        """Логирование без летописца не падает"""
        world_state.log_event('birth', engine_name='microbe')

    def test_log_event_with_chronicler(self):
        """Логирование с летописцем"""
        from core.chronicler import Chronicler

        ws = WorldState(run_id=1)
        ws.chronicler = Chronicler(run_id=1, save_to_db=False)
        ws.chronicler.set_hour(5)

        ws.log_event('birth', engine_name='microbe', organism_id=1)
        assert len(ws.chronicler.buffer) == 1