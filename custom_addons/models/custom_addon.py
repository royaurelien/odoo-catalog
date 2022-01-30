# -*- coding: utf-8 -*-

from multiprocessing import synchronize
from odoo import models, fields, api

import logging
import os
from random import randint

_logger = logging.getLogger(__name__)


class CustomAddon(models.Model):
    _name = 'custom.addon'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Custom Addon'

    name = fields.Char(required=True)
    description = fields.Text()
    web_description = fields.Html()
    summary = fields.Char()
    technical_name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    icon = fields.Char('Icon URL')
    # icon_image = fields.Binary(string='Icon', compute='_get_icon_image')
    url = fields.Char()
    version = fields.Char()
    author = fields.Char()
    partner_id = fields.Many2one(comodel_name='res.partner')
    user_id = fields.Many2one(comodel_name='res.users')
    category_id = fields.Many2one(comodel_name='ir.module.category')
    last_sync_date = fields.Datetime(string="Last Sync Date", readonly=True)

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
    color = fields.Integer(compute="_compute_branch", string="Color Index")

    def _compute_is_favorite(self):
        for record in self:
            record.is_favorite = self.env.user in record.favorite_user_ids

    def _inverse_is_favorite(self):
        favorite_addons = not_fav_addons = self.env['custom.addon'].sudo()
        for record in self:
            if self.env.user in record.favorite_user_ids:
                favorite_addons |= record
            else:
                not_fav_addons |= record

        not_fav_addons.write({'favorite_user_ids': [(4, self.env.uid)]})
        favorite_addons.write({'favorite_user_ids': [(3, self.env.uid)]})

    def _get_default_favorite_user_ids(self):
        # return [(6, 0, [self.env.uid])]
        return []

    favorite_user_ids = fields.Many2many(
        'res.users', 'custom_addons_favorite_user_rel',
        default=_get_default_favorite_user_ids,
        string='Members')
    is_favorite = fields.Boolean(compute='_compute_is_favorite', inverse='_inverse_is_favorite', string='Show Project on dashboard')

    # @api.depends('branch_ids')
    # def _compute_url(self):
    #     for record in self:
    #         record.url = os.path.join(record.branch_ids[0].url, record.technical_name) if record.branch_ids else ""

    @api.depends('branch_ids')
    def _compute_branch(self):
        for record in self:
            record.branch_count = len(record.branch_ids)
            record.repository_count = len(record.branch_ids.mapped('repository_id'))
            record.is_many_used = True if record.repository_count > 1 else False
            record.color = 1 if record.is_many_used else 0

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

    def action_open_url(self):
        self.ensure_one()

        _logger.warning(dict(self.env.context))
        res_id = self.env.context.get('branch_id')
        url = None
        if res_id:
            # res_id = self.env.context.get('id')
            # res_model = self.env.context.get('model')
            res_model = 'git.branch'
            res = self.env[res_model].browse(res_id)
            url = os.path.join(res.url, self.technical_name)

        action = {
            "type": "ir.actions.act_url",
            "url": url,
            "target": "new",
        }

        return action