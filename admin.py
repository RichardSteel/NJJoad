from django.contrib import admin
from django.db import models
from django.forms import TextInput

# Register your models here.
from .models import InvoicePaid, Student, ArcheryEvent, ArcherScore, JoadSession, JoadRoster

class StudentAdmin(admin.ModelAdmin):
    formfield_overrides = {
        # Django enforces maximum field length of 14 onto 'title' field when user is editing in the change form
        models.CharField: {'widget': TextInput(attrs={'size':'2'})},
        }

admin.site.register(Student,StudentAdmin)
admin.site.register(ArcheryEvent)
admin.site.register(ArcherScore)
admin.site.register(JoadSession)
admin.site.register(JoadRoster)
admin.site.register(InvoicePaid)