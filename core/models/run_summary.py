from django.db import models


class RunSummary(models.Model):
    """Сводка результатов запуска"""

    run_id = models.IntegerField()
    status = models.CharField(max_length=20, default='running')
    total_hours = models.IntegerField(null=True)

    # Финальные популяции
    final_microbes = models.IntegerField(null=True)
    final_multicellular = models.IntegerField(null=True)
    final_plants = models.IntegerField(null=True)
    final_fungi = models.IntegerField(null=True)
    final_worms = models.IntegerField(null=True)
    final_tetrapods = models.IntegerField(null=True)

    # Разнообразие
    max_diversity = models.IntegerField(null=True)
    dominant_form = models.CharField(max_length=20, null=True)

    # Первые события
    first_multicellular_hour = models.IntegerField(null=True)
    first_land_hour = models.IntegerField(null=True)
    first_plant_hour = models.IntegerField(null=True)
    first_tetrapod_hour = models.IntegerField(null=True)

    # Климат
    max_temperature = models.FloatField(null=True)
    max_humidity = models.FloatField(null=True)
    total_storms = models.IntegerField(default=0)
    total_deaths_by_storm = models.IntegerField(default=0)

    # Катастрофы
    extinction_hour = models.IntegerField(null=True)
    extinction_cause = models.CharField(max_length=50, null=True)

    # ML-ready
    timeline_24h = models.JSONField(null=True)
    unique_events = models.JSONField(null=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Сводка запуска'
        verbose_name_plural = 'Сводки запусков'

    def __str__(self):
        return f"RunSummary(run={self.run_id}, status={self.status})"