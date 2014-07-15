from django.contrib import admin
from . import models

class UplusTransactionAdmin(admin.ModelAdmin):
    list_display = ['amount', 'basket_id', 'timestamp', 'status', 'pay_type',]
    readonly_fields = ['amount', 'status', 'pay_type', 'basket_id']

admin.site.register(models.UplusTransaction, UplusTransactionAdmin)
