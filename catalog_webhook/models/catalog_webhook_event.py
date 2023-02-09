# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

import logging


_logger = logging.getLogger(__name__)


class CatalogWebhookEvent(models.Model):
    _name = "catalog.webhook.event"
    _description = "Catalog Webhook Event"

    name = fields.Char(required=True, string="Name")
    code = fields.Char(required=True, string="Code")
    event = fields.Char(string="HTTP Event")
    description = fields.Char(string="Help")
    service = fields.Selection([], string="Service")
    active = fields.Boolean(default=True)
