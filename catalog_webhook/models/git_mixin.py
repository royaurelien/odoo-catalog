# -*- coding: utf-8 -*-

import logging

from odoo import models
from odoo.addons.catalog.models.git_mixin import XML_ACTIONS


_logger = logging.getLogger(__name__)

XML_ACTIONS.update(
    {
        "webhook": "catalog_webhook.action_view_webhook",
    }
)


class GitMixin(models.AbstractModel):
    _inherit = "git.mixin"

    def action_view_webhook(self):
        """
        Open webhook views
        """
        return self._action_view("webhook", context=dict(create=True))
