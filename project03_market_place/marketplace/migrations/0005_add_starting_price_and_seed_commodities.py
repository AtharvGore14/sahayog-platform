from django.db import migrations, models


def seed_commodities(apps, schema_editor):
    Commodity = apps.get_model('marketplace', 'Commodity')
    defaults = {
        'Cardboard': 55.00,
        'PET Plastic': 25.00,
        'HDPE Plastic': 35.00,
        'Aluminum': 150.00,
        'Steel': 45.00,
        'Glass': 5.00,
    }
    for name, price in defaults.items():
        Commodity.objects.update_or_create(
            name=name,
            defaults={'market_price': price}
        )


class Migration(migrations.Migration):
    dependencies = [
        ('marketplace', '0004_supplylisting_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='supplylisting',
            name='starting_price',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.RunPython(seed_commodities, migrations.RunPython.noop),
    ]


