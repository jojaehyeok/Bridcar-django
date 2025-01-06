import random
import string

from django.db import migrations, models
import phonenumber_field.modelfields


def fill_username(apps, schema_editor):
    user_model = apps.get_model('users', 'User')

    for user in user_model.objects.filter(username=''):
        while True:
            username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=32))

            try:
                user_model.objects.get(username=username)
            except:
                break

        user.username = username
        user.save()


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0037_alter_agentprofile_insurance_expiry_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='api_id',
            field=models.CharField(blank=True, max_length=32, null=True, verbose_name='API ID'),
        ),
        migrations.AddField(
            model_name='user',
            name='api_secret',
            field=models.CharField(blank=True, max_length=32, null=True, verbose_name='API Secret'),
        ),
        migrations.AddField(
            model_name='user',
            name='username',
            field=models.CharField(blank=True, max_length=32, verbose_name='유저네임 (필요시 직접 수정)'),
        ),
        migrations.RunPython(fill_username),
        migrations.AlterField(
            model_name='user',
            name='username',
            field=models.CharField(blank=True, max_length=32, verbose_name='유저네임 (필요시 직접 수정)', unique=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='id',
            field=models.BigIntegerField(primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='user',
            name='mobile_number',
            field=phonenumber_field.modelfields.PhoneNumberField(blank=True, max_length=128, null=True, region=None, verbose_name='핸드폰 번호'),
        ),
    ]
