from __future__ import annotations

import random
from typing import TYPE_CHECKING

from core.base_engine import BaseEvolutionEngine

if TYPE_CHECKING:
    from core.world_state import WorldState


class MicrobeEngine(BaseEvolutionEngine):
    """Движок одноклеточных организмов"""

    @property
    def name(self) -> str:
        return "microbe"

    @property
    def version(self) -> str:
        return "0.1"

    @property
    def dependencies(self) -> list[str]:
        return []

    def initialize(self, ws: WorldState) -> None:
        """Первый микроб в мире"""
        water_cells = ws.get_water_cells()
        if water_cells and random.random() < 0.3:
            cell = random.choice(water_cells)
            self._spawn_microbe(ws, cell)

    def process_hour(self, ws: WorldState, hour: int, is_day: bool) -> list[dict]:
        """Обработка часа"""
        events: list[dict] = []

        # Шанс появления нового микроба
        total_microbes = ws.count_organisms_by_type('microbe')

        if total_microbes < 255:
            if random.random() < 0.3:
                water_cells = ws.get_water_cells()
                if water_cells:
                    cell = random.choice(water_cells)
                    self._spawn_microbe(ws, cell)
                    events.append({'type': 'spawn', 'x': cell.x, 'y': cell.y})

        # Обработка существующих микробов
        microbes = [o for o in ws.organisms if o.organism_type == 'microbe' and o.alive]

        for organism in microbes:
            if is_day:
                self._process_day(ws, organism)
            else:
                self._process_night(ws, organism)

            # Каннибализм (в час X)
            if organism.is_cannibal and organism.cannibal_hour == hour % 24:
                self._cannibal_hunt(ws, organism)

            # Деление
            if organism.energy >= 24:
                self._divide(ws, organism, events)

            # Смерть
            if organism.energy <= 0:
                self._kill(ws, organism, 'starvation')
                events.append({'type': 'death', 'cause': 'starvation', 'id': organism.id})
            elif (hour - organism.birth_hour) >= organism.max_age:
                self._kill(ws, organism, 'old_age')
                events.append({'type': 'death', 'cause': 'old_age', 'id': organism.id})

        # Миграция
        self._migrate(ws)
        self._force_migrate(ws)

        return events

    # === Спавн ===

    def _spawn_microbe(self, ws: WorldState, cell):
        """Создать нового микроба"""
        from core.models import Organism

        organism = Organism.objects.create(
            cell=cell,
            organism_type='microbe',
            energy=12.0,
            birth_hour=ws.hour,
            max_age=random.randint(24, 72),
            run_id=ws.run_id,
        )

        # Шанс получить свойство
        if random.random() < 0.35:
            organism.trait = random.randint(1, 5)

            # Каннибал: час охоты и поведение
            if organism.trait == 3:
                organism.cannibal_hour = random.randint(0, 23)
                organism.behavior = self._choose_behavior(ws, cell)
            organism.save()

        ws.add_organism(organism)
        ws.log_event('birth', self.name, organism_id=organism.id,
                     organism_type='microbe', x=cell.x, y=cell.y,
                     details={'trait': organism.trait, 'energy': organism.energy})

    # === Энергия ===

    def _process_day(self, ws: WorldState, organism):
        """Дневное накопление"""
        multiplier = 20 if organism.trait == 2 else 10  # Быстрое накопление
        gain = organism.cell.nutrients / 100.0 * multiplier if organism.cell else 1.0
        organism.energy += gain

        # Синергия
        if organism.trait == 4 and organism.cell:
            neighbours = [
                o for o in ws.get_organisms_in_cell(organism.cell.x, organism.cell.y)
                if o.trait == 4 and o.alive and o.id != organism.id
            ]
            if neighbours:
                organism.energy += len(neighbours)

        # Аккумулятор: излишек > 10 в резерв
        if organism.trait == 5 and organism.energy > 10:
            excess = organism.energy - 10
            organism.reserve += excess
            organism.energy = 10

        organism.save()

    def _process_night(self, ws: WorldState, organism):
        """Ночная трата"""
        cost = 0.5 if organism.trait == 1 else 1.0  # Выносливость

        # Аккумулятор: сначала тратит основную энергию
        if organism.trait == 5:
            if organism.energy > 0:
                organism.energy -= cost
            # Анабиоз: энергия не уходит ниже 0, резерв не тратится
        else:
            organism.energy -= cost

        organism.save()

    # === Каннибализм ===

    def _choose_behavior(self, ws: WorldState, cell) -> str:
        """Выбрать модель поведения каннибала"""
        living = len(ws.get_organisms_in_cell(cell.x, cell.y))
        dead = len(ws.get_dead_in_cell(cell.x, cell.y))

        total = living + dead
        if total == 0:
            return random.choice(['predator', 'scavenger', 'generalist'])

        p_predator = living / total
        p_scavenger = dead / total
        p_generalist = 0.1

        total_p = p_predator + p_scavenger + p_generalist
        roll = random.random() * total_p

        if roll < p_predator:
            return 'predator'
        elif roll < p_predator + p_scavenger:
            return 'scavenger'
        else:
            return 'generalist'

    def _cannibal_hunt(self, ws: WorldState, organism):
        """Охота каннибала"""
        if not organism.cell:
            return

        if organism.behavior == 'predator':
            self._hunt_living(ws, organism, efficiency=1.0)
        elif organism.behavior == 'scavenger':
            self._hunt_dead(ws, organism, efficiency=1.0)
        else:  # generalist
            # Сначала пробует живых, потом мёртвых
            if not self._hunt_living(ws, organism, efficiency=0.7):
                self._hunt_dead(ws, organism, efficiency=0.7)

    def _hunt_living(self, ws: WorldState, organism, efficiency: float) -> bool:
        """Охота на живого"""
        prey_list = [
            o for o in ws.get_organisms_in_cell(organism.cell.x, organism.cell.y)
            if o.alive and o.id != organism.id
        ]
        if not prey_list:
            return False

        prey = random.choice(prey_list)
        organism.energy += prey.energy * efficiency
        organism.save()
        self._kill(ws, prey, 'cannibalism')
        return True

    def _hunt_dead(self, ws: WorldState, organism, efficiency: float) -> bool:
        """Поедание падали"""
        dead_list = ws.get_dead_in_cell(organism.cell.x, organism.cell.y)
        if not dead_list:
            return False

        target = dead_list[0]
        organism.energy += target.energy * efficiency
        organism.save()
        target.eaten = True
        target.save()
        return True

    # === Деление ===

    def _divide(self, ws: WorldState, parent, events: list):
        """Деление микроба"""
        from core.models import Organism

        parent.energy /= 2
        parent.save()

        child = Organism.objects.create(
            cell=parent.cell,
            organism_type='microbe',
            energy=parent.energy,
            birth_hour=ws.hour,
            max_age=random.randint(24, 72),
            run_id=ws.run_id,
            trait=parent.trait,
            cannibal_hour=parent.cannibal_hour,
            behavior=parent.behavior,
        )

        ws.add_organism(child)
        events.append({'type': 'division', 'parent_id': parent.id, 'child_id': child.id})
        ws.log_event('division', self.name, organism_id=parent.id,
                     details={'child_id': child.id, 'energy': parent.energy})

    # === Смерть ===

    def _kill(self, ws: WorldState, organism, cause: str):
        """Убить организм"""
        from core.models import DeadOrganism

        organism.die(ws.hour, cause)
        organism.save()

        if organism.cell:
            dead = DeadOrganism.objects.create(
                organism_type=organism.organism_type,
                trait=organism.trait,
                energy=organism.energy,
                x=organism.cell.x,
                y=organism.cell.y,
                cause=cause,
                hour_of_death=ws.hour,
                run_id=ws.run_id,
            )
            ws.add_dead(dead)

        ws.log_event('death', self.name, organism_id=organism.id,
                     organism_type='microbe',
                     x=organism.cell.x if organism.cell else None,
                     y=organism.cell.y if organism.cell else None,
                     details={'cause': cause, 'energy': organism.energy})

    # === Миграция ===

    def _migrate(self, ws: WorldState):
        """Миграция организмов"""
        for organism in ws.organisms:
            if not organism.alive or not organism.cell or not organism.can_migrate:
                continue

            # Только в воде
            if organism.cell.is_land:
                continue

            neighbors = organism.cell.get_neighbors(ws.cells)
            water_neighbors = [n for n in neighbors if n.is_water]

            if not water_neighbors:
                continue

            if organism.is_cannibal:
                self._migrate_cannibal(ws, organism, water_neighbors)
            else:
                self._migrate_herbivore(ws, organism, water_neighbors)

    def _force_migrate(self, ws: WorldState):
        """Выдавливание из перенаселённых клеток"""
        for cell in list(ws.cells.values()):
            if not cell.is_water:
                continue

            orgs = ws.get_organisms_in_cell(cell.x, cell.y)
            if len(orgs) <= 100:
                continue

            # Самый слабый уходит
            weakest = min(orgs, key=lambda o: o.energy)

            neighbors = cell.get_neighbors(ws.cells)
            for neighbor in neighbors:
                if neighbor.is_water and len(ws.get_organisms_in_cell(neighbor.x, neighbor.y)) < 100:
                    self._move_to(ws, weakest, neighbor)
                    break

    def _migrate_herbivore(self, ws: WorldState, organism, water_neighbors: list):
        """Миграция не-каннибала: ищет где питательнее"""
        current_nutrients = organism.cell.nutrients
        better = [n for n in water_neighbors if n.nutrients > current_nutrients]

        if better:
            target = random.choice(better)
            delta = target.nutrients - current_nutrients
            if random.random() < (delta / 100.0):
                self._move_to(ws, organism, target)

    def _migrate_cannibal(self, ws: WorldState, organism, water_neighbors: list):
        """Миграция каннибала: ищет где больше добычи"""
        current_prey = len(ws.get_organisms_in_cell(organism.cell.x, organism.cell.y)) + \
                       len(ws.get_dead_in_cell(organism.cell.x, organism.cell.y))

        for neighbor in water_neighbors:
            neighbor_prey = len(ws.get_organisms_in_cell(neighbor.x, neighbor.y)) + \
                            len(ws.get_dead_in_cell(neighbor.x, neighbor.y))
            delta = neighbor_prey - current_prey

            if delta > 0 and random.random() < (delta * 10 / 100.0):
                self._move_to(ws, organism, neighbor)
                return

    def _move_to(self, ws: WorldState, organism, target_cell):
        """Переместить организм в другую клетку"""
        old_x, old_y = organism.cell.x, organism.cell.y
        organism.cell = target_cell
        organism.save()
        ws.log_event('migration', self.name, organism_id=organism.id,
                     x=target_cell.x, y=target_cell.y,
                     details={'from': [old_x, old_y], 'to': [target_cell.x, target_cell.y]})

    # === Статистика ===

    def get_statistics(self, ws: WorldState) -> dict:
        alive = [o for o in ws.organisms if o.organism_type == 'microbe' and o.alive]
        by_trait = {i: 0 for i in range(1, 6)}
        by_trait[None] = 0

        for o in alive:
            by_trait[o.trait] += 1

        return {
            'total_microbes': len(alive),
            'microbes_by_trait': by_trait,
        }