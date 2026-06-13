import pytest
from core.base_engine import BaseEvolutionEngine, EngineConfig
from core.registry import EngineRegistry


class EngineA(BaseEvolutionEngine):
    name = "engine_a"
    version = "0.1"
    dependencies = []

    def process_hour(self, ws, hour, is_day):
        return []


class EngineB(BaseEvolutionEngine):
    name = "engine_b"
    version = "0.2"
    dependencies = ["engine_a"]

    def process_hour(self, ws, hour, is_day):
        return []


class TestEngineRegistry:
    """Тесты EngineRegistry"""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        """Сбрасываем реестр перед каждым тестом"""
        EngineRegistry.reset()
        yield
        EngineRegistry.reset()

    def test_register_engine(self):
        """Регистрация движка"""
        EngineRegistry.register(EngineA)
        assert "engine_a" in EngineRegistry.get_available_engines()

    def test_register_multiple(self):
        """Регистрация нескольких движков"""
        EngineRegistry.register(EngineA)
        EngineRegistry.register(EngineB)
        assert EngineRegistry.get_available_engines() == ["engine_a", "engine_b"]

    def test_create_engine(self):
        """Создание экземпляра движка"""
        EngineRegistry.register(EngineA)
        engine = EngineRegistry.create("engine_a")
        assert engine.name == "engine_a"
        assert isinstance(engine, EngineA)

    def test_create_with_config(self):
        """Создание с конфигом"""
        EngineRegistry.register(EngineA)
        config = EngineConfig(enabled=False)
        engine = EngineRegistry.create("engine_a", config)
        assert engine.enabled == False

    def test_create_unregistered_raises(self):
        """Создание незарегистрированного движка"""
        with pytest.raises(ValueError, match="не зарегистрирован"):
            EngineRegistry.create("unknown")

    def test_get_engine(self):
        """Получение созданного движка"""
        EngineRegistry.register(EngineA)
        EngineRegistry.create("engine_a")
        engine = EngineRegistry.get("engine_a")
        assert engine is not None
        assert engine.name == "engine_a"

    def test_get_nonexistent(self):
        """Получение несуществующего движка"""
        assert EngineRegistry.get("ghost") is None

    def test_get_all(self):
        """Все активные движки"""
        EngineRegistry.register(EngineA)
        EngineRegistry.register(EngineB)
        EngineRegistry.create("engine_a")
        EngineRegistry.create("engine_b")

        all_engines = EngineRegistry.get_all()
        assert len(all_engines) == 2
        names = [e.name for e in all_engines]
        assert "engine_a" in names
        assert "engine_b" in names