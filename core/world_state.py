from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.chronicler import Chronicler
    from core.models import Cell


@dataclass
class WorldState:
    """Состояние мира, передаваемое между движками"""

    run_id: int
    hour: int = 0
    is_day: bool = True
    temperature: float = 15.0
    humidity: float = 50.0

    # Карта: (x, y) -> Cell
    cells: dict[tuple[int, int], Cell] = field(default_factory=dict)

    # Организмы (будут наполняться движками)
    organisms: list = field(default_factory=list)
    dead_organisms: list = field(default_factory=list)

    # События за текущий час
    events: list[dict] = field(default_factory=list)

    # Статистика
    statistics: dict[str, int | float] = field(default_factory=dict)

    # ML-метрики
    metrics: dict[str, float] = field(default_factory=dict)

    # Летописец
    chronicler: Chronicler | None = None

    def get_cell(self, x: int, y: int) -> Cell | None:
        """Получить ячейку по координатам"""
        return self.cells.get((x, y))

    def get_organisms_in_cell(self, x: int, y: int, alive_only: bool = True) -> list:
        """Получить организмы в ячейке"""
        orgs = [
            o for o in self.organisms
            if o.cell and o.cell.x == x and o.cell.y == y
        ]
        if alive_only:
            orgs = [o for o in orgs if o.alive]
        return orgs

    def get_dead_in_cell(self, x: int, y: int, uneaten_only: bool = True) -> list:
        """Получить мёртвые организмы в ячейке"""
        dead = [
            d for d in self.dead_organisms
            if d.x == x and d.y == y
        ]
        if uneaten_only:
            dead = [d for d in dead if not d.eaten]
        return dead

    def get_water_cells(self) -> list[Cell]:
        """Все водные ячейки"""
        return [c for c in self.cells.values() if c.is_water]

    def get_land_cells(self) -> list[Cell]:
        """Все ячейки суши"""
        return [c for c in self.cells.values() if c.is_land]

    def count_organisms_by_type(self, organism_type: str, alive_only: bool = True) -> int:
        """Количество организмов определённого типа"""
        orgs = self.organisms
        if alive_only:
            orgs = [o for o in orgs if o.alive]
        return sum(1 for o in orgs if o.organism_type == organism_type)

    def count_all_organisms(self, alive_only: bool = True) -> int:
        """Общее количество организмов"""
        if alive_only:
            return sum(1 for o in self.organisms if o.alive)
        return len(self.organisms)

    def add_organism(self, organism):
        """Добавить организм в мир"""
        self.organisms.append(organism)

    def remove_organism(self, organism):
        """Удалить организм из мира"""
        if organism in self.organisms:
            self.organisms.remove(organism)

    def add_dead(self, dead):
        """Добавить мёртвый организм"""
        self.dead_organisms.append(dead)

    def log_event(self, event_type: str, engine_name: str, **kwargs):
        """Краткий метод для логирования"""
        if self.chronicler:
            self.chronicler.record(event_type, engine_name, **kwargs)