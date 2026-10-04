from django.contrib import admin
from django.contrib.auth.models import User
from django.utils.html import format_html

from .creators import is_top_creator
from .models import Resource, UserProfile


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = (
        'thumb_preview',
        'title',
        'provider',
        'platform',
        'category',
        'resource_type',
        'language',
        'top_creator',
        'is_free',
        'rating',
        'is_active',
        'source',
    )
    # The first column is an image, so link the title instead — without this the
    # admin list has no clickable link at all (an <img> is not a link target).
    # NB: never list a field here that is also in `list_editable` (Django's
    # check admin.E121 refuses that with a system-check error).
    list_display_links = ('title',)
    # language / is_active live here so hidden (non English-Hindi) rows can be
    # inspected and brought back after `manage.py apply_languages --apply`
    list_filter = ('category', 'platform', 'resource_type', 'language', 'is_active',
                   'is_free', 'level', 'source')
    search_fields = ('title', 'provider', 'description', 'url')
    ordering = ('-created_at',)
    list_per_page = 50

    @admin.display(description='Image')
    def thumb_preview(self, obj):
        """Small preview — uses the same resolution as the API (photo fallback)."""
        return format_html(
            '<img src="{}" alt="" loading="lazy" style="width:76px;height:44px;'
            'object-fit:cover;border-radius:6px;background:#e8eef7" />',
            obj.display_thumbnail,
        )

    @admin.display(boolean=True, description='★ top creator')
    def top_creator(self, obj):
        """True for channels hand-picked in resources/creators.py (see /api/creators/)."""
        return is_top_creator(obj.provider)



class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile (interests)'


class UserAdmin(admin.ModelAdmin):
    inlines = (UserProfileInline,)


try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:  # pragma: no cover
    pass
admin.site.register(User, UserAdmin)

