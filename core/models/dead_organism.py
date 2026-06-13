from django.db import models
from django.core.validators import MinValueValidator


class DeadOrganism(models.Model):
    """Мёртвый организм — падаль для падальщиков"""

    run_id = models.IntegerField(default=1)
    organism_type = models.CharField(max_length=20)
    trait = models.IntegerField(null=True, blank=True)
    energy = models.FloatField(validators=[MinValueValidator(0.0)])
    x = models.IntegerField()
    y = models.IntegerField()
    cause = models.CharField(max_length=20)
    hour_of_death = models.IntegerField(validators=[MinValueValidator(0)])
    eaten = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Мёртвый организм'
        verbose_name_plural = 'Мёртвые организмы'
        indexes = [
            models.Index(fields=['eaten']),
            models.Index(fields=['x', 'y']),
            models.Index(fields=['run_id']),
        ]

    def __str__(self):
        status = "съеден" if self.eaten else "лежит"
        return f"DeadOrganism({self.organism_type}, {status}, energy={self.energy})"