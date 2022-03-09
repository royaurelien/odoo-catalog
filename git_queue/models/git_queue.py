# -*- coding: utf-8 -*-

import datetime
import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class GitQueue(models.Model):
    _name = 'git.queue'
    _inherit = 'queue.job'
    _description = 'Git Job'

    method = fields.Selection([
        ('action_sync', 'Git Synchronization'),
        ('bar', 'Method doing bar')
    ])

    res_model = fields.Char()
    res_ids = fields.Char()
    model_id = fields.Many2one(comodel_name='ir.model', compute='_compute_model')
    count = fields.Integer(compute='_compute_model')

    @api.depends('res_ids', 'res_model')
    def _compute_model(self):
        for record in self:
            record.count = len(self._string_to_ids(record.res_ids)) if record.res_ids else 0
            record.model_id = self.env['ir.model'].search([('model', '=', record.res_model)],limit=1)


    def _ids_to_string(self, ids):
        return ",".join([str(id) for id in ids])

    def _string_to_ids(self, string):
        return [int(id) for id in string.split(",")]

    def add(self, method, model, ids):
        vals = {
            'method': method,
            'res_model': model,
            'res_ids': self._ids_to_string(ids)
        }
        return self.create(vals)

    def action_sync(self):
        ids = self._string_to_ids(self.res_ids)
        model_env = self.env[self.res_model]
        # records = model_env.browse(ids)

        res = model_env._action_sync(ids)
        return (res, 'OK')


    def bar(self):
        """Execute the job `bar`.
        This could be a button method, a cron method, etc.
        """
        _logger.warning("<< BAR >>")



    def execute_cron(self):
        records = self.search([('state', '=', 'pending')], limit=5)
        for record in records:
            record.execute_call()