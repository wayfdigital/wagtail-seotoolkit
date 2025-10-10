"""
Wagtail hooks for SEO Toolkit
"""

from wagtail import hooks
from wagtail.admin.menu import MenuItem


@hooks.register('register_admin_menu_item')
def register_seo_toolkit_menu_item():
    """
    Add SEO Toolkit menu item to Wagtail admin
    """
    return MenuItem(
        'SEO Toolkit',
        '#',  # Does nothing when clicked
        icon_name='cog',
        order=1000
    )
