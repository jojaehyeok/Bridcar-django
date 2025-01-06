from django.contrib import admin

from boards.models import Agreement

@admin.register(Agreement)
class AgreementAdmin(admin.ModelAdmin):
    pass
