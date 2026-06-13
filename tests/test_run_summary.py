import pytest
from core.models import RunSummary


class TestRunSummary:
    """Тесты модели RunSummary"""

    def test_create_summary(self, db):
        """Создание сводки"""
        summary = RunSummary.objects.create(
            run_id=1,
            status='running',
            total_hours=0
        )
        assert summary.run_id == 1
        assert summary.status == 'running'
        assert summary.total_hours == 0
        assert summary.total_storms == 0

    def test_statuses(self, db):
        """Статусы запуска"""
        for status in ['running', 'finished', 'extinct']:
            summary = RunSummary.objects.create(
                run_id=1,
                status=status
            )
            assert summary.status == status

    def test_final_populations(self, db):
        """Финальные популяции"""
        summary = RunSummary.objects.create(
            run_id=1,
            status='finished',
            final_microbes=150,
            final_multicellular=20,
            final_plants=10,
            final_fungi=5,
            final_worms=8,
            final_tetrapods=2
        )
        assert summary.final_microbes == 150
        assert summary.final_multicellular == 20
        assert summary.final_tetrapods == 2

    def test_first_events(self, db):
        """Первые события"""
        summary = RunSummary.objects.create(
            run_id=1,
            status='finished',
            first_multicellular_hour=48,
            first_land_hour=120,
            first_plant_hour=130,
            first_tetrapod_hour=200
        )
        assert summary.first_multicellular_hour == 48
        assert summary.first_land_hour == 120
        assert summary.first_tetrapod_hour == 200

    def test_climate_data(self, db):
        """Климатические данные"""
        summary = RunSummary.objects.create(
            run_id=1,
            status='finished',
            max_temperature=35.5,
            max_humidity=80.0,
            total_storms=5,
            total_deaths_by_storm=12
        )
        assert summary.max_temperature == 35.5
        assert summary.total_storms == 5

    def test_extinction(self, db):
        """Вымирание"""
        summary = RunSummary.objects.create(
            run_id=1,
            status='extinct',
            extinction_hour=300,
            extinction_cause='overheating'
        )
        assert summary.status == 'extinct'
        assert summary.extinction_hour == 300
        assert summary.extinction_cause == 'overheating'

    def test_json_fields(self, db):
        """JSON поля для ML"""
        timeline = [{'hour': 24, 'microbes': 50}, {'hour': 48, 'microbes': 120}]
        unique = [{'event': 'first_fusion', 'hour': 50}]

        summary = RunSummary.objects.create(
            run_id=1,
            status='finished',
            timeline_24h=timeline,
            unique_events=unique
        )
        assert summary.timeline_24h == timeline
        assert summary.unique_events == unique
        assert summary.timeline_24h[0]['microbes'] == 50

    def test_dominant_form(self, db):
        """Доминирующая форма"""
        summary = RunSummary.objects.create(
            run_id=1,
            status='finished',
            dominant_form='plant'
        )
        assert summary.dominant_form == 'plant'

    def test_multiple_summaries(self, db):
        """Несколько сводок"""
        RunSummary.objects.create(run_id=1, status='finished')
        RunSummary.objects.create(run_id=2, status='extinct')
        RunSummary.objects.create(run_id=3, status='running')
        assert RunSummary.objects.count() == 3