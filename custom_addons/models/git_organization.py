# -*- coding: utf-8 -*-

from multiprocessing import synchronize
from odoo import models, fields, api

import logging
from random import randint

_logger = logging.getLogger(__name__)


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

    def action_sync_repository(self):
        return self._action_sync_repository(self.ids)

    @api.model
    def _action_sync_repository(self, ids, cron=False):
        organizations = self.browse(ids)
        for service in organizations.mapped('service'):
            records = organizations.filtered(lambda x: x.service == service)
            method_name = "_action_sync_repository_{}".format(service)
            method = getattr(records, method_name) if hasattr(records, method_name) else False
            if method:
                method()

