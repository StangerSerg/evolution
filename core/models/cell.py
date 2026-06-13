from django.db import models
from django.core.validators import MinValueValidator


class Cell(models.Model):
    TERRAIN_CHOICES = [
        ('water', 'Вода'),
        ('land', 'Суша'),
    ]

    x = models.IntegerField(validators=[MinValueValidator(0)])
    y = models.IntegerField(validators=[MinValueValidator(0)])
    terrain = models.CharField(max_length=10, choices=TERRAIN_CHOICES)
    nutrients = models.FloatField(default=100.0, validators=[MinValueValidator(0.0)])

    class Meta:
        unique_together = ('x', 'y')
        verbose_name = 'Ячейка'
        verbose_name_plural = 'Ячейки'
        ordering = ['y', 'x']

    def __str__(self):
        terrain_display = 'Вода' if self.terrain == 'water' else 'Суша'
        return f"Cell({self.x}, {self.y}) — {terrain_display}"

    @property
    def is_water(self) -> bool:
        return self.terrain == 'water'

    @property
    def is_land(self) -> bool:
        return self.terrain == 'land'

    def get_neighbors(self, cells_dict: dict) -> list:
        """Возвращает список соседних ячеек (4-связность: верх, низ, лево, право)"""
        neighbors = []
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            neighbor = cells_dict.get((self.x + dx, self.y + dy))
            if neighbor:
                neighbors.append(neighbor)
        return neighbors

    def get_organisms_count(self) -> int:
        """Количество живых организмов в ячейке"""
        return self.organisms.filter(alive=True).count()

    def is_full(self, capacity: int = 100) -> bool:
        """Проверяет, достигнут ли лимит организмов"""
        return self.get_organisms_count() >= capacity