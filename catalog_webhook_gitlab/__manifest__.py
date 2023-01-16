# -*- coding: utf-8 -*-
{
    'name': "Catalog - Webhook (Gitlab)",
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
        'catalog_webhook',
    ],
    'data': [
        'data/webhook.xml',
    ],
    'installable': True,
    'auto_install':False,
    'application': False,
    'license': 'LGPL-3',

}
