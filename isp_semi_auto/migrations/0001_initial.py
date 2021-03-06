# Generated by Django 2.1.7 on 2019-03-29 19:50

from django.db import migrations, models
import django.db.models.deletion
import isp_semi_auto.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Assignment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('js_id', models.CharField(max_length=2)),
                ('flavour', models.CharField(choices=[('Q', 'Quiz'), ('A', 'Assignment'), ('I', 'Interactive Content')], max_length=1)),
                ('title', models.CharField(max_length=130)),
            ],
        ),
        migrations.CreateModel(
            name='Cohort',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cohort_choices', models.CharField(choices=[('J', 'Jan Extended'), ('F', 'Feb Standard'), ('A', 'Aug Standard'), ('M', 'May Express'), ('O', 'October Express')], max_length=1)),
            ],
        ),
        migrations.CreateModel(
            name='Gradebook',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cohort_choices', models.CharField(choices=[('J', 'Jan Extended'), ('F', 'Feb Standard'), ('A', 'Aug Standard'), ('M', 'May Express'), ('O', 'October Express')], max_length=1)),
                ('subject_choices', models.CharField(choices=[('AE', 'Academic English'), ('IT', 'Information Technology'), ('BS', 'Behavioural Science'), ('MA', 'Mathematics'), ('CH', 'Chemistry'), ('PH', 'Physics'), ('AR', 'Architecture'), ('RE', 'Research'), ('AC', 'Accounting')], max_length=2)),
                ('gb_xls', models.FileField(upload_to='gradebook/%Y-%m-%d/%H/%M')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'get_latest_by': 'uploaded_at',
            },
        ),
        migrations.CreateModel(
            name='Student',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fyid', models.CharField(max_length=8, null=True)),
                ('cohort_choices', models.CharField(choices=[('J', 'Jan Extended'), ('F', 'Feb Standard'), ('A', 'Aug Standard'), ('M', 'May Express'), ('O', 'October Express')], max_length=1)),
                ('firstname', models.CharField(max_length=130)),
                ('lastname', models.CharField(max_length=130)),
                ('preferred', models.CharField(blank=True, max_length=130, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='StudentAssignmentGrades',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('grades', models.TextField(null=True)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('gradebook', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='isp_semi_auto.Gradebook')),
                ('student', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='isp_semi_auto.Student')),
            ],
            options={
                'get_latest_by': 'uploaded_at',
            },
        ),
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(choices=[('AE', 'Academic English'), ('IT', 'Information Technology'), ('BS', 'Behavioural Science'), ('MA', 'Mathematics'), ('CH', 'Chemistry'), ('PH', 'Physics'), ('AR', 'Architecture'), ('RE', 'Research'), ('AC', 'Accounting')], max_length=2)),
            ],
        ),
        migrations.CreateModel(
            name='SubjectTemplate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('step', models.CharField(choices=[('1', 'Step 1.'), ('2', 'Step 2.'), ('3', 'Step 3.'), ('4', 'Step 4.')], max_length=1)),
                ('flavour', models.CharField(choices=[('a', 'A'), ('b', 'B'), ('c', 'C'), ('d', 'D')], max_length=1)),
                ('stage', models.CharField(max_length=45)),
                ('template', models.TextField()),
                ('template_file', models.FileField(blank=True, null=True, upload_to=isp_semi_auto.models.template_path)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('subject_name', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='isp_semi_auto.Subject')),
            ],
            options={
                'get_latest_by': 'uploaded_at',
            },
        ),
        migrations.CreateModel(
            name='Teacher',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('firstname', models.CharField(max_length=130)),
                ('lastname', models.CharField(max_length=130)),
                ('preferred', models.CharField(blank=True, max_length=130, null=True)),
                ('subjects', models.ManyToManyField(related_name='teachers', to='isp_semi_auto.Subject')),
            ],
        ),
        migrations.AddField(
            model_name='assignment',
            name='gradebook',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='isp_semi_auto.Gradebook'),
        ),
    ]
