{
    "name": "Catalog",
    "summary": """Catalog of modules""",
    "description": """Catalog of modules""",
    "author": "Aurelien ROY",
    "website": "https://odoo.com",
    "category": "Productivity",
    "version": "17.0.1.0.0",
    "depends": [
        "base",
        "mail",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/menu.xml",
        "views/catalog_template.xml",
        "views/catalog_entry.xml",
    ],
    "demo": [
        # 'demo/demo.xml',
    ],
    "installable": True,
    "auto_install": False,
    "application": True,
    "license": "LGPL-3",
}
