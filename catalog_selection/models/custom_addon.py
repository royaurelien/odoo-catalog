# -*- coding: utf-8 -*-

from multiprocessing import synchronize
from odoo import models, fields, api, _

import logging
import os
from random import randint

_logger = logging.getLogger(__name__)


class CustomAddon(models.Model):
    _inherit = "custom.addon"

    def action_add_to_selection(self):
        return self.env["custom.addon.selection"]._add_to_selection(self.ids)
