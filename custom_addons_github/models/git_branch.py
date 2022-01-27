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

class GitBranch(models.Model):
    _inherit = 'git.branch'


    def _get_github(self):
        self.ensure_one()
        return Github(self.organization_id.token)

    def _get_items_from_github(self):
        self.ensure_one()
        g = self._get_github()
        org = g.get_organization(self.organization_id.name)
        repo = org.get_repo(self.path)
        branch = repo.get_branch(self.name)

        modules = dict()

        for branch in repo.get_branches():
            ref = branch.name
            modules[ref] = 0
            contents = repo.get_contents("", ref=ref)

            while contents:
                file_content = contents.pop(0)
                if file_content.name.startswith('.'):
                    continue

                if file_content.type == "dir":
                    try:
                        manifest = repo.get_contents(os.path.join(file_content.path, "__manifest__.py"))
                        manifest = eval(manifest.decoded_content)
                        modules[ref] += 1
                    except:
                        manifest = False
                    finally:
                        pass

                elif file_content.name == "requirements.txt":

                    pass


        return branch

    def _convert_github_to_odoo(self, item):
        self.ensure_one()
        vals = {
            'repository_id': self.id,
            'name': item.name,
        }
        return vals



