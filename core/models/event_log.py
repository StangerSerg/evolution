from django.db import models


class EventLog(models.Model):
    """Летопись событий симуляции"""

    EVENT_CHOICES = [
        ('birth', 'Рождение'),
        ('death', 'Смерть'),
        ('division', 'Деление'),
        ('fusion', 'Слияние'),
        ('migration', 'Миграция'),
        ('mutation', 'Мутация'),
        ('storm_kill', 'Гибель от бури'),
        ('weather', 'Погодное событие'),
        ('first_multicellular', 'Первый многоклеточный'),
        ('first_land', 'Первый выход на сушу'),
        ('extinction', 'Вымирание'),
    ]

    run_id = models.IntegerField(default=1)
    hour = models.IntegerField()
    event_type = models.CharField(max_length=30, choices=EVENT_CHOICES)
    organism_id = models.IntegerField(null=True, blank=True)
    organism_type = models.CharField(max_length=20, null=True, blank=True)
    x = models.IntegerField(null=True, blank=True)
    y = models.IntegerField(null=True, blank=True)
    details = models.JSONField(null=True, blank=True)

    class Meta:
        verbose_name = 'Событие'
        verbose_name_plural = 'События'
        indexes = [
            models.Index(fields=['run_id', 'hour']),
            models.Index(fields=['event_type']),
        ]

    def __str__(self):
        return f"EventLog({self.event_type}, hour={self.hour})"