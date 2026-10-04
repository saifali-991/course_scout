"""Tests for the two language guards the catalog relies on:

* ``resources.langs`` decides a title's writing system (stdlib ``unicodedata``);
* ``manage.py clean_invalid_titles`` deletes only rows that cannot be English
  or Hindi, and the admin list links the title so rows stay editable.
"""
from io import StringIO

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase

from resources.admin import ResourceAdmin
from resources.langs import foreign_scripts, is_english_or_hindi_title
from resources.models import Resource

ENGLISH = 'Django REST Framework tutorial for beginners'
HINDI = 'Python पूरा कोर्स हिंदी में 2026'
MIXED = 'Figma UI design ट्यूटोरियल part 1'
JAPANESE = 'Photoshop 中級・上級者のイラスト講座【完全版】'
CHINESE = '色彩中级课程 Photoshop 从零开始'
KOREAN = 'illustrator 기초부터 실무까지'
THAI = 'การเรียนรู้ Adobe Illustrator อย่างง่าย'
ARABIC = 'الفوتوشوب من الصفر للاحتراف'
RUSSIAN = 'Перевод на русский язык'


def make(title, **kwargs):
    kwargs.setdefault('url', f'https://example.com/{abs(hash(title)) % 10**9}')
    kwargs.setdefault('platform', Resource.Platform.YOUTUBE)
    kwargs.setdefault('category', 'web-development')
    return Resource.objects.create(title=title, **kwargs)


class ScriptDetectionTests(TestCase):
    def test_english_and_hindi_titles_are_safe(self):
        for title in (ENGLISH, HINDI, MIXED, 'Python 45 ⚡️ — 100% free ©'):
            self.assertEqual(foreign_scripts(title), [], title)
            self.assertTrue(is_english_or_hindi_title(title), title)

    def test_other_scripts_are_reported(self):
        expected = {JAPANESE: ['CJK', 'Hiragana', 'Katakana'],
                    CHINESE: ['CJK'],
                    KOREAN: ['Hangul'],
                    THAI: ['Thai'],
                    ARABIC: ['Arabic'],
                    RUSSIAN: ['Cyrillic']}
        for title, scripts in expected.items():
            self.assertEqual(foreign_scripts(title), scripts, title)
            self.assertFalse(is_english_or_hindi_title(title), title)

    def test_greek_letters_double_as_maths_symbols(self):
        self.assertEqual(foreign_scripts('The dynamics of e^(πi)'), [])
        self.assertEqual(foreign_scripts('Εισαγωγή στην Python'), ['Greek'])

    def test_detect_language_still_tags_hindi_and_english(self):
        from resources.langs import detect_language
        self.assertEqual(detect_language(HINDI), 'hi')
        self.assertEqual(detect_language(ENGLISH), 'en')
        self.assertEqual(detect_language(RUSSIAN), 'ru')


class AdminLinkTests(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser('tester', 't@example.com', 'pw-12345')
        self.resource = make(ENGLISH)

    def test_title_is_the_list_link(self):
        self.assertEqual(ResourceAdmin.list_display_links, ('title',))
        for field in ResourceAdmin.list_display_links:
            self.assertIn(field, ResourceAdmin.list_display)
        # list_editable + list_display_links on the same field = admin.E121
        self.assertNotIn('title', ResourceAdmin.list_editable)

    def test_changelist_links_the_title_and_opens_the_change_form(self):
        self.client.force_login(self.superuser)
        response = self.client.get('/admin/resources/resource/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'>{ENGLISH}</a>')
        self.assertEqual(
            self.client.get(f'/admin/resources/resource/{self.resource.pk}/change/').status_code,
            200)


class CleanInvalidTitlesTests(TestCase):
    def setUp(self):
        self.keep = [make(t) for t in (ENGLISH, HINDI, MIXED)]
        self.drop = [make(t) for t in (JAPANESE, CHINESE, KOREAN, THAI, ARABIC, RUSSIAN)]

    def test_dry_run_deletes_nothing(self):
        out = StringIO()
        call_command('clean_invalid_titles', stdout=out)
        self.assertEqual(Resource.objects.count(), 9)
        self.assertIn('DRY RUN', out.getvalue())

    def test_apply_removes_only_the_foreign_titles(self):
        out = StringIO()
        call_command('clean_invalid_titles', apply=True, stdout=out)
        self.assertEqual(set(Resource.objects.values_list('title', flat=True)),
                         {t.title for t in self.keep})
        self.assertEqual(Resource.objects.count(), 3)
        text = out.getvalue()
        self.assertIn('deleted 6 row(s) · 3 left', text)

    def test_second_run_is_a_no_op(self):
        call_command('clean_invalid_titles', apply=True, stdout=StringIO())
        out = StringIO()
        call_command('clean_invalid_titles', apply=True, stdout=out)
        self.assertIn('nothing to remove', out.getvalue())
        self.assertEqual(Resource.objects.count(), 3)

    def test_latin_marker_rows_survive_without_the_flag(self):
        row = make('Curso completo de Photoshop', language='es')
        call_command('clean_invalid_titles', apply=True, stdout=StringIO())
        self.assertTrue(Resource.objects.filter(pk=row.pk).exists())
        call_command('clean_invalid_titles', apply=True,
                     include_latin_foreign=True, stdout=StringIO())
        self.assertFalse(Resource.objects.filter(pk=row.pk).exists())
