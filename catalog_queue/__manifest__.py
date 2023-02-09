# -*- coding: utf-8 -*-
{
    "name": "Catalog - Job Queue",
    "summary": """Job Queue for the modules catalog""",
    "description": """Job Queue for the modules catalog""",
    "author": "Aurelien ROY",
    "website": "https://odoo.com",
    "category": "Technical",
    "version": "14.0.0.1.0",
    "depends": [
        "base",
        "catalog",
        "queue_job",
        "queue_job_batch",
        "web_notify",
    ],
    "data": [
        "security/security.xml",
        "data/channel.xml",
        "views/actions.xml",
    ],
    "demo": [
        # 'demo/demo.xml',
    ],
    "installable": True,
    "auto_install": False,
    "application": False,
    "license": "LGPL-3",
}
