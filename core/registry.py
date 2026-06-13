from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.base_engine import BaseEvolutionEngine, EngineConfig


class EngineRegistry:
    """Центральный реестр движков"""

    _engine_classes: dict[str, type[BaseEvolutionEngine]] = {}
    _engines: dict[str, BaseEvolutionEngine] = {}

    @classmethod
    def register(cls, engine_class: type[BaseEvolutionEngine]):
        """Зарегистрировать класс движка"""
        # Создаём временный экземпляр для получения name
        temp = engine_class.__new__(engine_class)
        cls._engine_classes[temp.name] = engine_class

    @classmethod
    def create(cls, name: str, config: EngineConfig | None = None) -> BaseEvolutionEngine:
        """Создать экземпляр движка по имени"""
        if name not in cls._engine_classes:
            raise ValueError(f"Движок '{name}' не зарегистрирован")

        engine = cls._engine_classes[name](config)
        cls._engines[name] = engine
        return engine

    @classmethod
    def get(cls, name: str) -> BaseEvolutionEngine | None:
        """Получить созданный экземпляр движка"""
        return cls._engines.get(name)

    @classmethod
    def get_all(cls) -> list[BaseEvolutionEngine]:
        """Все активные движки"""
        return list(cls._engines.values())

    @classmethod
    def get_available_engines(cls) -> list[str]:
        """Список имён всех зарегистрированных движков"""
        return list(cls._engine_classes.keys())

    @classmethod
    def reset(cls):
        """Сбросить реестр (для тестов)"""
        cls._engine_classes.clear()
        cls._engines.clear()
