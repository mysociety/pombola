import autocomplete_light

from .models import Category, Tag

autocomplete_light.register(Category, search_fields=['name'] )
autocomplete_light.register(Tag,      search_fields=['name'] )
