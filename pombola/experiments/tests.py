from .models import Experiment

from django.test import TestCase

class ExperimentTest(TestCase):

    def setUp(self):
        self.experiment = Experiment.objects.create(
            name = 'Example Experiment',
            slug = 'example')
        self.event_1 = self.experiment.event_set.create(
            extra_data = '{"foo": 1, "bar": 2}',
        )
        self.event_2 = self.experiment.event_set.create(
            extra_data = '{"foo": 3, "quux": 2}'
        )

    def test_extra_fields(self):
        self.assertEqual(
            self.experiment.extra_fields,
            set(['foo', 'bar', 'quux']))

    def tearDown(self):
        self.event_1.delete()
        self.event_2.delete()
        self.experiment.delete()
