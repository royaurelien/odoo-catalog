# -*- coding: utf-8 -*-

from multiprocessing import synchronize
from odoo import models, fields, api
from odoo.tools import datetime

from datetime import datetime
from github import Github
import logging
import re
import os

REGEX_MAJOR_VERSION = re.compile("^(0|[1-9]\d*)\.(0|[1-9]\d*)$")

_logger = logging.getLogger(__name__)

class GitRepository(models.Model):
    _inherit = 'git.repository'


    def _get_items_from_gitlab(self):
        gl = self.organization_id._get_gitlab()
        project = gl.projects.get(self.repo_id)
        branches = project.branches.list()

        return [branch for branch in branches]

    def _convert_gitlab_to_odoo(self, item):
        vals = {
            'repository_id': self.id,
            'name': item.name,
            'url': item.web_url,
        }

        if item.commit:
            _gitlab_date_to_datetime = self.organization_id._gitlab_date_to_datetime

            vals.update({
                'last_commit_date': _gitlab_date_to_datetime(item.commit.get('committed_date')),
                'last_commit_message': item.commit.get('title'),
                'last_commit_author': item.commit.get('author_email'),
                'last_commit_short_id': item.commit.get('short_id'),
                'last_commit_url': item.commit.get('web_url'),
            })

        # _logger.debug(vals)
        return vals



