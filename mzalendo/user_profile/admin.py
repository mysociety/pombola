from django.contrib import admin
from user_profile.models import UserProfile

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_profile_public', 'twitter', 'facebook')
    list_filter = ('is_profile_public',)
    raw_id_fields = ('user',)
    search_fields = ('user',)

admin.site.register(UserProfile, UserProfileAdmin)
