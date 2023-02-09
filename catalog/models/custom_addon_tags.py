# -*- coding: utf-8 -*-


import logging
from random import randint

from odoo import models, fields

_logger = logging.getLogger(__name__)


class CustomAddonTags(models.Model):
    _name = "custom.addon.tags"
    _description = "Custom Addon Tags"

    def _get_default_color(self):
        return randint(1, 11)

    name = fields.Char(required=True)
    color = fields.Integer(default=_get_default_color)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists!"),
    ]
