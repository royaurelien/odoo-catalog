# -*- coding: utf-8 -*-


import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class CatalogWebhookEvent(models.Model):
    _inherit = "catalog.webhook.event"

    service = fields.Selection(selection_add=[("gitlab", "Gitlab")])
