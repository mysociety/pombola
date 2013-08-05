from django.contrib import admin
from user_profile.models import UserProfile

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_profile_public', 'twitter', 'facebook')
    list_filter = ('is_profile_public',)
    raw_id_fields = ('user',)
    search_fields = ('user',)


# We want to put the user profile with the users and groups in the 'auth'
# section of the admin. Do this by creating a proxy and then fiddling with its
# app_label. Also need to give it a new verbose_name.
class UserProfileProxy(UserProfile):
    class Meta():
        proxy = True
        app_label='auth'
        verbose_name = "user profile"

# Register the proxy
admin.site.register(UserProfileProxy, UserProfileAdmin)
