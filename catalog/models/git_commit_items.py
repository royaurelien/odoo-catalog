# -*- coding: utf-8 -*-

from multiprocessing import synchronize
from odoo import models, fields, api, _

from datetime import datetime
import logging
from random import randint

_logger = logging.getLogger(__name__)

RECENT_ACTIVITY_DAYS = 30
COMMIT_MESSAGE = "{o[last_commit_message]}, {o[last_commit_author]} ({o[last_commit_short_id]})"
COMMIT_VARS = ['last_commit_message', 'last_commit_author', 'last_commit_short_id', 'last_commit_url', 'last_commit_date']

MESSAGES = {
    'new_branch': "Found {} from {} repository."
}


# class GitCommitItem(models.TransientModel):
#     _name = 'git.commit.item'
#     _description = 'Git Commit Item'
#     # _order = "last_sync_date desc, name desc"

#     parent_id = fields.Many2one('git.commit.items')



class GitCommitItems(models.TransientModel):
    _name = 'git.commit.items'
    _description = 'Git Commit Items'
    # _order = "last_sync_date desc, name desc"

    branch_id = fields.Many2one('git.branch')
    repository_id = fields.Many2one('git.repository')
    # commit_ids = fields.One2many(comodel_name='git.commit.item', inverse_name='parent_id')
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