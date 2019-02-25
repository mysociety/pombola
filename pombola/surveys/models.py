from sorl.thumbnail import ImageField

from django.db import models


class Survey(models.Model):
  label = models.CharField(max_length=200, help_text="For your reference only. This label isn't displayed on the public website.")
  image = ImageField(upload_to='surveys')
  url = models.URLField()
  created = models.DateTimeField(auto_now_add=True)
  updated = models.DateTimeField(auto_now=True)

  def __str__(self):
    return self.label

  class Meta:
    get_latest_by = "created"
