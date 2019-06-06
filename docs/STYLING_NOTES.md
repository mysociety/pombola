# Styling a Pombola site

These notes cover how the styling currently works, but it is almost certainly **not the best way** and needs improving, which will hopefully be done as part of a larger refactor to make it easier to reuse the codebase across several countries.

## SASS and CSS

The CSS is generated from SASS, which is all in the `sass` dir of [pombola/core/static/]*(https://github.com/mysociety/pombola/tree/master/pombola/core/static), and is compiled into the `css` dir.

You can compile the SASS using `make css` in the project root. This uses [compass](http://compass-style.org/) but could probably be changed to just use sass.

The main entry point for the SASS is the `<country_name>.scss` file. These are largely similar and let you include or not styles specific to the various apps. Note that often these will contain entries like:

``` scss
@import "colours_kenya";
/// ... snip ...
@import "kenya_overrides";
```

All the `.scss` files should be considered generic for all countries apart from ones like those above, that contain specific tweaks for the specific country.

## Templates

All the templates in `core` and the other apps should be kept generic. Country specific templates should go into the countries app and will be used in preference to the generic ones. If you find yourself needing to change a bit of html for just one country feel free to break it out into a template.

The templates that you will most likely want to look at are in [templates](https://github.com/mysociety/pombola/tree/master/pombola/templates) as these are the ones that are used site wide.

Your app will have a `base.html` template that should extend `default_base.html`. Likewise you will most likely want to change `main_menu.html` to include links specific for your site.

## Static assets (images, js, etc)

Novel assets, and overrides, should go into `/pombola/<country_app>/static` (eg [Kenya's](https://github.com/mysociety/pombola/tree/master/pombola/kenya/static)). Anything that appears here will be used in preference to assets from the core or other apps.
