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
TYPE = [('github', 'Github')]

_logger = logging.getLogger(__name__)

class GitRepository(models.Model):
    _inherit = 'git.repository'


    # def _get_github(self):
    #     self.ensure_one()
    #     return Github(self.organization_id.token)

    def _get_items_from_github(self):
        self.ensure_one()
        org = self.organization_id._get_github()
        # org = g.get_organization(self.organization_id.name)

        repo = org.get_repo(self.path)
        # _logger.warning(repo)

        branches = repo.get_branches()
        # _logger.warning(branches)

        return branches

    def _convert_github_to_odoo(self, item):
        vals = {
            'repository_id': self.id,
            'name': item.name,
        }

        if item.commit:
            commit = item.commit.commit
            vals.update({
                'last_commit_date': commit.author.date,
                'last_commit_message': commit.message,
                'last_commit_author': commit.author.email,
                'last_commit_short_id': commit.sha,
                'last_commit_url': commit.html_url,
            })

        if self.url:
           url = os.path.join(self.url, 'tree', item.name)
           vals['url'] = url

        return vals



