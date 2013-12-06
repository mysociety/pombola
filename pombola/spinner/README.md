# Spinner

The spinner is a content box in which various slides are shown. It is possible
to go forward and back through them on the page. Reloading the page gives you a
random slide. Originally for Pombola Kenya the slide content was always a
person, this app extends that to let you have any content of each silde.

## TODO

- Better admin interface for adding slides (selecting the `content_type` and
  manually specifying `id` is fiddly and error prone).

- Replace featured persons with spinner on non-ZA sites.

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

### Image and Quote content

As these are likely to be wanted (and useful for testing) they are provided as
part of the spinner app.

## Working with the admin

To create a new slide go to the admin and then Spinner -> Slide -> add new.
Unfortunately the default admin make you select the content type from the drop
down list, where there are multiple entries for some `content_types` (notably
`person` - one from core, one from popit). If you choose the wrong one, change
to the other one (I know that's not very helpful, sorry).

You also need to select the id`` of the item you are adding manually. This is
easiest done by goin to the admin page for the person etc you want to add a
slide for and then copying down the number at the end of the URL in the address
bar.

## Templates and design

The templates that are used to generate the spinner are intended to be simple
to use and override for country specific branding.

### spinner/carousel-slides.html

This is almost certainly what you want to use when displaying the spinner.

''' html
<div id="home-carousel" class="carousel">
  {% include "spinner/carousel-slides.html" %}
</div>
```

You'll need to include some javascript and css on the page you use it (see
comments in the template file). You do not need to add the slides to the
template context, they are loaded using a template tag in `carousel.html`.

### spinner/display-slide.html

Calls the appropiate template for the slide with `slide` as the slide, and
`object` as the thing the slide contains. A very thin wrapper.

### spinner/slides/<some-app_some-model>.html

This is a template specific to the content object of the slide. You will almost
certainly have to create these templates. Possibly in your country specific app
if they need distinct styling.

### spinner/slides/default.html

A default template that is used if a template like
`spinner/slides/<some-app_some-model>.html` can not be found. It is
intentionally ugly and contains instructions to create a specific template for
the content object.

## Present, but unused code

## Replacing featured person code
