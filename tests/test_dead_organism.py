import pytest
from django.core.exceptions import ValidationError
from core.models import DeadOrganism


class TestDeadOrganism:
    """Тесты модели DeadOrganism"""

    def test_create_dead_organism(self, db):
        """Создание записи о мёртвом организме"""
        dead = DeadOrganism.objects.create(
            organism_type='microbe',
            energy=5.0,
            x=3,
            y=7,
            cause='starvation',
            hour_of_death=42,
            run_id=1
        )
        assert dead.organism_type == 'microbe'
        assert dead.energy == 5.0
        assert dead.x == 3
        assert dead.y == 7
        assert dead.cause == 'starvation'
        assert dead.hour_of_death == 42
        assert dead.eaten == False
        assert dead.trait is None

    def test_with_trait(self, db):
        """Мёртвый организм с свойством"""
        dead = DeadOrganism.objects.create(
            organism_type='microbe',
            trait=3,
            energy=10.0,
            x=0,
            y=0,
            cause='cannibalism',
            hour_of_death=100,
            run_id=1
        )
        assert dead.trait == 3

    def test_eaten_default_false(self, db):
        """По умолчанию не съеден"""
        dead = DeadOrganism.objects.create(
            organism_type='microbe',
            energy=5.0,
            x=0,
            y=0,
            cause='old_age',
            hour_of_death=50,
            run_id=1
        )
        assert dead.eaten == False

    def test_mark_as_eaten(self, db):
        """Пометка как съеденного"""
        dead = DeadOrganism.objects.create(
            organism_type='microbe',
            energy=5.0,
            x=0,
            y=0,
            cause='old_age',
            hour_of_death=50,
            run_id=1
        )
        dead.eaten = True
        dead.save()

        dead.refresh_from_db()
        assert dead.eaten == True

    def test_str_representation(self, db):
        """Строковое представление"""
        dead = DeadOrganism.objects.create(
            organism_type='worm',
            energy=15.0,
            x=5,
            y=5,
            cause='storm',
            hour_of_death=200,
            run_id=1
        )
        assert 'лежит' in str(dead)

        dead.eaten = True
        dead.save()
        assert 'съеден' in str(dead)

    @pytest.mark.parametrize('cause', [
        'starvation', 'old_age', 'cannibalism', 'storm', 'crowding'
    ])
    def test_death_causes(self, db, cause):
        """Разные причины смерти"""
        dead = DeadOrganism.objects.create(
            organism_type='microbe',
            energy=1.0,
            x=0,
            y=0,
            cause=cause,
            hour_of_death=10,
            run_id=1
        )
        assert dead.cause == cause

    def test_negative_energy_not_allowed(self, db):
        """Отрицательная энергия недопустима"""
        dead = DeadOrganism(
            organism_type='microbe',
            energy=-5.0,
            x=0,
            y=0,
            cause='starvation',
            hour_of_death=10,
            run_id=1
        )
        with pytest.raises(ValidationError):
            dead.full_clean()

    def test_multiple_dead_in_same_cell(self, db):
        """В одной клетке может быть несколько трупов"""
        DeadOrganism.objects.create(
            organism_type='microbe', energy=5.0,
            x=0, y=0, cause='starvation', hour_of_death=10, run_id=1
        )
        DeadOrganism.objects.create(
            organism_type='microbe', energy=8.0,
            x=0, y=0, cause='old_age', hour_of_death=12, run_id=1
        )
        DeadOrganism.objects.create(
            organism_type='worm', energy=20.0,
            x=0, y=0, cause='cannibalism', hour_of_death=15, run_id=1
        )

        count = DeadOrganism.objects.filter(x=0, y=0).count()
        assert count == 3

    def test_run_id_default(self, db):
        """run_id по умолчанию = 1"""
        dead = DeadOrganism.objects.create(
            organism_type='microbe',
            energy=5.0,
            x=0, y=0,
            cause='starvation',
            hour_of_death=10
        )
        assert dead.run_id == 1