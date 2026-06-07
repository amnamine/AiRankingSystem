from django import template

register = template.Library()

@register.filter
def split(value, delimiter=','):
    """Split a string by delimiter."""
    if not value:
        return []
    return [item.strip() for item in value.split(delimiter) if item.strip()]

@register.filter
def score_class(value):
    """Return CSS class based on score value."""
    try:
        val = float(value)
        if val >= 70:
            return 'high'
        elif val >= 40:
            return 'medium'
        return 'low'
    except (ValueError, TypeError):
        return 'low'
