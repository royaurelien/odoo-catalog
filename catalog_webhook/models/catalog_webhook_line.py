from odoo import models, fields


class CatalogWebhookEvent(models.Model):
    _name = "catalog.webhook.line"
    _description = "Catalog Webhook line"

    webhook_id = fields.Many2one("catalog.webhook", required=True)
    event_id = fields.Many2one("catalog.webhook.event", required=True)
    code = fields.Char(related="event_id.code")
    description = fields.Char(related="event_id.description")
    action = fields.Selection([("post", "Post message")])
    active = fields.Boolean(default=True)
