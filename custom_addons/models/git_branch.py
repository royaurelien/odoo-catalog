# -*- coding: utf-8 -*-

from multiprocessing import synchronize
from odoo import models, fields, api

import logging
from random import randint

_logger = logging.getLogger(__name__)


class GitBranch(models.Model):
    _name = 'git.branch'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Git Branch'

    name = fields.Char(required=True, tracking=True)
    url = fields.Char()

    last_commit_message = fields.Char()
    last_commit_author = fields.Char()
    last_commit_short_id = fields.Char()
    last_commit_url = fields.Char()

    active = fields.Boolean(default=True)
    major = fields.Boolean(default=False)
    requirements = fields.Boolean(default=False)
    python_modules = fields.Char()
    odoo_version = fields.Char()
    is_synchronized = fields.Boolean(default=False, tracking=True)


    repository_id = fields.Many2one(comodel_name='git.repository')
    organization_id = fields.Many2one(related='repository_id.organization_id', store=True)
    service = fields.Selection(related='repository_id.organization_id.service', store=True)
    partner_id = fields.Many2one(related='repository_id.partner_id', store=True)
    user_id = fields.Many2one(comodel_name='res.users')
    path = fields.Char(related='repository_id.path', store=True)

    tag_ids = fields.Many2many('custom.addon.tags', string='Tags')

    custom_addon_ids = fields.Many2many(
        string="Custom Addons",
        comodel_name="custom.addon",
        relation="git_branch_custom_addon_rel",
        column1="branch_id",
        column2="custom_addon_id",
        tracking=True,
    )

    # def name_get(self):
    #     return [(record.id, "{o.path} / {o.name}".format(o=record)) for record in self]

    custom_addon_count = fields.Integer(compute='_compute_custom_addon', store=True)

    @api.depends('custom_addon_ids')
    def _compute_custom_addon(self):
        for record in self:
            record.custom_addon_count = len(record.custom_addon_ids)


    def action_view_custom_addon(self):
        self.ensure_one()
        action = self.env.ref("custom_addons.action_view_addons").read()[0]
        action["context"] = dict(self.env.context)
        action["context"].pop("group_by", None)
        action["domain"] = [('id', 'in', self.custom_addon_ids.ids)]

        return action

    def _action_sync_addons(self):
        for service in self.mapped('repository_id.service'):
            records = self.filtered(lambda x: x.repository_id.service == service)
            method_name = "_action_sync_addons_{}".format(service)
            method = getattr(records, method_name) if hasattr(records, method_name) else False
            if method:
                method()
        return True


    def action_sync_addons(self):
        return self._action_sync_addons()

    # def _track_subtype(self, init_values):
    # # init_values contains the modified fields' values before the changes
    # #
    # # the applied values can be accessed on the record as they are already
    # # in cache
    # self.ensure_one()
    # if 'state' in init_values and self.state == 'confirmed':
    #     return self.env.ref('my_module.mt_state_change')
    # return super(BusinessTrip, self)._track_subtype(init_values)