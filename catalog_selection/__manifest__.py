# -*- coding: utf-8 -*-
{
    'name': "Catalog - Addons Selection",
    'summary': """Selection for the modules catalog""",
    'description': """Selection for the modules catalog""",
    'author': "Aurelien ROY",
    'website': "https://odoo.com",
    'category': 'Technical',
    'version': '14.0.0.1.0',
    'depends': [
        'base',
        'catalog',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/custom_addon_selection.xml',
        'views/custom_addon.xml',
        'wizard/addons_selection_wizard.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'auto_install':False,
    'application': False,
    'license': 'LGPL-3',

}
