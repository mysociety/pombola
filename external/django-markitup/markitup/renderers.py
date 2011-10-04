try:
    from docutils.core import publish_parts
    def render_rest(markup, **docutils_settings):
        parts = publish_parts(source=markup, writer_name="html4css1", settings_overrides=docutils_settings)
        return parts["html_body"]
except ImportError:
    pass
