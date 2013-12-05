from django.test import TestCase

from .models import Slide

class ModelTest(TestCase):

    fixtures = ['test_data.json']

    def test_active(self):
        self.assertEqual(
            set(
                Slide.objects.all().active().values_list('id', flat=True)
            ),
            set([1, 3])
        )

    def test_inactive(self):
        self.assertEqual(
            set(
                Slide.objects.all().inactive().values_list('id', flat=True)
            ),
            set([2])
        )

    def test_random_slide(self):
        """
        Test that we get back a random active slide. Do this by running many
        times and then checking that all activo slides are in the returned data.
        """

        seen_slide_ids = set()

        for i in range(100):
            slide = Slide.objects.random_slide()
            seen_slide_ids.add(slide.id)

        for slide in Slide.objects.all().active():
            self.assertTrue(slide.id in seen_slide_ids)
        for slide in Slide.objects.all().inactive():
            self.assertFalse(slide.id in seen_slide_ids)
