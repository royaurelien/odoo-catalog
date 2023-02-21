# -*- coding: utf-8 -*-


import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class GitRepository(models.Model):
    _inherit = "git.repository"

    webhook_ids = fields.One2many(
        comodel_name="catalog.webhook", inverse_name="repository_id"
    )
    webhook_count = fields.Integer(compute="_compute_webhook")

    @api.depends("webhook_ids")
    def _compute_webhook(self):
        for record in self:
            record.webhook_count = len(record.webhook_ids)

    def _action_view_webhook(self, action):
        action["domain"] = [("id", "in", self.webhook_ids.ids)]
        action["context"].update(
            {
                "default_repository_id": self.id,
            }
        )

        return action
