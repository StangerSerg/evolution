from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.world_state import WorldState


@dataclass
class EngineConfig:
    """Конфигурация движка"""
    enabled: bool = True
    parameters: dict = field(default_factory=dict)


class BaseEvolutionEngine(ABC):
    """Базовый класс для всех движков эволюции"""

    def __init__(self, config: EngineConfig | None = None):
        self.config = config or EngineConfig()
        self.enabled = self.config.enabled

    @property
    @abstractmethod
    def name(self) -> str:
        """Уникальное имя движка"""
        ...

    @property
    @abstractmethod
    def version(self) -> str:
        """Версия движка"""
        ...

    @property
    @abstractmethod
    def dependencies(self) -> list[str]:
        """Список имён движков, от которых зависит этот"""
        ...

    def is_available(self, ws: WorldState) -> bool:
        """Доступен ли движок в текущем состоянии мира"""
        return True

    def initialize(self, ws: WorldState) -> None:
        """Вызывается при старте симуляции"""
        pass

    @abstractmethod
    def process_hour(self, ws: WorldState, hour: int, is_day: bool) -> list[dict]:
        """Обработка одного часа. Возвращает список событий."""
        ...

    def get_statistics(self, ws: WorldState) -> dict:
        """Статистика движка для отображения"""
        return {}