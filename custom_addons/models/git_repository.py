# -*- coding: utf-8 -*-

from multiprocessing import synchronize
from odoo import models, fields, api

import logging
from random import randint

_logger = logging.getLogger(__name__)


class GitRepository(models.Model):
    _name = 'git.repository'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Git Repository'

    name = fields.Char(required=True)
    path = fields.Char(required=True)
    description = fields.Char()
    repo_id = fields.Integer(string="Repository ID")
    url = fields.Char()
    http_git_url = fields.Char(string="HTTP Url")
    ssh_git_url = fields.Char(string="SSH Url")
    active = fields.Boolean(default=True)
    is_synchronized = fields.Boolean(default=True, tracking=True)

    repository_create_date = fields.Datetime(readonly=True)
    repository_update_date = fields.Datetime(readonly=True, tracking=True)

    partner_id = fields.Many2one(comodel_name='res.partner')
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

    # def _action_sync_branch(self):
    #     _logger.warning(len(self))

    #     for service in list(set(self.mapped('service'))):
    #         method_name = "_action_sync_branch_{}".format(service)
    #         method = getattr(self, method_name) if hasattr(self, method_name) else False

    #         if not method:
    #             _logger.error('Method not found for {}'.format(method_name))
    #             continue

    #         records = self.filtered(lambda x: x.service == service)
    #         _logger.warning('Call {} for {}'.format(method_name, len(records)))
    #         method(records)



        # for service in self.mapped('service'):
        #     _logger.warning(service)
        #     records = self.filtered(lambda x: x.service == service)
        #     method_name = "_action_sync_branch_{}".format(service)
        #     method = getattr(records, method_name) if hasattr(records, method_name) else False
        #     if method:
        #         _logger.warning('Call {} for {}'.format(method_name, len(records)))
        #         # method(records)


    def action_sync_branch(self):
        return self._action_sync_branch(self.ids)

    @api.model
    def _action_sync_branch(self, ids, cron=False):
        repositories = self.browse(ids)
        for service in repositories.mapped('service'):
            records = repositories.filtered(lambda x: x.service == service)
            method_name = "_action_sync_branch_{}".format(service)
            method = getattr(records, method_name) if hasattr(records, method_name) else False
            if method:
                method()


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

