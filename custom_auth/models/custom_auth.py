# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CustomAuth(models.Model):
    _name = 'custom.auth'
    _description = 'Custom Auth'

    name = fields.Char()
    auth_method = fields.Selection([('public', 'Public'),
                             ('basic', 'Basic'),
                             ('token', 'Token')],
                            default='public', required=True)
    login = fields.Char()
    password = fields.Char()
    token = fields.Char()

    parent_id = fields.Many2one('custom.auth', 'Child Categories')
    child_ids = fields.One2many('custom.auth', 'parent_id', 'Fallback')


