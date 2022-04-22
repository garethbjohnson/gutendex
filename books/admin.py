from django.contrib import admin

# Register your models here.
from django.apps import apps


from books.models import Book, Format

class FormatVariableInline(admin.TabularInline):
    model = Format
    fieldsets = (
        (None, {
            'fields': ('book', 'mime_type', 'url')
        }),)

class BookAdmin(admin.ModelAdmin):
    inlines = [
        FormatVariableInline,
    ]


admin.site.register(Book, BookAdmin)

models = apps.get_models()

for model in models:
    try:
        admin.site.register(model)
    except admin.sites.AlreadyRegistered:
        #already registered
        pass