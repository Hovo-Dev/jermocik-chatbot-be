# Generated manually for chat app

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Conversation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, help_text='Title of the conversation', max_length=255)),
                ('is_archived', models.BooleanField(default=False, help_text='Whether the conversation is archived')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='When the conversation was created')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='When the conversation was last updated')),
                ('last_message_at', models.DateTimeField(blank=True, help_text='Timestamp of the last message in this conversation', null=True)),
                ('user', models.ForeignKey(help_text='The user who owns this conversation', on_delete=django.db.models.deletion.CASCADE, related_name='conversations', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Conversation',
                'verbose_name_plural': 'Conversations',
                'db_table': 'conversations',
                'ordering': ['-last_message_at', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(help_text='The content of the message')),
                ('message_type', models.CharField(choices=[('user', 'User'), ('assistant', 'Assistant'), ('system', 'System')], default='user', help_text='Type of message (user, assistant, system)', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='When the message was created')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='When the message was last updated')),
                ('conversation', models.ForeignKey(help_text='The conversation this message belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='chat.conversation')),
            ],
            options={
                'verbose_name': 'Message',
                'verbose_name_plural': 'Messages',
                'db_table': 'messages',
                'ordering': ['created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='conversation',
            index=models.Index(fields=['user', '-created_at'], name='conversations_user_created_idx'),
        ),
        migrations.AddIndex(
            model_name='conversation',
            index=models.Index(fields=['user', 'is_archived'], name='conversations_user_archived_idx'),
        ),
        migrations.AddIndex(
            model_name='message',
            index=models.Index(fields=['conversation', 'created_at'], name='messages_conversation_created_idx'),
        ),
        migrations.AddIndex(
            model_name='message',
            index=models.Index(fields=['message_type'], name='messages_type_idx'),
        ),
    ]
