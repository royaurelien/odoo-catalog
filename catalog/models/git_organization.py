# -*- coding: utf-8 -*-


import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class GitOrganization(models.Model):
    _name = 'git.organization'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'git.sync', 'git.mixin']
    _description = 'Git Organization'

    ### GIT ###
    _git_service = "service"
    _git_field_rel = 'repository_ids'
    _git_field_name = 'repo_id'
    _git_type_rel = "o2m"

    auth_id = fields.Many2one(comodel_name='custom.auth')
    auth_method = fields.Selection([('public', 'Public'),
                             ('private', 'Private')],
                            default='public', required=True)

    # login = fields.Char()
    # password = fields.Char()
    # token = fields.Char()
    service = fields.Selection([])
    sync_identifier = fields.Char(compute='_compute_identifier', store=True)

    exclude_names = fields.Char(copy=False, string="Exclude")
    is_user = fields.Boolean(default=False)
    repository_ids = fields.One2many(comodel_name='git.repository', inverse_name='organization_id')
    repository_count = fields.Integer(compute='_compute_repository', compute_sudo=True, store=False)
    branch_count = fields.Integer(compute='_compute_repository', compute_sudo=True, store=False)
    custom_addons_count = fields.Integer(compute='_compute_repository', compute_sudo=True, store=False)
    force_update = fields.Boolean(default=False)
    enable_debug = fields.Boolean(default=False, string="Debug mode")
    icon = fields.Char(compute='_compute_icon', string="Module Icon")


    @api.depends('service')
    def _compute_icon(self):
        for record in self:
            record.icon = f"/catalog_{record.service}/static/src/img/logo.png"


    @api.depends('service', 'auth_method', 'auth_id')
    def _compute_identifier(self):
        for record in self:
            items = [record.service, record.auth_method]
            if record.auth_id:
                items.append(str(record.auth_id.id))
            record.sync_identifier = "-".join(items)


    @api.depends('repository_ids')
    def _compute_repository(self):
        for record in self:
            record.repository_count = len(record.repository_ids)
            record.branch_count = len(record.repository_ids.branch_ids)

            addons = len(record.repository_ids.mapped('branch_ids.custom_addon_ids'))

            # repository_ids = self.env['custom.addon'].search([]).mapped('branch_ids.repository_id')
            # addons = len(repository_ids.filtered(lambda rec: rec.id in record.repository_ids.ids))
            record.custom_addons_count = addons


    @api.onchange('auth_method')
    def _onchange_auth_method(self):
        if not self.auth_method or self.auth_method == 'public':
            self.auth_id = False


    def _action_view_git_repository(self, action):
        action["domain"] = [('organization_id', '=', self.id)]

        return action

    def _action_view_git_branch(self, action):
        action["domain"] = [('organization_id', '=', self.id)]

        return action

    def _action_view_custom_addons(self, action):
        addons = self.repository_ids.mapped('branch_ids.custom_addon_ids')
        action["domain"] = [('id', 'in', addons.ids)]

        return action
