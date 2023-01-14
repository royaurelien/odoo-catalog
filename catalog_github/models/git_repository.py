# -*- coding: utf-8 -*-

import logging
import re
import os

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class GitRepository(models.Model):
    _inherit = 'git.repository'


    def _get_commits_from_github(self):
        self.ensure_one()
        org = self.organization_id._get_github()
        repo = org.get_repo(self.path)
        # total = repo.get_commits().totalCount
        # commits = repo.get_commits()
        vals_list = []
        max_count = 100

        for item in repo.get_commits()[:max_count]:
            commit = item.commit
            committer = commit.committer

            vals_list.append({
                'name': commit.message,
                'author': committer.name,
                'email': committer.email,
                'commit_id': item.sha,
                'commit_url': item.html_url,
                'commit_date': committer.date,
            })

            # _logger.warning(committer.date)
        return vals_list


    def _get_items_from_github(self):
        self.ensure_one()
        org = self.organization_id._get_github()

        repo = org.get_repo(self.path)
        branches = repo.get_branches()

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



