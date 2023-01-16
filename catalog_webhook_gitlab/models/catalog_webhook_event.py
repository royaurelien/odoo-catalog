# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

import logging


_logger = logging.getLogger(__name__)



class CatalogWebhookEvent(models.Model):
    _inherit = 'catalog.webhook.event'


    service = fields.Selection(selection_add=[('gitlab', 'Gitlab')])

