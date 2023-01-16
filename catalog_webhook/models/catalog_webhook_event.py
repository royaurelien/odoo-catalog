# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

import logging


_logger = logging.getLogger(__name__)



class CatalogWebhookEvent(models.Model):
    _name = 'catalog.webhook.event'
    _description = 'Catalog Webhook Event'

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    description = fields.Char()
    service = fields.Selection([])
    active = fields.Boolean(default=True)

