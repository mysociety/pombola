# Moving from pombola.core.models to popolo.models

## Which models need to be considered?

 * `Person`
 * `Organisation` => `Organization`
 * `Position` => `Post`
 * `Contact` => `ContactDetail`
 * `AlternativePersonName` => `OtherName`
 * `InformationSource` => `Source`


## What are the difference in fields provided by the core and popolo models?

### `Person`

Missing from `popolo`:

 * `slug`
 * `hidden`
 * `can_be_featured`
 * `images` => popolo only has one image per Person
 
Changed in `popolo`:

 * `created` and `updated`, from `ModelBase` abstract class are replaced with `created_at` and `updated_at` from `Timestampable` mixin
 * `date_of_birth` => `birth_date`. This and death fields are `CharField` in popolo - might make filtering harder?
  * `title` => `honorific_prefix`


### `Organisation`

This model is named `Organization` in `popolo`.

Missing from `popolo`:

 * `slug`
 * `summary`
 * `kind` is missing; `classification` as a `CharField` seems to serve the same purpose
 * `images`

Changed in `popolo`:

 * `name` is restricted to 128 chars, not 200.


### `Position`

This model has a rough equivalent in `popolo` using `Post` and `Membership`

Missing from `popolo`:

 * `place`
 * `note`
 * `title`, `subtitle`: `label` and `role` might be suitable here
 * `category`
 * `sorting_start_date`
 * `sorting_end_date`
 * `sorting_start_date_high`
 * `sorting_end_date_high`

### `Contact`

This model has an equivalent in `popolo` called `ContactDetail`

Changed in `popolo`:

 * `kind`: instead of a foreign key to `ContactKind` which can hold any type of contact info, `contact_type` is used, and is a `CharField` with a few defined choices.

### `AlternativePersonName`

This model has a rough equivalent in `popolo` called `OtherName`. The `OtherName` model is very simple and stores the name as a single string, instead of structured as family name, given name etc.


### `InformationSource`

This model has an equivalent in `popolo` called `Source`

Missing from `popolo`:

* `entered`



## Things to think about

 * Need to preserve object managers that provide custom filters
 * Need to preserve custom properties, and custom save behaviour/signals
 * Haystack indexes need to be created - perhaps as a PR on django-popolo itself? 
 * What's the rationale for using `CharField` instead of `DateField` in popolo's models?
 
## Notes

Adding `popolo` to `INSTALLED_APPS` causes a `related_name` clash on `popolo.Identifier.content_type` and `core.Identifier.content_type`. Added `related_name="core_identifier_set"` to `core.Identifier`. This doesn't seem to be used anywhere, so is probably safe.


Is it best to migrate models one at a time or all at once? Piecemeal might be tricky thanks to the level of interaction between models.

No way to bulk_create because Django doesn't support that on inherited models.
