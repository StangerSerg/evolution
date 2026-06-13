from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Полный сброс симуляции (очистка всех данных и автоинкрементов)'

    def handle(self, *args, **options):
        self.stdout.write('Очистка базы данных...')

        # Удаляем все записи
        from core.models import Organism, DeadOrganism, EventLog, Cell, RunConfig, RunSummary
        Organism.objects.all().delete()
        DeadOrganism.objects.all().delete()
        EventLog.objects.all().delete()
        Cell.objects.all().delete()
        RunConfig.objects.all().delete()
        RunSummary.objects.all().delete()

        # Сброс автоинкрементов (SQLite/PostgreSQL)
        tables = [
            'core_organism',
            'core_deadorganism',
            'core_eventlog',
            'core_cell',
            'core_runconfig',
            'core_runsunmmary',
        ]

        db_engine = connection.vendor
        with connection.cursor() as cursor:
            for table in tables:
                try:
                    if db_engine == 'sqlite':
                        cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")
                    elif db_engine == 'postgresql':
                        cursor.execute(f"ALTER SEQUENCE {table}_id_seq RESTART WITH 1")
                except Exception:
                    pass

        self.stdout.write(self.style.SUCCESS('База очищена. Можно запускать симуляцию заново!'))