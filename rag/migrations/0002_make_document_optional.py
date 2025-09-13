# Generated manually to make document field optional and add summary field

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rag', '0001_initial'),
    ]

    operations = [
        # Add summary field with default value
        migrations.AddField(
            model_name='documentchunk',
            name='summary',
            field=models.TextField(blank=True, default=''),
        ),
        # Make document field nullable
        migrations.AlterField(
            model_name='documentchunk',
            name='document',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='chunks', to='rag.document'),
        ),
        # Remove unique_together constraint since it doesn't work with nullable fields
        migrations.AlterUniqueTogether(
            name='documentchunk',
            unique_together=set(),
        ),
    ]
