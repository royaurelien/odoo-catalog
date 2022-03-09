# -*- coding: utf-8 -*-

from multiprocessing import synchronize
from odoo import models, fields, api

import logging
from random import randint

_logger = logging.getLogger(__name__)


# class GitRules(models.Model):
#     _name = "git.rules"
#     _description = "Git Rules"
#     _inherits = {'base.automation': 'automation_id'}
#     _check_company_auto = True

#     automation_id = fields.Many2one('base.automation', 'Automated Action', required=True, ondelete='restrict')

class GitRules(models.Model):
    _name = "git.rules"
    _description = "Git Rules"

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    trigger = fields.Selection([])
    is_global = fields.Boolean(compute='_compute_global', store=True)
    model = fields.Selection([('git.organization', 'Organization'),
                               ('git.organization', 'Repository'),
                               ('git.repository', 'Branch'),
                               ('git.branch', 'Custom Addons')], required=True)
    action = fields.Selection([('update', 'Update'),
                               ('ignore', 'Ignore')], required=True)
    condition = fields.Char()
    code = fields.Char()
    organization_ids = fields.Many2many(comodel_name='git.organization')

    tag_ids = fields.Many2many(comodel_name='custom.addon.tags')
    partner_id = fields.Many2one(comodel_name='res.partner')
    user_id = fields.Many2one(comodel_name='res.users')


    @api.depends('organization_ids')
    def _compute_global(self):
        for record in self:
            record.is_global = True if not len(record.organization_ids) else False
