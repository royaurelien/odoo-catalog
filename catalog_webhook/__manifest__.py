# -*- coding: utf-8 -*-
{
    'name': "Catalog - Webhook",
    'summary': """Manage webhook for catalog application""",
    'description': """Manage webhook for catalog application """,
    'author': "Aurelien ROY",
    'website': "https://odoo.com",
    'category': 'Technical',
    'version': '14.0.0.1.0',
    'depends': [
        'base',
        'catalog',
        'catalog_developper',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/git_organization.xml',
        'views/git_repository.xml',
        'views/catalog_webhook.xml',
        'views/catalog_webhook_event.xml',
        # 'wizard/create_repository.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'auto_install':False,
    'application': False,
    'license': 'LGPL-3',

}