from django import template

register = template.Library()

@register.filter
def ultimos_digitos(value):
    """Devuelve los últimos 4 caracteres de una cadena."""
    if isinstance(value, str) and len(value) >= 4:
        return value[-4:]
    return value