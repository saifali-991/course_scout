from django.db import models

from .categories import CATEGORY_CHOICES
from .thumbnails import resolve_thumbnail


class Resource(models.Model):
    """A learning resource (course / video / certificate) aggregated from
    external platforms. We only ever store URLs — never the media files."""

    class Platform(models.TextChoices):
        COURSERA = 'coursera', 'Coursera'
        EDX = 'edx', 'edX'
        YOUTUBE = 'youtube', 'YouTube'
        FREECODECAMP = 'freecodecamp', 'freeCodeCamp'
        MIT_OCW = 'mit_ocw', 'MIT OpenCourseWare'
        NPTEL = 'nptel', 'NPTEL'
        KHAN_ACADEMY = 'khan_academy', 'Khan Academy'
        CS50 = 'cs50', 'CS50'
        THE_ODIN_PROJECT = 'the_odin_project', 'The Odin Project'
        UNACADEMY = 'unacademy', 'Unacademy'
        PHYSICS_WALLAH = 'physics_wallah', 'Physics Wallah'
        OTHER = 'other', 'Other'

    class ResourceType(models.TextChoices):
        COURSE = 'course', 'Course'
        YOUTUBE = 'youtube', 'YouTube'
        VIDEO = 'video', 'Video'
        CERTIFICATE = 'certificate', 'Certificate'
        TUTORIAL = 'tutorial', 'Tutorial'
        PLAYLIST = 'playlist', 'Playlist'

    class Level(models.TextChoices):
        BEGINNER = 'beginner', 'Beginner'
        INTERMEDIATE = 'intermediate', 'Intermediate'
        ADVANCED = 'advanced', 'Advanced'
        ALL = 'all', 'All levels'

    title = models.CharField(max_length=300)
    description = models.TextField(blank=True, default='')
    url = models.URLField(max_length=500, unique=True)  # dedupe key
    thumbnail_url = models.TextField(blank=True, default='')  # URL or SVG data-URI
    provider = models.CharField(max_length=200, blank=True, default='')
    platform = models.CharField(
        max_length=30, choices=Platform.choices, default=Platform.OTHER
    )
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    resource_type = models.CharField(
        max_length=20, choices=ResourceType.choices, default=ResourceType.COURSE
    )
    is_free = models.BooleanField(default=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    rating = models.FloatField(null=True, blank=True)  # 0–5
    level = models.CharField(max_length=20, choices=Level.choices, blank=True, default='')
    duration_text = models.CharField(max_length=100, blank=True, default='')
    duration_hours = models.FloatField(null=True, blank=True)
    language = models.CharField(max_length=10, default='en')
    source = models.CharField(max_length=30, blank=True, default='')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-rating', '-created_at']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['is_free']),
            models.Index(fields=['platform']),
            models.Index(fields=['rating']),
        ]

    def __str__(self):
        return self.title

    @property
    def display_thumbnail(self):
        """Image for the card: YouTube frame / source thumbnail, else a topic photo.

        Kaggle-sourced rows carry no image, so they resolve to a stock photo
        chosen from the resource id (stable per course). Falls back to the SVG
        gradient only if the category has no photo pool at all.
        """
        return resolve_thumbnail(
            self.thumbnail_url, self.category, self.pk or self.url,
            self.title, self.provider or 'CourseScout', url=self.url)


class UserProfile(models.Model):
    """Per-user interests (category slugs) used by the recommendations API."""

    user = models.OneToOneField(
        'auth.User', on_delete=models.CASCADE, related_name='profile'
    )
    interests = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s profile"
