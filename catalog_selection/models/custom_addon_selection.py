# -*- coding: utf-8 -*-

from multiprocessing import synchronize
from odoo import models, fields, api, _

import logging
import os
from random import randint

_logger = logging.getLogger(__name__)


class CustomAddonSelection(models.Model):
    _name = 'custom.addon.selection'
    _description = 'Custom Addons Selection'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'git.mixin']

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    user_id = fields.Many2one('res.users', string='Responsible', required=True, default=lambda self: self.env.user)
    tag_ids = fields.Many2many('custom.addon.tags', string='Tags')

    custom_addon_ids = fields.Many2many(
        string="Custom Addons",
        comodel_name="custom.addon",
        relation="custom_addon_selection_rel",
        column1="selection_id",
        column2="custom_addon_id",
        tracking=True,
    )

    custom_addon_count = fields.Integer(compute='_compute_custom_addon', store=True)
    note = fields.Html()

    @api.depends('custom_addon_ids')
    def _compute_custom_addon(self, context=None):
        for record in self:
            record.custom_addon_count = len(record.custom_addon_ids)


    def _action_view_custom_addons(self, action):
        action["domain"] = [('id', 'in', self.custom_addon_ids.ids)]

        return action


    @api.model
    def _add_to_selection(self, ids):
        view_id = self.env.ref('catalog_selection.addons_selection_wizard_view_form').id
        vals = {
            'custom_addon_ids': [(6, 0, ids)],
        }

        wizard = self.env['addons.selection.wizard'].create(vals)

        return {
            'name': _('Add to selection'),
            'view_mode': 'form',
            'res_model': 'addons.selection.wizard',
            'view_id': view_id,
            'views': [(view_id, 'form')],
            'type': 'ir.actions.act_window',
            'res_id': wizard.id,
            'target': 'new',
        }