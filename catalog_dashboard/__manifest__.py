{
    "name": "Catalog - Dashboard",
    "summary": """Dashboard view for the modules catalog""",
    "description": """Dashboard view for the modules catalog""",
    "author": "Aurelien ROY",
    "website": "https://odoo.com",
    "category": "Technical",
    "version": "14.0.1.0.0",
    "depends": [
        "base",
        "catalog",
        "web_enterprise",
    ],
    "data": [
        "views/assets.xml",
        "views/dashboard.xml",
        "views/menu.xml",
    ],
    "qweb": [
        "static/src/xml/catalog_dashboard.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": False,
    "license": "LGPL-3",
}
