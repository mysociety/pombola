from django.core.urlresolvers import reverse, resolve

from models import MP
from core.models import Person

import pprint

def process(request):
    print 'WaHooooo!!!!'
    rs = resolve(request.path_info)
    if rs.url_name is 'person':
        slug = rs.kwargs['slug']
        person = Person.objects.get(slug=slug)
        return dict(mp=MP.objects.get(person=person))
    return {}



# SUB_MENU = dict(
#     Sales=(
#         ('sales_cart', 'Cart'),
#         #('sales_history', 'History'),
#         #('credit_notes', 'Credit Notes')
#     ),
#     Products=(
#         ('products_list', 'Products'),
#         ('brands_list', 'Brands'),
#         ('categories_list', 'Categories'),
#     ),
#     Customers=(
#         ('customers_list', 'Customers'),
#         #('suppliers_list', 'Suppliers'),
#         #('staff_list', 'Staff')
#     ),
#     Reports=(
#         ('sales_by_day', 'Sales by Day'),
#         ('sales_by_month', 'Month'),
#         # ('sales_by_year', 'Year'),
#         # ('sales_by_popularity', 'Popularity'),
#         # ('sales_by_category', 'Category'),
#         # ('sales_by_brand', 'Brand'),
#         # ('sales_by_staff', 'Staff'),
#     ),
#     Settings=()
# )

# MENU = dict()

# for key in SUB_MENU:
#     xs = SUB_MENU[key]
#     for key1, _ in xs:
#         MENU.update({key1: key})


# LEFT_MENU_ITEMS = (('Sales', reverse('sales_cart')),
#                    ('Products', reverse('products_list')),
#                    ('Contacts', reverse('contacts')),
#                    ('Reports', '#'))

# RIGHT_MENU_ITEMS = (('Settings', '#'),
#                     ('Logout', '#'))

# SUB_MENU_ITEMS = dict()

# def sub_menu_items(key):
#     if not key in SUB_MENU_ITEMS:
#         xs = SUB_MENU[key]
#         SUB_MENU_ITEMS[key] = [(title, reverse(url_name)) \
#                                for url_name, title in xs]
#     return SUB_MENU_ITEMS[key]

# def active_sub_title(url_name):
#     active_title = MENU[url_name]
#     xs = SUB_MENU[active_title]
#     for name, title in xs:
#         if name == url_name:
#             return title
#     return None

# def menu(request):
#     if request.is_ajax():
#         return {}
    
#     url_name = resolve(request.path_info).url_name
#     try:
#         active_title = MENU[url_name]
#         sub_menu = sub_menu_items(active_title)
#     except KeyError:
#         active_title = None
#         sub_menu = None
#     # try:
#     #     active_sub_title = SUB_MENU.get(active_title).get(url_name)
#     # except KeyError:
#     #     active_sub_title = None
    
#     try:
#       sub_title = active_sub_title(url_name)
#     except:
#       sub_title = None

#     return dict(LEFT_MENU=LEFT_MENU_ITEMS,
#                 SUB_MENU=sub_menu,
#                 ACTIVE_TITLE=active_title,
#                 ACTIVE_SUB_TITLE=sub_title)
