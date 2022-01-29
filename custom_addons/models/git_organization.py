# -*- coding: utf-8 -*-

from multiprocessing import synchronize
from odoo import models, fields, api

import logging
from random import randint

_logger = logging.getLogger(__name__)


class GitOrganization(models.Model):
    _name = 'git.organization'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'abstract.git.model']
    _description = 'Git Organization'

    ### GIT ###
    _git_service = "service"
    _git_field_rel = 'repository_ids'
    _git_field_name = 'repo_id'
    _git_type_rel = "o2m"

    url = fields.Char()
    login = fields.Char()
    password = fields.Char()
    token = fields.Char()
    service = fields.Selection([])
    auth_method = fields.Selection([('public', 'Public'),
                             ('basic', 'Basic'),
                             ('token', 'Token')],
                            default='public', required=True)
    exclude_names = fields.Char()

    repository_ids = fields.One2many(comodel_name='git.repository', inverse_name='organization_id')
    repository_count = fields.Integer(compute='_compute_repository', store=False)
    force_update = fields.Boolean(default=False)

    @api.depends('repository_ids')
    def _compute_repository(self):
        for record in self:
            record.repository_count = len(record.repository_ids)


    def action_view_git_repository(self):
        self.ensure_one()
        action = self.env.ref("custom_addons.action_view_repository").read()[0]
        action["context"] = dict(self.env.context)
        action["context"].pop("group_by", None)
        # action["context"]["search_default_repository_id"] = self.id
        action["domain"] = [('organization_id', '=', self.id)]

        return action