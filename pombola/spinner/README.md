# Spinner

The spinner is a content box in which various slides are shown. It is possible
to go forward and back through them on the page. Reloading the page gives you a
random slide. Originally for Pombola Kenya the slide content was always a
person, this app extends that to let you have any content of each silde.

## Concepts

### Spinner

This is the content area that the slides are shown on. For now there is only
one spinner per site (eg you can't have a "Homepage" spinner and an "About Us"
page spinner). As such there is no model class for the spinner.

### Slides

A piece of content that can be shown on the spinner is a `slide`. There is a
model that represents slides, wether they are active, what the sort order is
and what the actual content of them is.

### Slide Content

The slides simply reference the content that should be displayed on them using
Django's [contenttypes
framework](https://docs.djangoproject.com/en/dev/ref/contrib/contenttypes/).
How the content is displayed is determined by the `app_label` of the referenced
object which is used to select the template to render.
