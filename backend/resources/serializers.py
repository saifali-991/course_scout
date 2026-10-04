from rest_framework import serializers

from .categories import get_category
from .creators import is_top_creator
from .langs import language_label as language_name
from .models import Resource


class ResourceSerializer(serializers.ModelSerializer):
    """Card/detail payload — matches exactly what the React UI renders."""

    category_name = serializers.SerializerMethodField()
    platform_name = serializers.CharField(source='get_platform_display', read_only=True)
    level_name = serializers.SerializerMethodField()
    # Never blank: missing thumbnails resolve to a topic-matched stock photo.
    thumbnail_url = serializers.SerializerMethodField()
    # Hand-picked YouTube channels (CodeWithHarry, codebasics, freeCodeCamp …).
    is_top_creator = serializers.SerializerMethodField()
    language_label = serializers.SerializerMethodField()

    class Meta:
        model = Resource
        fields = [
            'id',
            'title',
            'description',
            'url',
            'thumbnail_url',
            'provider',
            'platform',
            'platform_name',
            'category',
            'category_name',
            'resource_type',
            'is_free',
            'price',
            'rating',
            'level',
            'level_name',
            'duration_text',
            'duration_hours',
            'language',
            'language_label',
            'is_top_creator',
            'source',
            'created_at',
        ]

    def get_category_name(self, obj):
        cat = get_category(obj.category)
        return cat['name'] if cat else obj.category

    def get_level_name(self, obj):
        return obj.get_level_display() if obj.level else ''

    def get_thumbnail_url(self, obj):
        return obj.display_thumbnail

    def get_is_top_creator(self, obj):
        return is_top_creator(obj.provider)

    def get_language_label(self, obj):
        return language_name(obj.language)

