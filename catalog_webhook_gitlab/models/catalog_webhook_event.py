from odoo import models, fields


class CatalogWebhookEvent(models.Model):
    _inherit = "catalog.webhook.event"

    service = fields.Selection(selection_add=[("gitlab", "Gitlab")])
