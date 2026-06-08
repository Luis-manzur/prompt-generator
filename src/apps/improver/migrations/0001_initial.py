from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ('projects', '0001_initial'),
    ]
    operations = [
        migrations.CreateModel(
            name='PromptJob',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('project', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='prompt_jobs',
                    to='projects.project',
                )),
                ('raw_prompt', models.TextField()),
                ('improved_prompt', models.TextField(blank=True)),
                ('raw_tokens', models.PositiveIntegerField()),
                ('improved_tokens', models.PositiveIntegerField(default=0)),
                ('token_delta', models.IntegerField(default=0)),
                ('model_used', models.CharField(max_length=120)),
                ('status', models.CharField(
                    choices=[('pending', 'Pending'), ('completed', 'Completed'), ('failed', 'Failed')],
                    default='pending',
                    max_length=20,
                )),
                ('error', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.AddIndex(
            model_name='promptjob',
            index=models.Index(fields=['project'], name='improver_job_project_idx'),
        ),
        migrations.AddIndex(
            model_name='promptjob',
            index=models.Index(fields=['created_at'], name='improver_job_created_idx'),
        ),
        migrations.AddIndex(
            model_name='promptjob',
            index=models.Index(fields=['status'], name='improver_job_status_idx'),
        ),
    ]
