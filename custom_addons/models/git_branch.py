# -*- coding: utf-8 -*-

from multiprocessing import synchronize
from odoo import models, fields, api

from datetime import datetime
import logging
from random import randint

_logger = logging.getLogger(__name__)

RECENT_ACTIVITY_DAYS = 30
COMMIT_MESSAGE = "{o[last_commit_message]}, {o[last_commit_author]} ({o[last_commit_short_id]})"
COMMIT_VARS = ['last_commit_message', 'last_commit_author', 'last_commit_short_id', 'last_commit_url', 'last_commit_date']

MESSAGES = {
    'new_branch': "New branch {}."
}

class GitBranch(models.Model):
    _name = 'git.branch'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'abstract.git.model']
    _description = 'Git Branch'
    _order = "last_sync_date desc, name desc"

    ### GIT ###
    _git_service = "service"
    _git_field_rel = 'custom_addon_ids'
    _git_field_name = 'technical_name'
    _git_type_rel = "m2m"

    last_commit_message = fields.Char()
    last_commit_author = fields.Char()
    last_commit_short_id = fields.Char()
    last_commit_url = fields.Char()
    last_commit_date = fields.Datetime()
    last_commit = fields.Char(compute='_compute_commit', store=True)
    is_recent_activity = fields.Boolean(compute='_compute_commit', string="Recent Activity", store=True)

    @api.depends('last_commit_message', 'last_commit_author', 'last_commit_date', 'last_sync_date')
    def _compute_commit(self):
        now = datetime.now()
        for record in self:
            vals = record.read(COMMIT_VARS)[0]
            record.last_commit = COMMIT_MESSAGE.format(o=vals)
            record.is_recent_activity = False

            if record.last_sync_date and record.last_commit_date:
                if (now - record.last_commit_date).days <= RECENT_ACTIVITY_DAYS:
                    record.is_recent_activity = True

    major = fields.Boolean(default=False)
    requirements = fields.Boolean(default=False)
    python_modules = fields.Char()
    odoo_version = fields.Char()

    repository_id = fields.Many2one(comodel_name='git.repository')
    organization_id = fields.Many2one(related='repository_id.organization_id', store=True)
    service = fields.Selection(related='repository_id.organization_id.service', store=True)
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
    def _compute_custom_addon(self, context=None):
        _logger.error(context)
        for record in self:
            record.custom_addon_count = len(record.custom_addon_ids)


    def action_view_custom_addon(self):
        self.ensure_one()
        action = self.env.ref("custom_addons.action_view_addons").read()[0]
        action["context"] = dict(self.env.context)
        action["context"].pop("group_by", None)
        action["domain"] = [('id', 'in', self.custom_addon_ids.ids)]

        return action


    def action_sync(self):
        super(GitBranch, self).action_sync(force_update=True)
        # super(GitBranch, self)._action_sync(ids)

    # @api.model
    # def create(self, vals):
    #     res = super(GitBranch, self).create(vals)

    #     message = {
    #         'body': "New branch {} !".format(res.name),
    #         'message_type': 'notification',
    #     }
    #     message_id = res.repository_id.message_post(**message)
    #     return res

    @api.model_create_multi
    def create(self, vals_list):
        res_ids = super(GitBranch, self).create(vals_list)
        for parent_id in res_ids.mapped('repository_id'):
            names = res_ids.filtered(lambda rec: rec.repository_id.id == parent_id.id).mapped('name')
            names = ", ".join(names)

            message = {
                'body': MESSAGES['new_branch'].format(names),
                'message_type': 'notification',
            }
            message_id = parent_id.message_post(**message)

        return res_ids


    # def _track_subtype(self, init_values):
    # # init_values contains the modified fields' values before the changes
    # #
    # # the applied values can be accessed on the record as they are already
    # # in cache
    # self.ensure_one()
    # if 'state' in init_values and self.state == 'confirmed':
    #     return self.env.ref('my_module.mt_state_change')
    # return super(BusinessTrip, self)._track_subtype(init_values)