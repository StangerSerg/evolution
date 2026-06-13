from django.db import models
from django.core.validators import MinValueValidator
from .cell import Cell


class Organism(models.Model):
    TRAIT_CHOICES = [
        (1, 'Выносливость'),
        (2, 'Быстрое накопление'),
        (3, 'Каннибализм'),
        (4, 'Синергия'),
        (5, 'Аккумулятор'),
    ]
    ENHANCEMENT_CHOICES = [
        ('A', 'Плодовитость'),
        ('B', 'Гигантизм'),
        ('C', 'Сложность'),
        ('D', 'Скорость'),
    ]
    TYPE_CHOICES = [
        ('microbe', 'Одноклеточное'),
        ('multicellular', 'Многоклеточное'),
        ('plant', 'Растение'),
        ('fungi', 'Мицелий'),
        ('worm', 'Червь'),
        ('tetrapod', 'Тетрапод'),
    ]
    BEHAVIOR_CHOICES = [
        ('predator', 'Хищник'),
        ('scavenger', 'Падальщик'),
        ('generalist', 'Универсал'),
    ]

    cell = models.ForeignKey(Cell, on_delete=models.SET_NULL, null=True, blank=True, related_name='organisms')
    organism_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='microbe')
    alive = models.BooleanField(default=True)
    energy = models.FloatField(default=12.0, validators=[MinValueValidator(0.0)])
    reserve = models.FloatField(default=0.0, validators=[MinValueValidator(0.0)])
    trait = models.IntegerField(choices=TRAIT_CHOICES, null=True, blank=True)
    enhancement = models.CharField(max_length=5, choices=ENHANCEMENT_CHOICES, null=True, blank=True)
    behavior = models.CharField(max_length=15, choices=BEHAVIOR_CHOICES, null=True, blank=True)
    cell_count = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    speed = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    birth_hour = models.IntegerField(validators=[MinValueValidator(0)])
    max_age = models.IntegerField(validators=[MinValueValidator(1)])
    death_hour = models.IntegerField(null=True, blank=True)
    death_cause = models.CharField(max_length=20, null=True, blank=True)
    cannibal_hour = models.IntegerField(null=True, blank=True)
    run_id = models.IntegerField(default=1)

    class Meta:
        verbose_name = 'Организм'
        verbose_name_plural = 'Организмы'
        indexes = [
            models.Index(fields=['alive']),
            models.Index(fields=['cell']),
            models.Index(fields=['run_id']),
            models.Index(fields=['organism_type', 'alive']),
        ]

    def __str__(self):
        status = "жив" if self.alive else "мёртв"
        return f"Organism({self.organism_type}, {status}, energy={self.energy})"

    # === Жизненный цикл ===

    def die(self, hour: int, cause: str):
        """Умертвляет организм"""
        self.alive = False
        self.death_hour = hour
        self.death_cause = cause

    # === Свойства ===

    @property
    def is_cannibal(self) -> bool:
        """Является ли каннибалом"""
        return self.trait == 3

    @property
    def is_multicellular(self) -> bool:
        """Является ли многоклеточным"""
        return self.organism_type in ['multicellular', 'plant', 'fungi', 'worm', 'tetrapod']

    @property
    def can_migrate(self) -> bool:
        """Может ли мигрировать"""
        return self.organism_type in ['microbe', 'multicellular', 'worm', 'tetrapod']

    @property
    def is_on_land(self) -> bool:
        """Находится ли на суше"""
        return self.cell is not None and self.cell.is_land

    # === Проверки ===

    def has_trait(self, trait_id: int) -> bool:
        """Проверяет наличие конкретного свойства"""
        return self.trait == trait_id

    def has_enhancement(self, enhancement_code: str) -> bool:
        """Проверяет наличие конкретного усиления"""
        return self.enhancement == enhancement_code