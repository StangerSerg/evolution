import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from core.models import Cell, Organism


class TestOrganism:
    """Тесты модели Organism"""

    @pytest.fixture
    def water_cell(self, db):
        return Cell.objects.create(x=0, y=0, terrain='water')

    @pytest.fixture
    def land_cell(self, db):
        return Cell.objects.create(x=1, y=0, terrain='land')

    @pytest.fixture
    def microbe(self, water_cell):
        return Organism.objects.create(
            cell=water_cell,
            organism_type='microbe',
            energy=12.0,
            birth_hour=0,
            max_age=72,
            run_id=1
        )

    # === Создание ===

    def test_create_basic_microbe(self, water_cell):
        """Создание базового микроба"""
        org = Organism.objects.create(
            cell=water_cell,
            organism_type='microbe',
            energy=12.0,
            birth_hour=0,
            max_age=72,
            run_id=1
        )
        assert org.organism_type == 'microbe'
        assert org.alive == True
        assert org.energy == 12.0
        assert org.cell_count == 1
        assert org.speed == 1
        assert org.trait is None
        assert org.enhancement is None

    def test_default_values(self, water_cell):
        """Значения по умолчанию"""
        org = Organism.objects.create(
            cell=water_cell,
            organism_type='microbe',
            birth_hour=0,
            max_age=72,
            run_id=1
        )
        assert org.energy == 12.0
        assert org.reserve == 0.0
        assert org.alive == True
        assert org.cell_count == 1
        assert org.speed == 1
        assert org.trait is None
        assert org.enhancement is None
        assert org.behavior is None

    # === Типы организмов ===

    @pytest.mark.parametrize('org_type', [
        'microbe', 'multicellular', 'plant', 'fungi', 'worm', 'tetrapod'
    ])
    def test_valid_organism_types(self, water_cell, org_type):
        """Все допустимые типы организмов"""
        org = Organism(
            cell=water_cell,
            organism_type=org_type,
            energy=10.0,
            birth_hour=0,
            max_age=100,
            run_id=1
        )
        org.full_clean()

    def test_invalid_organism_type(self, water_cell):
        """Недопустимый тип организма"""
        org = Organism(
            cell=water_cell,
            organism_type='dinosaur',
            energy=10.0,
            birth_hour=0,
            max_age=100,
            run_id=1
        )
        with pytest.raises(ValidationError):
            org.full_clean()

    # === Свойства (traits) ===

    @pytest.mark.parametrize('trait', [1, 2, 3, 4, 5])
    def test_valid_traits(self, water_cell, trait):
        """Все 5 свойств"""
        org = Organism(
            cell=water_cell,
            organism_type='microbe',
            energy=10.0,
            birth_hour=0,
            max_age=100,
            run_id=1,
            trait=trait
        )
        org.full_clean()

    def test_trait_none_allowed(self, water_cell):
        """Микроб без свойства"""
        org = Organism.objects.create(
            cell=water_cell,
            organism_type='microbe',
            energy=10.0,
            birth_hour=0,
            max_age=100,
            run_id=1
        )
        assert org.trait is None

    def test_invalid_trait(self, water_cell):
        """Недопустимое свойство"""
        org = Organism(
            cell=water_cell,
            organism_type='microbe',
            energy=10.0,
            birth_hour=0,
            max_age=100,
            run_id=1,
            trait=99
        )
        with pytest.raises(ValidationError):
            org.full_clean()

    # === Усиления (enhancements) ===

    @pytest.mark.parametrize('enhancement', ['A', 'B', 'C', 'D'])
    def test_valid_enhancements(self, water_cell, enhancement):
        """Все 4 усиления"""
        org = Organism(
            cell=water_cell,
            organism_type='multicellular',
            energy=10.0,
            birth_hour=0,
            max_age=100,
            run_id=1,
            enhancement=enhancement
        )
        org.full_clean()

    def test_invalid_enhancement(self, water_cell):
        """Недопустимое усиление"""
        org = Organism(
            cell=water_cell,
            organism_type='multicellular',
            energy=10.0,
            birth_hour=0,
            max_age=100,
            run_id=1,
            enhancement='X'
        )
        with pytest.raises(ValidationError):
            org.full_clean()

    # === Поведение ===

    @pytest.mark.parametrize('behavior', ['predator', 'scavenger', 'generalist'])
    def test_valid_behaviors(self, water_cell, behavior):
        """Модели поведения"""
        org = Organism(
            cell=water_cell,
            organism_type='microbe',
            energy=10.0,
            birth_hour=0,
            max_age=100,
            run_id=1,
            trait=3,
            behavior=behavior
        )
        org.full_clean()

    def test_behavior_on_non_cannibal(self, water_cell):
        """Поведение у не-каннибала (допустимо, но бессмысленно)"""
        org = Organism.objects.create(
            cell=water_cell,
            organism_type='microbe',
            energy=10.0,
            birth_hour=0,
            max_age=100,
            run_id=1,
            trait=1,  # Выносливость
            behavior='predator'
        )
        assert org.behavior == 'predator'

    # === Каннибал ===

    def test_cannibal_hour(self, water_cell):
        """Час охоты для каннибала"""
        org = Organism.objects.create(
            cell=water_cell,
            organism_type='microbe',
            energy=10.0,
            birth_hour=0,
            max_age=100,
            run_id=1,
            trait=3,
            cannibal_hour=15
        )
        assert org.cannibal_hour == 15

    def test_is_cannibal_property(self, water_cell):
        """Свойство is_cannibal"""
        cannibal = Organism.objects.create(
            cell=water_cell,
            organism_type='microbe',
            energy=10.0,
            birth_hour=0,
            max_age=100,
            run_id=1,
            trait=3
        )
        non_cannibal = Organism.objects.create(
            cell=water_cell,
            organism_type='microbe',
            energy=10.0,
            birth_hour=1,
            max_age=100,
            run_id=1,
            trait=1
        )
        assert cannibal.is_cannibal == True
        assert non_cannibal.is_cannibal == False

    # === Многоклеточность ===

    def test_cell_count_default(self, water_cell):
        """По умолчанию 1 клетка"""
        org = Organism.objects.create(
            cell=water_cell,
            organism_type='microbe',
            energy=10.0,
            birth_hour=0,
            max_age=100,
            run_id=1
        )
        assert org.cell_count == 1

    def test_multicellular_cell_count(self, water_cell):
        """У многоклеточного может быть много клеток"""
        org = Organism.objects.create(
            cell=water_cell,
            organism_type='multicellular',
            energy=100.0,
            birth_hour=0,
            max_age=200,
            run_id=1,
            cell_count=10
        )
        assert org.cell_count == 10

    def test_is_multicellular_property(self, water_cell):
        """Свойство is_multicellular"""
        microbe = Organism.objects.create(
            cell=water_cell,
            organism_type='microbe',
            energy=10.0,
            birth_hour=0,
            max_age=100,
            run_id=1
        )
        multi = Organism.objects.create(
            cell=water_cell,
            organism_type='multicellular',
            energy=10.0,
            birth_hour=1,
            max_age=100,
            run_id=1
        )
        assert microbe.is_multicellular == False
        assert multi.is_multicellular == True

    # === Скорость ===

    def test_speed_default(self, microbe):
        """Базовая скорость = 1"""
        assert microbe.speed == 1

    def test_speed_with_enhancement(self, water_cell):
        """Скорость с усилением D"""
        org = Organism.objects.create(
            cell=water_cell,
            organism_type='multicellular',
            energy=10.0,
            birth_hour=0,
            max_age=100,
            run_id=1,
            enhancement='D',
            speed=3
        )
        assert org.speed == 3

    # === Жизненный цикл ===

    def test_alive_by_default(self, microbe):
        """Новый организм жив"""
        assert microbe.alive == True

    def test_die_method(self, microbe):
        """Метод die()"""
        microbe.die(hour=50, cause='starvation')
        assert microbe.alive == False
        assert microbe.death_hour == 50
        assert microbe.death_cause == 'starvation'

    def test_str_representation_alive(self, microbe):
        """Строковое представление живого"""
        assert 'жив' in str(microbe)

    def test_str_representation_dead(self, microbe):
        """Строковое представление мёртвого"""
        microbe.die(hour=50, cause='starvation')
        assert 'мёртв' in str(microbe)

    # === Энергия ===

    def test_reserve_default_zero(self, microbe):
        """Запасник по умолчанию = 0"""
        assert microbe.reserve == 0.0

    def test_reserve_for_accumulator(self, water_cell):
        """Запасник для аккумулятора"""
        org = Organism.objects.create(
            cell=water_cell,
            organism_type='microbe',
            energy=15.0,
            reserve=5.0,
            birth_hour=0,
            max_age=72,
            run_id=1,
            trait=5
        )
        assert org.reserve == 5.0

    # === Связь с ячейкой ===

    def test_cell_relation(self, water_cell, microbe):
        """Связь с ячейкой"""
        assert microbe.cell == water_cell
        assert microbe in water_cell.organisms.all()

    def test_organism_without_cell(self, db):
        """Организм без ячейки (миграция)"""
        org = Organism.objects.create(
            cell=None,
            organism_type='microbe',
            energy=10.0,
            birth_hour=0,
            max_age=72,
            run_id=1
        )
        assert org.cell is None

    # === Миграция ===

    def test_can_migrate_microbe(self, microbe):
        """Микроб может мигрировать"""
        assert microbe.can_migrate == True

    def test_can_migrate_plant(self, water_cell):
        """Растение не может мигрировать"""
        plant = Organism.objects.create(
            cell=water_cell,
            organism_type='plant',
            energy=10.0,
            birth_hour=0,
            max_age=500,
            run_id=1
        )
        assert plant.can_migrate == False

    # === Суша ===

    def test_is_on_land(self, water_cell, land_cell):
        """Проверка нахождения на суше"""
        water_org = Organism.objects.create(
            cell=water_cell,
            organism_type='microbe',
            energy=10.0,
            birth_hour=0,
            max_age=72,
            run_id=1
        )
        land_org = Organism.objects.create(
            cell=land_cell,
            organism_type='microbe',
            energy=10.0,
            birth_hour=1,
            max_age=72,
            run_id=1
        )
        assert water_org.is_on_land == False
        assert land_org.is_on_land == True

    # === has_trait / has_enhancement ===

    def test_has_trait(self, water_cell):
        """Проверка наличия свойства"""
        org = Organism.objects.create(
            cell=water_cell,
            organism_type='microbe',
            energy=10.0,
            birth_hour=0,
            max_age=72,
            run_id=1,
            trait=2
        )
        assert org.has_trait(2) == True
        assert org.has_trait(1) == False

    def test_has_enhancement(self, water_cell):
        """Проверка наличия усиления"""
        org = Organism.objects.create(
            cell=water_cell,
            organism_type='multicellular',
            energy=10.0,
            birth_hour=0,
            max_age=100,
            run_id=1,
            enhancement='B'
        )
        assert org.has_enhancement('B') == True
        assert org.has_enhancement('A') == False

    # === run_id ===

    def test_run_id_default(self, water_cell):
        """run_id по умолчанию = 1"""
        org = Organism.objects.create(
            cell=water_cell,
            organism_type='microbe',
            energy=10.0,
            birth_hour=0,
            max_age=72
        )
        assert org.run_id == 1

    def test_different_run_ids(self, water_cell):
        """Разные run_id"""
        org1 = Organism.objects.create(
            cell=water_cell,
            organism_type='microbe',
            energy=10.0,
            birth_hour=0,
            max_age=72,
            run_id=1
        )
        org2 = Organism.objects.create(
            cell=water_cell,
            organism_type='microbe',
            energy=10.0,
            birth_hour=1,
            max_age=72,
            run_id=2
        )
        assert org1.run_id == 1
        assert org2.run_id == 2