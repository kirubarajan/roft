from django.contrib import admin
from core.models import Prompt, Tag, EvaluationText, Annotation, Group

admin.site.site_header = 'Annotation Data'

admin.site.register(Prompt)
admin.site.register(Tag)
admin.site.register(EvaluationText)
admin.site.register(Annotation)
admin.site.register(Group)