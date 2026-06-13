import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from core.models import Cell


class TestCell:
    """Тесты модели Cell — базовой ячейки мира"""

    # === Создание ===

    def test_create_water_cell(self, db):
        """Создание водной ячейки"""
        cell = Cell.objects.create(x=0, y=0, terrain='water')
        assert cell.terrain == 'water'
        assert cell.nutrients == 100.0
        assert str(cell) == "Cell(0, 0) — Вода"

    def test_create_land_cell(self, db):
        """Создание сухопутной ячейки"""
        cell = Cell.objects.create(x=10, y=5, terrain='land')
        assert cell.terrain == 'land'
        assert cell.nutrients == 100.0

    def test_default_nutrients(self, db):
        """Питательность по умолчанию = 100"""
        cell = Cell.objects.create(x=0, y=0, terrain='water')
        assert cell.nutrients == 100.0

    def test_custom_nutrients(self, db):
        """Можно задать свою питательность"""
        cell = Cell.objects.create(x=0, y=0, terrain='water', nutrients=50.0)
        assert cell.nutrients == 50.0

    # === Валидация ===

    def test_unique_coordinates(self, db):
        """Координаты должны быть уникальны"""
        Cell.objects.create(x=0, y=0, terrain='water')

        with pytest.raises(IntegrityError):
            Cell.objects.create(x=0, y=0, terrain='land')

    @pytest.mark.parametrize('terrain', ['water', 'land'])
    def test_valid_terrain_choices(self, db, terrain):
        """Допустимые типы местности"""
        cell = Cell.objects.create(x=0, y=0, terrain=terrain)
        cell.full_clean()  # Не должно быть ошибки

    def test_invalid_terrain(self, db):
        """Недопустимый тип местности"""
        cell = Cell(x=0, y=0, terrain='air')
        with pytest.raises(ValidationError):
            cell.full_clean()

    def test_negative_coordinates(self, db):
        """Отрицательные координаты недопустимы"""
        cell = Cell(x=-1, y=0, terrain='water')
        with pytest.raises(ValidationError):
            cell.full_clean()

    def test_negative_nutrients(self, db):
        """Отрицательная питательность недопустима"""
        cell = Cell(x=0, y=0, terrain='water', nutrients=-10)
        with pytest.raises(ValidationError):
            cell.full_clean()

    # === Связи ===

    def test_organisms_relation(self, db):
        """Связь с организмами"""
        from core.models import Organism

        cell = Cell.objects.create(x=0, y=0, terrain='water')

        org1 = Organism.objects.create(
            cell=cell, organism_type='microbe',
            energy=10.0, birth_hour=0, max_age=72, run_id=1
        )
        org2 = Organism.objects.create(
            cell=cell, organism_type='microbe',
            energy=8.0, birth_hour=1, max_age=72, run_id=1
        )

        assert cell.organisms.count() == 2
        assert org1 in cell.organisms.all()
        assert org2 in cell.organisms.all()

    # === Свойства ===

    def test_is_water_property(self, db):
        """Свойство is_water"""
        water = Cell.objects.create(x=0, y=0, terrain='water')
        land = Cell.objects.create(x=1, y=0, terrain='land')

        assert water.is_water == True
        assert water.is_land == False
        assert land.is_water == False
        assert land.is_land == True

    # === Соседи ===

    def test_get_neighbors(self, db):
        """Получение соседних ячеек"""
        # Создаём сетку 3x3
        cells = {}
        for x in range(3):
            for y in range(3):
                cells[(x, y)] = Cell.objects.create(x=x, y=y, terrain='water')

        # Центральная ячейка (1,1) должна иметь 4 соседа
        center = cells[(1, 1)]
        neighbors = center.get_neighbors(cells)

        assert len(neighbors) == 4
        expected = [(0, 1), (2, 1), (1, 0), (1, 2)]
        for neighbor in neighbors:
            assert (neighbor.x, neighbor.y) in expected

    def test_corner_cell_neighbors(self, db):
        """Угловая ячейка имеет только 2 соседа"""
        cells = {}
        for x in range(3):
            for y in range(3):
                cells[(x, y)] = Cell.objects.create(x=x, y=y, terrain='water')

        corner = cells[(0, 0)]
        neighbors = corner.get_neighbors(cells)

        assert len(neighbors) == 2
        expected = [(1, 0), (0, 1)]
        for neighbor in neighbors:
            assert (neighbor.x, neighbor.y) in expected

    # === Заполненность ===

    def test_is_full(self, db):
        """Проверка заполненности ячейки"""
        from core.models import Organism

        cell = Cell.objects.create(x=0, y=0, terrain='water')

        # Пустая ячейка
        assert cell.is_full(capacity=2) == False

        # Добавляем организмы
        for i in range(2):
            Organism.objects.create(
                cell=cell, organism_type='microbe',
                energy=10.0, birth_hour=i, max_age=72, run_id=1
            )

        assert cell.is_full(capacity=2) == True