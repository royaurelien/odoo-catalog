# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

import logging


_logger = logging.getLogger(__name__)



class GitContributor(models.Model):
    _name = 'git.contributor'
    _description = 'Git Contributor'

    name = fields.Char()
    email = fields.Char()
    repository_id = fields.Many2one('git.repository')