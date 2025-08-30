from django.db import migrations


class Migration(migrations.Migration):

    # This migration is intentionally left empty to resolve a conflict with 0011_complaint.
    # It depends on 0011 so the graph has a single leaf.
    dependencies = [
        ('hr', '0011_complaint'),
    ]

    operations = []
