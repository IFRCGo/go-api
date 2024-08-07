from django.contrib.gis.geos import Polygon
from django.core.management.base import BaseCommand
from django.db import transaction

from api.models import Region


class Command(BaseCommand):
    help = "update regions with bbox. To run, python manage.py update-region-bbox"

    @transaction.atomic
    def handle(self, *args, **options):
        regions = [
            {"id": 0, "bbox": (-32.99047851563364, -47.08120743260383, 67.90795898435852, 41.72638107989897)},
            {"id": 1, "bbox": (-128.9670410156471, -57.359018263521115, -5.217041015634948, 67.04395625933893)},
            {"id": 2, "bbox": (40.44219970775032, -60.71287461544427, 201.6028442389869, 54.2178334601123)},
            {"id": 3, "bbox": (-27.66226811933268, 16.635693975568614, 49.79104043156599, 63.5750514523651)},
            {"id": "4", "bbox": (-29.826416015646174, 10.082644243860557, 72.20141321303817, 52.44608914954304)},
        ]

        results = Region.objects.all()
        for region in results:
            bbox = Polygon.from_bbox(regions[region.name.value]["bbox"])
            region.bbox = bbox
            region.save()
