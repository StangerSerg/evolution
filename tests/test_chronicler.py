import pytest
from core.chronicler import Chronicler, SimulationEvent
from core.models import EventLog


class TestSimulationEvent:
    """Тесты класса SimulationEvent"""

    def test_create_event(self):
        """Создание события"""
        event = SimulationEvent(
            hour=10,
            event_type='birth',
            run_id=1,
            engine_name='microbe',
            organism_id=42,
            organism_type='microbe',
            x=5,
            y=5,
            details={'trait': 3}
        )
        assert event.hour == 10
        assert event.event_type == 'birth'
        assert event.run_id == 1
        assert event.engine_name == 'microbe'
        assert event.organism_id == 42
        assert event.organism_type == 'microbe'
        assert event.x == 5
        assert event.y == 5
        assert event.details == {'trait': 3}

    def test_event_defaults(self):
        """Значения по умолчанию"""
        event = SimulationEvent(
            hour=0,
            event_type='weather',
            run_id=1,
            engine_name='climate'
        )
        assert event.organism_id is None
        assert event.organism_type is None
        assert event.x is None
        assert event.y is None
        assert event.details == {}

    def test_event_details_default(self):
        """details по умолчанию — пустой dict"""
        event = SimulationEvent(
            hour=0,
            event_type='weather',
            run_id=1,
            engine_name='climate'
        )
        assert event.details == {}
        assert isinstance(event.details, dict)


class TestChronicler:
    """Тесты Chronicler"""

    @pytest.fixture
    def chronicler(self):
        return Chronicler(run_id=1, buffer_size=100, save_to_db=True)

    def test_create_chronicler(self):
        """Создание летописца"""
        c = Chronicler(run_id=42, buffer_size=500, save_to_db=False)
        assert c.run_id == 42
        assert c.buffer_size == 500
        assert c.save_to_db == False
        assert len(c.buffer) == 0

    def test_default_values(self):
        """Значения по умолчанию"""
        c = Chronicler(run_id=1)
        assert c.buffer_size == 1000
        assert c.save_to_db == True
        assert c.counters['total_births'] == 0
        assert c.counters['total_deaths'] == 0

    def test_record_event(self, chronicler):
        """Запись события"""
        chronicler.set_hour(10)
        chronicler.record('birth', engine_name='microbe', organism_id=1)

        assert len(chronicler.buffer) == 1
        assert chronicler.buffer[0].event_type == 'birth'
        assert chronicler.buffer[0].hour == 10

    def test_counters_update(self, chronicler):
        """Обновление счётчиков"""
        chronicler.set_hour(1)
        chronicler.record('birth', 'microbe')
        chronicler.record('birth', 'microbe')
        chronicler.record('death', 'microbe')
        chronicler.record('division', 'microbe')
        chronicler.record('fusion', 'microbe')
        chronicler.record('migration', 'microbe')
        chronicler.record('storm_kill', 'climate')

        assert chronicler.counters['total_births'] == 2
        assert chronicler.counters['total_deaths'] == 1
        assert chronicler.counters['total_divisions'] == 1
        assert chronicler.counters['total_fusions'] == 1
        assert chronicler.counters['total_migrations'] == 1
        assert chronicler.counters['total_storm_deaths'] == 1

    def test_first_events(self, chronicler):
        """Первое событие каждого типа"""
        chronicler.set_hour(5)
        chronicler.record('birth', 'microbe')

        chronicler.set_hour(10)
        chronicler.record('death', 'microbe')

        chronicler.set_hour(15)
        chronicler.record('birth', 'microbe')  # не первое

        assert chronicler.first_events['birth'] == 5
        assert chronicler.first_events['death'] == 10

    def test_flush_saves_to_db(self, db, chronicler):
        """Сброс буфера в БД"""
        chronicler.set_hour(1)
        chronicler.record('birth', 'microbe', organism_id=1, x=0, y=0)
        chronicler.record('death', 'microbe', organism_id=2, x=1, y=1)

        chronicler.flush()

        assert EventLog.objects.count() == 2
        assert EventLog.objects.filter(event_type='birth').count() == 1
        assert EventLog.objects.filter(event_type='death').count() == 1

    def test_flush_clears_buffer(self, db, chronicler):
        """Сброс очищает буфер"""
        chronicler.set_hour(1)
        chronicler.record('birth', 'microbe')
        assert len(chronicler.buffer) == 1

        chronicler.flush()
        assert len(chronicler.buffer) == 0

    def test_auto_flush_when_buffer_full(self):
        """Авто-сброс при заполнении буфера"""
        c = Chronicler(run_id=1, buffer_size=3, save_to_db=False)
        c.set_hour(1)

        c.record('birth', 'microbe')
        c.record('birth', 'microbe')
        assert len(c.buffer) == 2

        c.record('birth', 'microbe')  # buffer_size=3, должен сбросить
        assert len(c.buffer) == 0

    def test_get_summary(self, chronicler):
        """Получение сводки"""
        chronicler.set_hour(1)
        chronicler.record('birth', 'microbe')
        chronicler.record('death', 'microbe')

        summary = chronicler.get_summary()
        assert 'counters' in summary
        assert 'first_events' in summary
        assert summary['counters']['total_births'] == 1
        assert summary['counters']['total_deaths'] == 1

    def test_set_hour(self, chronicler):
        """Установка часа"""
        chronicler.set_hour(42)
        chronicler.record('birth', 'microbe')
        assert chronicler.buffer[0].hour == 42

    def test_save_to_db_false(self, db):
        """Отключение сохранения в БД"""
        c = Chronicler(run_id=1, save_to_db=False)
        c.set_hour(1)
        c.record('birth', 'microbe')
        c.flush()

        assert EventLog.objects.count() == 0

    def test_multiple_runs_separation(self, db):
        """Разделение запусков"""
        c1 = Chronicler(run_id=1, save_to_db=True)
        c2 = Chronicler(run_id=2, save_to_db=True)

        c1.set_hour(1)
        c1.record('birth', 'microbe')
        c1.flush()

        c2.set_hour(1)
        c2.record('birth', 'microbe')
        c2.flush()

        assert EventLog.objects.filter(run_id=1).count() == 1
        assert EventLog.objects.filter(run_id=2).count() == 1