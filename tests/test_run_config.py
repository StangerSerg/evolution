import pytest
from django.db import IntegrityError
from core.models import RunConfig


class TestRunConfig:
    """Тесты модели RunConfig"""

    def test_create_config(self, db):
        """Создание конфигурации с параметрами по умолчанию"""
        config = RunConfig.objects.create(run_id=1)
        assert config.run_id == 1
        assert config.map_width == 30
        assert config.map_height == 20
        assert config.water_ratio == 0.5
        assert config.microbe_spawn_chance == 0.3
        assert config.trait_chance == 0.35
        assert config.cell_capacity == 100

    def test_unique_run_id(self, db):
        """run_id должен быть уникальным"""
        RunConfig.objects.create(run_id=1)
        with pytest.raises(IntegrityError):
            RunConfig.objects.create(run_id=1)

    def test_custom_parameters(self, db):
        """Пользовательские параметры"""
        config = RunConfig.objects.create(
            run_id=2,
            map_width=50,
            map_height=30,
            microbe_spawn_chance=0.5,
            trait_chance=0.4,
            cell_capacity=200
        )
        assert config.map_width == 50
        assert config.map_height == 30
        assert config.microbe_spawn_chance == 0.5
        assert config.trait_chance == 0.4
        assert config.cell_capacity == 200

    def test_notes_field(self, db):
        """Поле заметок"""
        config = RunConfig.objects.create(
            run_id=1,
            notes='Тестовый запуск с повышенной плодовитостью'
        )
        assert config.notes == 'Тестовый запуск с повышенной плодовитостью'

    def test_str_representation(self, db):
        """Строковое представление"""
        config = RunConfig.objects.create(run_id=42)
        assert '42' in str(config)

    def test_multiple_configs(self, db):
        """Несколько конфигураций"""
        RunConfig.objects.create(run_id=1)
        RunConfig.objects.create(run_id=2)
        RunConfig.objects.create(run_id=3)
        assert RunConfig.objects.count() == 3