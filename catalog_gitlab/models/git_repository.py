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


    def _get_commits_from_gitlab(self):
        """
            {
                'project_id': '137',
                'id': '0ddeb21adbbfac223556d4121ee1f06a120d1474',
                'short_id': '0ddeb21a',
                'created_at': '2021-10-07T10:55:49.000+02:00',
                'parent_ids': [],
                'title': 'Initial commit',
                'message': 'Initial commit',
                'author_name': 'XXXX',
                'author_email': '00000001+XXXX@users.noreply.github.com',
                'authored_date': '2021-10-07T10:55:49.000+02:00',
                'committer_name': 'GitHub',
                'committer_email': 'noreply@github.com',
                'committed_date': '2021-10-07T10:55:49.000+02:00',
                'web_url': 'http://gitlab.xxxx.xxxx/dev/xxx_xxxxx/-/commit/0ddeb21adbbfac223556d4121ee1f06a120d1474',
                'stats': {'additions': 1, 'deletions': 0, 'total': 1}}
        """
        self.ensure_one()

        gl = self.organization_id._get_gitlab()
        project = gl.projects.get(self.repo_id, lazy=True)
        max_count = 100
        commits = project.commits.list(page=1, per_page=max_count, with_stats=True)

        vals_list = []
        _gitlab_date_to_datetime = self.organization_id._gitlab_date_to_datetime

        for commit in commits:
            _logger.error(commit.attributes)

            vals_list.append({
                'commit_date': _gitlab_date_to_datetime(commit.committed_date),
                'name': commit.title,
                'author': commit.author_name,
                'email': commit.author_email,
                'commit_id': commit.short_id,
                'commit_url': commit.web_url,
                'stats': "+{o[additions]}/-{o[deletions]}/{o[total]}".format(o=commit.stats),
            })

        return vals_list


    def _get_items_from_gitlab(self):
        gl = self.organization_id._get_gitlab()
        project = gl.projects.get(self.repo_id)
        # `get_all=True` or `iterator=True`
        # commits = project.commits.list(get_all=True, all=True)
        # _logger.warning(commits)
        branches = project.branches.list(get_all=True)

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

        return vals



