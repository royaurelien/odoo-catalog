# -*- coding: utf-8 -*-

from multiprocessing import synchronize
from odoo import models, fields, api

import logging
from random import randint

_logger = logging.getLogger(__name__)


class GitRepository(models.Model):
    _name = 'git.repository'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'abstract.git.model']
    _description = 'Git Repository'

    ### GIT ###
    _git_service = "service"
    _git_field_rel = 'branch_ids'
    _git_field_name = 'name'
    _git_type_rel = "o2m"

    path = fields.Char(required=True)
    description = fields.Char()
    repo_id = fields.Integer(string="Repository ID")
    url = fields.Char()
    http_git_url = fields.Char(string="HTTP Url")
    ssh_git_url = fields.Char(string="SSH Url")

    repository_create_date = fields.Datetime(readonly=True)
    repository_update_date = fields.Datetime(readonly=True, tracking=True)

    user_id = fields.Many2one(comodel_name='res.users')
    organization_id = fields.Many2one(comodel_name='git.organization',
                                      index=True,
                                      readonly=True,
                                      ondelete="cascade",)
    service = fields.Selection(related='organization_id.service', store=True)
    branch_ids = fields.One2many(comodel_name='git.branch', inverse_name='repository_id')

    branch_count = fields.Integer(compute='_compute_branch', store=True, string="# Branches")
    branch_major_count = fields.Integer(compute='_compute_branch', store=True, string="# Major Branches")
    custom_addon_count = fields.Integer(compute='_compute_branch', string="# Addons")

    tag_ids = fields.Many2many('custom.addon.tags', string='Tags')

    @api.depends('branch_ids')
    def _compute_branch(self):
        for record in self:
            record.branch_count = len(record.branch_ids)
            record.branch_major_count = len(record.branch_ids.filtered(lambda x: x.major))
            record.custom_addon_count = sum(record.branch_ids.mapped('custom_addon_count'))


    def action_view_git_branch(self):
        self.ensure_one()
        action = self.env.ref("custom_addons.action_view_branch").read()[0]
        action["context"] = dict(self.env.context)
        action["context"].pop("group_by", None)
        action["context"]["search_default_repository_id"] = self.id
        action["domain"] = [('repository_id', '=', self.id)]

        return action

    def action_view_custom_addon(self):
        self.ensure_one()
        action = self.env.ref("custom_addons.action_view_addons").read()[0]
        action["context"] = dict(self.env.context)
        action["context"].pop("group_by", None)
        action["domain"] = [('id', 'in', self.branch_ids.mapped('custom_addon_ids').ids)]

        return action

