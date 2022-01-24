# -*- coding: utf-8 -*-

from multiprocessing import synchronize
from odoo import models, fields, api

import logging
from random import randint

_logger = logging.getLogger(__name__)

class CustomAddonTags(models.Model):
    _name = "custom.addon.tags"
    _description = "Custom Addon Tags"

    def _get_default_color(self):
        return randint(1, 11)

    name = fields.Char('Name', required=True)
    color = fields.Integer(string='Color', default=_get_default_color)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists!"),
    ]



class CustomAddon(models.Model):
    _name = 'custom.addon'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Custom Addon'

    name = fields.Char(required=True)
    description = fields.Text()
    summary = fields.Char()
    technical_name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    icon = fields.Char('Icon URL')
    # icon_image = fields.Binary(string='Icon', compute='_get_icon_image')
    version = fields.Char()
    author = fields.Char()
    partner_id = fields.Many2one(comodel_name='res.partner', string="Author")
    category_id = fields.Many2one(comodel_name='ir.module.category')

    tag_ids = fields.Many2many('custom.addon.tags', string='Tags')

    branch_ids = fields.Many2many(
        string="Branches",
        comodel_name="git.branch",
        relation="git_branch_custom_addon_rel",
        column1="custom_addon_id",
        column2="branch_id",
    )

    branch_count = fields.Integer(compute='_compute_branch', store=True, string="# Branches")
    repository_count = fields.Integer(compute='_compute_branch', store=True, string="# Repository")
    is_many_used = fields.Boolean(compute='_compute_branch', store=True, string="Many Used")

    @api.depends('branch_ids')
    def _compute_branch(self):
        for record in self:
            record.branch_count = len(record.branch_ids)
            record.repository_count = len(record.branch_ids.mapped('repository_id'))
            record.is_many_used = True if record.repository_count > 1 else False

    def action_view_git_branch(self):
        self.ensure_one()
        action = self.env.ref("custom_addons.action_view_branch").read()[0]
        action["context"] = dict(self.env.context)
        action["context"].pop("group_by", None)
        # action["context"]["search_default_repository_id"] = self.id
        action["domain"] = [('id', 'in', self.branch_ids.ids)]

        return action

    def action_view_git_repository(self):
        self.ensure_one()
        action = self.env.ref("custom_addons.action_view_repository").read()[0]
        action["context"] = dict(self.env.context)
        action["context"].pop("group_by", None)
        action["domain"] = [('id', 'in', self.branch_ids.mapped('repository_id').ids)]

        return action


class GitOrganization(models.Model):
    _name = 'git.organization'
    _inherit = ['mail.thread', 'mail.activity.mixin']
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
    organization_id = fields.Many2one(comodel_name='git.organization',
                                      index=True,
                                      readonly=True,
                                      ondelete="cascade",)
    service = fields.Selection(related='organization_id.service')
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

    def _action_sync_branch(self):
        _logger.warning(len(self))

        for service in list(set(self.mapped('service'))):
            method_name = "_action_sync_branch_{}".format(service)
            method = getattr(self, method_name) if hasattr(self, method_name) else False

            if not method:
                _logger.error('Method not found for {}'.format(method_name))
                continue

            records = self.filtered(lambda x: x.service == service)
            _logger.warning('Call {} for {}'.format(method_name, len(records)))
            method(records)



        # for service in self.mapped('service'):
        #     _logger.warning(service)
        #     records = self.filtered(lambda x: x.service == service)
        #     method_name = "_action_sync_branch_{}".format(service)
        #     method = getattr(records, method_name) if hasattr(records, method_name) else False
        #     if method:
        #         _logger.warning('Call {} for {}'.format(method_name, len(records)))
        #         # method(records)



    def action_sync_branch(self):
        return self._action_sync_branch()


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

class GitBranch(models.Model):
    _name = 'git.branch'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Git Branch'

    name = fields.Char(required=True)
    url = fields.Char()

    last_commit_message = fields.Char()
    last_commit_author = fields.Char()
    last_commit_short_id = fields.Char()
    last_commit_url = fields.Char()

    active = fields.Boolean(default=True)
    major = fields.Boolean(default=False)
    requirements = fields.Boolean(default=False)
    odoo_version = fields.Char()

    repository_id = fields.Many2one(comodel_name='git.repository')
    partner_id = fields.Many2one(related='repository_id.partner_id')
    path = fields.Char(related='repository_id.path', store=True)

    tag_ids = fields.Many2many('custom.addon.tags', string='Tags')

    custom_addon_ids = fields.Many2many(
        string="Custom Addons",
        comodel_name="custom.addon",
        relation="git_branch_custom_addon_rel",
        column1="branch_id",
        column2="custom_addon_id",
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