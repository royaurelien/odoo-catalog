# -*- coding: utf-8 -*-


import logging
from random import randint

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class CustomAddonVersion(models.Model):
    _name = "custom.addon.version"
    _description = "Custom Addon Version"

    def _get_default_color(self):
        return randint(1, 11)

    name = fields.Char(required=True)
    color = fields.Integer(default=_get_default_color)
    custom_addon_count = fields.Integer(compute="_compute_addons", string="# Addons")

    _sql_constraints = [
        ("name_uniq", "unique (name)", "Version already exists!"),
    ]

    def _compute_addons(self):
        for record in self:
            branches = self.env["git.branch"].search([("name", "=", record.name)])
            record.custom_addon_count = sum(branches.mapped("custom_addon_count"))

    @api.model
    def search_or_create(self, names):
        names = set(names)
        records = self.search([("name", "in", list(names))])
        to_create = names - set(records.mapped("name"))
        new_records = self.create([{"name": name} for name in to_create])

        return records + new_records
