# -*- coding: utf-8 -*-
{
    'name': "Custom Addons",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

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
        'mail',
        'custom_auth',
    ],

    # always loaded
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'views/menu.xml',
        'views/git_organization.xml',
        'views/git_repository.xml',
        'views/git_branch.xml',
        'views/git_rules.xml',
        'views/custom_addon.xml',
        'views/custom_addon_tags.xml',
        'views/custom_addon_version.xml',
        'data/mail_message_subtype.xml',
        'data/cron.xml',
        'data/git_rules.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}
