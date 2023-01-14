# -*- coding: utf-8 -*-

from multiprocessing import synchronize
from odoo import models, fields, api, _

from datetime import datetime
import logging
from random import randint

_logger = logging.getLogger(__name__)


class GitCommitItems(models.TransientModel):
    _name = 'git.commit.items'
    _description = 'Git Commit Items'

    _transient_max_hours = 1

    branch_id = fields.Many2one('git.branch')
    repository_id = fields.Many2one('git.repository')

    name = fields.Char()
    author = fields.Char()
    email = fields.Char()
    stats = fields.Char()
    commit_id = fields.Char()
    commit_url = fields.Char()
    commit_date = fields.Datetime()


    def action_open_url(self):
        self.ensure_one()

        if not self.commit_url:
            return False

        action = {
            "type": "ir.actions.act_url",
            "url": self.commit_url,
            "target": "new",
        }

        return action