# -*- coding: utf-8 -*-

import logging
from uuid import uuid4

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class GitOrganization(models.Model):
    _inherit = "git.organization"

    webhook_enable = fields.Boolean(default=False, string="Webhook")
    webhook_token = fields.Char(string="Webhook token", index=True)

    @api.model
    def _generate_token(self):
        return str(uuid4())

    @api.onchange("webhook_enable")
    def _onchange_webhook(self):
        if self.webhook_enable:
            self.webhook_token = self._generate_token()
        else:
            self.webhook_token = False

    @api.model
    def _get_tokens(self):
        records = self.search(
            [("webhook_enable", "=", True), ("webhook_token", "!=", False)]
        )
        return records.mapped("webhook_token")
