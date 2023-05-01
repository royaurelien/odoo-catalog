import logging
import re

from odoo import models

REGEX_MAJOR_VERSION = re.compile("^(0|[1-9]\d*)\.(0|[1-9]\d*)$")

_logger = logging.getLogger(__name__)


class GitRepository(models.Model):
    _inherit = "git.repository"

    def _create_branch_from_gitlab(self, vals, **kwargs):
        self.ensure_one()

        gitlab = self.organization_id._get_gitlab()
        project = gitlab.projects.get(self.repo_id, lazy=True)
        version, _ = gitlab.version()
        major_version = int(version.split(".")[0])
        force_create = kwargs.get("force_create", False)

        vals_list = []

        if force_create and major_version < 14:
            branch = project.branches.create(
                {
                    "branch": vals["ref"],
                    "ref": "master",
                }
            )
            if branch:
                vals_list.append(self._convert_gitlab_to_odoo(branch))

                project.default_branch = branch.name
                project.save()

        branch = project.branches.create(vals)

        if branch:
            vals_list.append(self._convert_gitlab_to_odoo(branch))

        if vals_list:
            self.write({"branch_ids": [(0, False, vals) for vals in vals_list]})

        return True

    def _get_commits_from_gitlab(self, **kwargs):
        """
        {
            'project_id': '137',
            'id': '0ddeb21adbbfac223556d412xxxxxxxxxxxxxxxxx',
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
            'web_url': 'http://gitlab.xxxx.xxxx/dev/xxx_xxxxx/-/commit/0ddeb21adbbfac223556d412xxxxxxxxxxxxxxxxx',
            'stats': {'additions': 1, 'deletions': 0, 'total': 1}
        }
        """
        self.ensure_one()

        gitlab = self.organization_id._get_gitlab()
        project = gitlab.projects.get(self.repo_id, lazy=True)
        max_count = 100
        commits = project.commits.list(page=1, per_page=max_count, with_stats=True)

        vals_list = []
        _gitlab_date_to_datetime = self.organization_id._gitlab_date_to_datetime

        for commit in commits:
            # _logger.error(commit.attributes)

            vals_list.append(
                {
                    "commit_date": _gitlab_date_to_datetime(commit.committed_date),
                    "name": commit.title,
                    "author": commit.author_name,
                    "email": commit.author_email,
                    "commit_id": commit.short_id,
                    "commit_url": commit.web_url,
                    "stats": "+{o[additions]}/-{o[deletions]}/{o[total]}".format(
                        o=commit.stats
                    ),
                }
            )

        return vals_list

    def _get_items_from_gitlab(self):
        gitlab = self.organization_id._get_gitlab()
        project = gitlab.projects.get(self.repo_id, lazy=True)
        # `get_all=True` or `iterator=True`
        # commits = project.commits.list(get_all=True, all=True)
        # _logger.warning(commits)
        branches = project.branches.list(all=True, get_all=True)

        return [branch for branch in branches]

    def _get_item_from_gitlab(self, **kwargs):
        gl = self.organization_id._get_gitlab()
        project = gl.projects.get(self.repo_id)

        return project

    def _convert_gitlab_to_odoo(self, item, **kwargs):
        vals = {
            "repository_id": self.id,
            "name": item.name,
            "url": item.web_url,
        }

        if item.commit:
            _gitlab_date_to_datetime = self.organization_id._gitlab_date_to_datetime

            vals.update(
                {
                    "last_commit_date": _gitlab_date_to_datetime(
                        item.commit.get("committed_date")
                    ),
                    "last_commit_message": item.commit.get("title"),
                    "last_commit_author": item.commit.get("author_email"),
                    "last_commit_short_id": item.commit.get("short_id"),
                    "last_commit_url": item.commit.get("web_url"),
                }
            )

        return vals
