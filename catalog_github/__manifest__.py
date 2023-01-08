# -*- coding: utf-8 -*-
{
    'name': "Catalog - Github Connector",
    'summary': """Github connector for the modules catalog""",
    'description': """Github connector for the modules catalog""",
    'author': "Aurelien ROY",
    'website': "https://odoo.com",
    'category': 'Productivity',
    'version': '14.0.1.0.0',
    'depends': [
        'base',
        'catalog',
    ],
    'data': [
        # 'security/ir.model.access.csv',
        'data/data.xml',
        # 'views/menu.xml',
        # 'views/views.xml',
    ],
    'demo': [
        # 'demo/demo.xml',
    ],
    'installable': True,
    'auto_install':False,
    'application': False,
    'license': 'LGPL-3',

}
