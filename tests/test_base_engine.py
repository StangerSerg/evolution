import pytest
from core.base_engine import BaseEvolutionEngine, EngineConfig


class DummyEngine(BaseEvolutionEngine):
    """Тестовый движок"""

    @property
    def name(self) -> str:
        return "dummy"

    @property
    def version(self) -> str:
        return "0.1"

    @property
    def dependencies(self) -> list[str]:
        return []

    def process_hour(self, ws, hour, is_day):
        return [{'event_type': 'dummy_tick', 'hour': hour}]

    def get_statistics(self, ws):
        return {'dummy_count': 42}


class TestEngineConfig:
    """Тесты EngineConfig"""

    def test_default_config(self):
        """Конфиг по умолчанию"""
        config = EngineConfig()
        assert config.enabled == True
        assert config.parameters == {}

    def test_disabled_config(self):
        """Отключённый конфиг"""
        config = EngineConfig(enabled=False)
        assert config.enabled == False

    def test_config_with_parameters(self):
        """Конфиг с параметрами"""
        config = EngineConfig(parameters={'spawn_rate': 0.5, 'max_count': 100})
        assert config.parameters['spawn_rate'] == 0.5
        assert config.parameters['max_count'] == 100


class TestBaseEvolutionEngine:
    """Тесты BaseEvolutionEngine"""

    def test_create_engine(self):
        """Создание движка"""
        engine = DummyEngine()
        assert engine.name == "dummy"
        assert engine.version == "0.1"
        assert engine.dependencies == []
        assert engine.enabled == True

    def test_create_with_config(self):
        """Создание с конфигом"""
        config = EngineConfig(enabled=False, parameters={'key': 'value'})
        engine = DummyEngine(config)
        assert engine.enabled == False
        assert engine.config.parameters == {'key': 'value'}

    def test_is_available_default(self):
        """По умолчанию движок доступен"""
        engine = DummyEngine()
        assert engine.is_available(None) == True

    def test_initialize_does_nothing(self):
        """initialize по умолчанию ничего не делает"""
        engine = DummyEngine()
        engine.initialize(None)  # Не должно падать

    def test_process_hour(self):
        """process_hour возвращает события"""
        engine = DummyEngine()
        events = engine.process_hour(None, 10, True)
        assert len(events) == 1
        assert events[0]['event_type'] == 'dummy_tick'
        assert events[0]['hour'] == 10

    def test_get_statistics(self):
        """get_statistics возвращает словарь"""
        engine = DummyEngine()
        stats = engine.get_statistics(None)
        assert stats == {'dummy_count': 42}

    def test_default_statistics(self):
        """Статистика по умолчанию — пустой словарь"""

        class MinimalEngine(BaseEvolutionEngine):
            name = "minimal"
            version = "1.0"
            dependencies = []

            def process_hour(self, ws, hour, is_day):
                return []

        engine = MinimalEngine()
        assert engine.get_statistics(None) == {}