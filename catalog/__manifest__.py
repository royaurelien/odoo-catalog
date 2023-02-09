# -*- coding: utf-8 -*-
{
    "name": "Catalog",
    "summary": """Catalog of modules""",
    "description": """Catalog of modules""",
    "author": "Aurelien ROY",
    "website": "https://odoo.com",
    "category": "Productivity",
    "version": "14.0.1.0.1",
    "depends": [
        "base",
        "mail",
        "custom_auth",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/menu.xml",
        "views/git_organization.xml",
        "views/git_repository.xml",
        "views/git_branch.xml",
        "views/git_commit_items.xml",
        "views/git_contributor.xml",
        "views/git_rules.xml",
        "views/custom_addon.xml",
        "views/custom_addon_tags.xml",
        "views/custom_addon_version.xml",
        "data/mail_message_subtype.xml",
        "data/ir_config.xml",
        "data/ir_cron.xml",
        "data/custom_addon_tags.xml",
        "data/git_rules.xml",
    ],
    "demo": [
        # 'demo/demo.xml',
    ],
    "installable": True,
    "auto_install": False,
    "application": True,
    "license": "LGPL-3",
}
