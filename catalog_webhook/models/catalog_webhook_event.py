from odoo import fields, models


class CatalogWebhookEvent(models.Model):
    _name = "catalog.webhook.event"
    _description = "Catalog Webhook Event"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    event = fields.Char(string="HTTP Event")
    description = fields.Char(string="Help")
    service = fields.Selection([])
    active = fields.Boolean(default=True)
