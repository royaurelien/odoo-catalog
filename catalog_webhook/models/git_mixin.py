# -*- coding: utf-8 -*-

from multiprocessing import synchronize

from odoo import models, fields, api, _
from odoo.addons.catalog.models.git_mixin import XML_ACTIONS

import logging

_logger = logging.getLogger(__name__)

XML_ACTIONS.update({
    'webhook': "catalog_webhook.action_view_webhook",
})

class GitMixin(models.AbstractModel):
    _inherit = "git.mixin"


    def action_view_webhook(self):
        return self._action_view('webhook', context=dict(create=True))
