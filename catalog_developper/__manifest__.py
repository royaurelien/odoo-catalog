# -*- coding: utf-8 -*-
{
    'name': "Catalog - Developper",
    'summary': """Add developpement's capabilities for catalog application""",
    'description': """Add developpement's capabilities for catalog application """,
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
        # 'views/custom_addon_selection.xml',
        'views/git_organization.xml',
        'wizard/create_repository.xml',
        # 'views/menu.xml',
    ],
    'installable': True,
    'auto_install':False,
    'application': False,
    'license': 'LGPL-3',

}
