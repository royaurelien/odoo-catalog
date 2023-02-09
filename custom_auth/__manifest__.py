# -*- coding: utf-8 -*-
{
    "name": "Custom Authentication Management",
    "summary": """Custom authentication management""",
    "description": """Custom authentication management""",
    "author": "Aurelien ROY",
    "website": "http://www.odoo.com",
    "category": "Technical",
    "version": "14.0.1.0.0",
    "depends": ["base"],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/custom_auth.xml",
    ],
    "demo": [],
    "installable": True,
    "auto_install": False,
    "application": False,
    "license": "LGPL-3",
}
