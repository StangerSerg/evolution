import pytest
from core.models import EventLog


class TestEventLog:
    """Тесты модели EventLog"""

    def test_create_birth_event(self, db):
        """Событие рождения"""
        event = EventLog.objects.create(
            run_id=1,
            hour=10,
            event_type='birth',
            organism_id=1,
            organism_type='microbe',
            x=5,
            y=5,
            details={'trait': 3, 'energy': 12.0}
        )
        assert event.event_type == 'birth'
        assert event.hour == 10
        assert event.organism_id == 1
        assert event.details == {'trait': 3, 'energy': 12.0}

    def test_create_death_event(self, db):
        """Событие смерти"""
        event = EventLog.objects.create(
            run_id=1,
            hour=50,
            event_type='death',
            organism_id=2,
            organism_type='microbe',
            x=3,
            y=4,
            details={'cause': 'starvation', 'energy_at_death': 0.5}
        )
        assert event.event_type == 'death'
        assert event.details['cause'] == 'starvation'

    @pytest.mark.parametrize('event_type', [
        'birth', 'death', 'division', 'fusion', 'migration',
        'mutation', 'storm_kill', 'weather', 'first_multicellular',
        'first_land', 'extinction'
    ])
    def test_all_event_types(self, db, event_type):
        """Все типы событий"""
        event = EventLog.objects.create(
            run_id=1,
            hour=1,
            event_type=event_type
        )
        assert event.event_type == event_type

    def test_details_json_field(self, db):
        """JSON поле для деталей"""
        complex_details = {
            'parent_id': 10,
            'child_id': 11,
            'energy_before': 50.0,
            'energy_after': 25.0,
            'trait': 4
        }
        event = EventLog.objects.create(
            run_id=1,
            hour=24,
            event_type='division',
            details=complex_details
        )
        assert event.details == complex_details
        assert event.details['energy_before'] == 50.0

    def test_null_fields(self, db):
        """Необязательные поля могут быть None"""
        event = EventLog.objects.create(
            run_id=1,
            hour=5,
            event_type='weather',
            details={'temperature': 25.0, 'humidity': 60.0}
        )
        assert event.organism_id is None
        assert event.x is None
        assert event.y is None

    def test_str_representation(self, db):
        """Строковое представление"""
        event = EventLog.objects.create(
            run_id=1,
            hour=100,
            event_type='extinction'
        )
        assert 'extinction' in str(event)
        assert '100' in str(event)

    def test_multiple_events_same_hour(self, db):
        """Несколько событий в один час"""
        EventLog.objects.create(run_id=1, hour=10, event_type='birth')
        EventLog.objects.create(run_id=1, hour=10, event_type='death')
        EventLog.objects.create(run_id=1, hour=10, event_type='migration')

        count = EventLog.objects.filter(run_id=1, hour=10).count()
        assert count == 3

    def test_run_id_separation(self, db):
        """События разных запусков разделены"""
        EventLog.objects.create(run_id=1, hour=1, event_type='birth')
        EventLog.objects.create(run_id=2, hour=1, event_type='birth')

        assert EventLog.objects.filter(run_id=1).count() == 1
        assert EventLog.objects.filter(run_id=2).count() == 1
