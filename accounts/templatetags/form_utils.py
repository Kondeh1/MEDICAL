"""
Form rendering: use django-crispy-forms if installed, otherwise fall back to form.as_p().
Use in templates as: {% load form_utils %} ... {{ form|crispy }}
"""
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def crispy(form):
    """Render form with crispy_forms if available, else as_p()."""
    if form is None:
        return ""
    try:
        from crispy_forms.utils import render_crispy_form
        return mark_safe(render_crispy_form(form))
    except ImportError:
        return form.as_p()
