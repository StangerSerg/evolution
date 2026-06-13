import json
from django.shortcuts import render
from core.models import Cell, Organism, EventLog


def index(request):
    cells = Cell.objects.all().order_by('y', 'x')
    max_x = max(c.x for c in cells) + 1 if cells else 0
    max_y = max(c.y for c in cells) + 1 if cells else 0

    organisms = Organism.objects.filter(alive=True)

    last_event = EventLog.objects.order_by('-hour').first()
    current_hour = last_event.hour if last_event else 0

    cell_data = {}
    cell_info = {}

    for org in organisms:
        if org.cell:
            key = f"{org.cell.x},{org.cell.y}"
            if key not in cell_data:
                cell_data[key] = []
            cell_data[key].append({
                'id': org.id,
                'trait': org.trait,
                'energy': org.energy,
                'age': current_hour - org.birth_hour,
                'birth_hour': org.birth_hour,
                'max_age': org.max_age,
                'behavior': org.behavior,
            })

    for c in cells:
        key = f"{c.x},{c.y}"
        cell_info[key] = {
            'terrain': c.terrain,
            'nutrients': c.nutrients,
        }

    stats = {
        'total_microbes': organisms.filter(organism_type='microbe').count(),
        'total_plants': organisms.filter(organism_type='plant').count(),
        'total_fungi': organisms.filter(organism_type='fungi').count(),
        'total_worms': organisms.filter(organism_type='worm').count(),
        'total_tetrapods': organisms.filter(organism_type='tetrapod').count(),
    }

    return render(request, 'index.html', {
        'cells': cells,
        'max_x': range(max_x),
        'max_y': range(max_y),
        'stats': stats,
        'cell_data_json': json.dumps(cell_data, ensure_ascii=False),
        'cell_info_json': json.dumps(cell_info, ensure_ascii=False),
    })