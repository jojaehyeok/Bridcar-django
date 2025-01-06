from django.contrib import admin

from .models import Car, CarEvaluationResult

@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    pass

@admin.register(CarEvaluationResult)
class CarEvaluationResultAdmin(admin.ModelAdmin):
    pass
