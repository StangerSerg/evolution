from django.db import models


class RunConfig(models.Model):
    """Конфигурация запуска симуляции"""

    run_id = models.IntegerField(unique=True)

    # Карта
    map_width = models.IntegerField(default=30)
    map_height = models.IntegerField(default=20)
    water_ratio = models.FloatField(default=0.5)

    # Одноклеточные
    microbe_spawn_chance = models.FloatField(default=0.3)
    trait_chance = models.FloatField(default=0.35)
    max_microbes_for_spawn = models.IntegerField(default=255)
    microbe_division_threshold = models.FloatField(default=24)
    microbe_min_age = models.IntegerField(default=24)
    microbe_max_age = models.IntegerField(default=72)

    # Многоклеточные
    fusion_chance = models.FloatField(default=0.03)
    multicell_division_threshold = models.FloatField(default=255)
    fertility_threshold = models.FloatField(default=200)
    enhancement_mutation_chance = models.FloatField(default=0.15)

    # Среда
    cell_capacity = models.IntegerField(default=100)
    crowding_chain_length = models.IntegerField(default=5)

    # Климат
    storm_temp_threshold = models.FloatField(default=30)
    storm_death_chance = models.FloatField(default=0.1)
    humidity_per_plant = models.FloatField(default=1.0)
    temp_per_land_creature = models.FloatField(default=1.0)

    # Миграция
    nutrient_migration_factor = models.FloatField(default=1.0)
    cannibal_migration_factor = models.FloatField(default=10.0)

    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = 'Конфигурация запуска'
        verbose_name_plural = 'Конфигурации запусков'

    def __str__(self):
        return f"RunConfig(run={self.run_id})"