# -*- coding: utf-8 -*-
{
    'name': "Custom Addons Job Queue",

    'summary': """
        Asynchronously Jobs""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Aurelien ROY",
    'website': "https://odoo.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'custom_addons',
        'queue_job',
        'queue_job_batch',
        'web_notify',
    ],

    # always loaded
    'data': [
        'security/security.xml',
        'views/actions.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}
