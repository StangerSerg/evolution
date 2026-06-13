import datetime as dt

from django.db import models


class SimulationEvent:
    """Одно событие в симуляции"""

    def __init__(
        self,
        hour: int,
        event_type: str,
        run_id: int,
        engine_name: str,
        organism_id: int | None = None,
        organism_type: str | None = None,
        x: int | None = None,
        y: int | None = None,
        details: dict | None = None,
    ):
        self.hour = hour
        self.event_type = event_type
        self.run_id = run_id
        self.engine_name = engine_name
        self.organism_id = organism_id
        self.organism_type = organism_type
        self.x = x
        self.y = y
        self.details = details or {}
        self.timestamp = dt.datetime.now()


class Chronicler:
    """
    Летописец симуляции.
    Буферизует события и сохраняет пачками в БД.
    """

    def __init__(self, run_id: int, buffer_size: int = 1000, save_to_db: bool = True):
        self.run_id = run_id
        self.buffer: list[SimulationEvent] = []
        self.buffer_size = buffer_size
        self.save_to_db = save_to_db

        # Счётчики для сводки
        self.counters: dict[str, int] = {
            'total_births': 0,
            'total_deaths': 0,
            'total_divisions': 0,
            'total_fusions': 0,
            'total_migrations': 0,
            'total_storm_deaths': 0,
        }
        self.first_events: dict[str, int] = {}

    def record(
        self,
        event_type: str,
        engine_name: str,
        organism_id: int | None = None,
        organism_type: str | None = None,
        x: int | None = None,
        y: int | None = None,
        details: dict | None = None,
    ):
        """Записать событие в летопись"""
        event = SimulationEvent(
            hour=self._current_hour,
            event_type=event_type,
            run_id=self.run_id,
            engine_name=engine_name,
            organism_id=organism_id,
            organism_type=organism_type,
            x=x,
            y=y,
            details=details,
        )
        self._update_counters(event)
        self.buffer.append(event)

        if len(self.buffer) >= self.buffer_size:
            self.flush()

    @property
    def _current_hour(self) -> int:
        """Текущий час (устанавливается извне перед тиком)"""
        return getattr(self, '_hour', 0)

    def set_hour(self, hour: int):
        """Установить текущий час"""
        self._hour = hour

    def _update_counters(self, event: SimulationEvent):
        """Обновление счётчиков"""
        match event.event_type:
            case 'birth':
                self.counters['total_births'] += 1
            case 'death':
                self.counters['total_deaths'] += 1
            case 'division':
                self.counters['total_divisions'] += 1
            case 'fusion':
                self.counters['total_fusions'] += 1
            case 'migration':
                self.counters['total_migrations'] += 1
            case 'storm_kill':
                self.counters['total_storm_deaths'] += 1

        if event.event_type not in self.first_events:
            self.first_events[event.event_type] = event.hour

    def flush(self):
        """Сбросить буфер в БД"""
        if not self.buffer:
            return

        if self.save_to_db:
            self._save_to_database()

        self.buffer.clear()

    def _save_to_database(self):
        """Пакетная вставка в БД"""
        from core.models import EventLog

        events = [
            EventLog(
                run_id=e.run_id,
                hour=e.hour,
                event_type=e.event_type,
                organism_id=e.organism_id,
                organism_type=e.organism_type,
                x=e.x,
                y=e.y,
                details=e.details,
            )
            for e in self.buffer
        ]
        EventLog.objects.bulk_create(events)

    def get_summary(self) -> dict:
        """Возвращает сводку для RunSummary"""
        return {
            'counters': self.counters.copy(),
            'first_events': self.first_events.copy(),
        }
