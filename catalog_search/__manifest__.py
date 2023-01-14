# -*- coding: utf-8 -*-
{
    'name': "Catalog - Advanced Search",
    'summary': """Search method for the modules catalog""",
    'description': """Search method for the modules catalog""",
    'author': "Aurelien ROY",
    'website': "https://odoo.com",
    'category': 'Technical',
    'version': '14.0.0.1.0',
    'depends': [
        'base',
        'catalog',
        'base_search_fuzzy',
    ],
    'data': [
        'data/index.xml',
        'views/custom_addon.xml',
    ],
    'installable': True,
    'auto_install':False,
    'application': False,
    'license': 'LGPL-3',

}
