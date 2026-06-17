from django import template

register = template.Library()


@register.filter
def dict_get(dictionary, key):
    """Позволяет обращаться к словарю по ключу в шаблоне: {{ my_dict|dict_get:key }}"""
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None
