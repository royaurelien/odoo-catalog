# -*- coding: utf-8 -*-

from multiprocessing import synchronize
from odoo import models, fields, api


class CustomAddon(models.Model):
    _name = 'custom.addon'
    _description = 'Custom Addon'

    name = fields.Char(required=True)
    technical_name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    version = fields.Char()

    branch_ids = fields.Many2many(
        string="Branches",
        comodel_name="git.branch",
        relation="git_branch_custom_addon_rel",
        column1="custom_addon_id",
        column2="branch_id",
    )

    # repository_ids = fields.One2many(compute='_compute_repository', store=True, readonly=True)
    # repository_ids = fields.One2many(related='branch_ids.repository_id')

    # @api.depends('branch_ids')
    # def _compute_repository(self):
    #     for record in self:
    #         record.repository_ids = record.branch_ids.mapped('repository_id')

class GitOrganization(models.Model):
    _name = 'git.organization'
    _description = 'Git Organization'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    url = fields.Char()
    login = fields.Char()
    password = fields.Char()
    token = fields.Char()
    service = fields.Selection([])
    auth_method = fields.Selection([('public', 'Public'),
                             ('basic', 'Basic'),
                             ('token', 'Token')],
                            default='public', required=True)
    is_synchronized = fields.Boolean(default=False)
    exclude_names = fields.Char()

    repository_ids = fields.One2many(comodel_name='git.repository', inverse_name='organization_id')
    repository_count = fields.Integer(compute='_compute_repository', store=False)

    @api.depends('repository_ids')
    def _compute_repository(self):
        for record in self:
            record.repository_count = len(record.repository_ids)

    def _action_sync_repository(self):
        pass

    def action_sync_repository(self):
        return self._action_sync_repository()



class GitRepository(models.Model):
    _name = 'git.repository'
    _description = 'Git Repository'

    name = fields.Char(required=True)
    path = fields.Char(required=True)
    description = fields.Char()
    repo_id = fields.Integer()
    url = fields.Char()
    http_git_url = fields.Char()
    ssh_git_url = fields.Char()
    active = fields.Boolean(default=True)

    repository_create_date = fields.Datetime()
    repository_update_date = fields.Datetime()

    organization_id = fields.Many2one(comodel_name='git.organization')
    branch_ids = fields.One2many(comodel_name='git.branch', inverse_name='repository_id')

    branch_count = fields.Integer(compute='_compute_branch', store=True)
    branch_major_count = fields.Integer(compute='_compute_branch', store=True)

    @api.depends('branch_ids')
    def _compute_branch(self):
        for record in self:
            record.branch_count = len(record.branch_ids)
            record.branch_major_count = len(record.branch_ids.filtered(lambda x: x.major))

class GitBranch(models.Model):
    _name = 'git.branch'
    _description = 'Git Branch'

    name = fields.Char(required=True)
    url = fields.Char()

    last_commit_message = fields.Char()
    last_commit_author = fields.Char()
    last_commit_short_id = fields.Char()
    last_commit_url = fields.Char()

    active = fields.Boolean(default=True)
    major = fields.Boolean(default=False)
    odoo_version = fields.Char()

    repository_id = fields.Many2one(comodel_name='git.repository')
    path = fields.Char(related='repository_id.path', store=True)

    custom_addon_ids = fields.Many2many(
        string="Custom Addons",
        comodel_name="custom.addon",
        relation="git_branch_custom_addon_rel",
        column1="branch_id",
        column2="custom_addon_id",
    )

    def name_get(self):
        return [(record.id, "{o.path} / {o.name}".format(o=record)) for record in self]

