from django.contrib import admin
from core.models import Prompt, Generation, Annotation, Playlist, Profile, FeedbackOption

admin.site.site_header = 'Annotation Data'

admin.site.register(Profile)
admin.site.register(Prompt)
admin.site.register(Generation)
admin.site.register(Annotation)
admin.site.register(Playlist)
admin.site.register(FeedbackOption)
