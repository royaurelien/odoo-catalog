{
    "name": "Catalog - Gitlab Connector",
    "summary": """Gitlab connector for the modules catalog""",
    "description": """Gitlab connector for the modules catalog""",
    "author": "Aurelien ROY",
    "website": "https://odoo.com",
    "category": "Productivity",
    "version": "14.0.1.0.0",
    "depends": [
        "base",
        "catalog",
    ],
    "data": [
        # 'security/ir.model.access.csv',
        # 'views/menu.xml',
        "views/git_organization.xml",
    ],
    "demo": [
        # 'demo/demo.xml',
    ],
    "installable": True,
    "auto_install": False,
    "application": False,
    "license": "LGPL-3",
}
