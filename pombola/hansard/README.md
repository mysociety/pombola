# Notes on importing Kenyan Parliament PDFs


## pdftohtml version differences

To do the conversion more easily it is useful if the generated HTML has bold and italic flags in it. Different versions of pdftohtml produce different results.

### pdftohtml version 0.40:

  * installed on Mac using `brew install pdftohtml`
  * does not output `<b>` or `<i>` tags (in HTML or XML).
  * Attempting to install the latest not-experimental version (0.39) results in compilation errors

### pdftohtml version 0.12.4:

  * installed on debian squeeze using `apt-get install poppler-utils`
  * does produce the `<b>` and `<i>` tags

### pdftohtml version 0.18.4:

  * installed on debian wheezy using `apt-get install poppler-utils`
  * As 0.12.4 except html doctype different, ends tags with `/>` where appropriate and uses `&#160;` instead of `&nbsp`. Otherwise output identical so tests and code should be easy to adapt.

