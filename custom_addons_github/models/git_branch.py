# -*- coding: utf-8 -*-

from multiprocessing import synchronize
from odoo import models, fields, api
from odoo.tools import datetime

from datetime import datetime
from github import Github, GithubException
import logging
import re
import os

MANIFEST_NAMES = ['__manifest__.py', '__openerp__.py']
REGEX_MAJOR_VERSION = re.compile("^(0|[1-9]\d*)\.(0|[1-9]\d*)$")
# TYPE = [('github', 'Github')]

_logger = logging.getLogger(__name__)

class GitBranch(models.Model):
    _inherit = 'git.branch'


    # def _get_github(self):
    #     self.ensure_one()
    #     return Github(self.organization_id.token)

    def _get_items_from_github(self):
        self.ensure_one()
        org = self.organization_id._get_github()
        # org = g.get_organization(self.organization_id.name)
        repo = org.get_repo(self.path)
        branch = repo.get_branch(self.name)

        requirements = False
        python_modules = ""
        addons = []
        ref = branch.name
        path = self.repository_id.subfolder or ""

        try:
            contents = repo.get_contents(path, ref=ref)
        except GithubException as message:
            _logger.error(message)
            return []

        while contents:
            file_content = contents.pop(0)
            if file_content.name.startswith('.'):
                continue

            if file_content.type == "dir":
                _logger.warning(file_content.name)
                for filename in MANIFEST_NAMES:
                    try:
                        manifest = repo.get_contents(os.path.join(file_content.path, filename), ref=ref)
                        manifest = eval(manifest.decoded_content)
                        manifest['technical_name'] = file_content.path

                        try:
                            web_description = repo.get_contents(os.path.join(file_content.path, 'static/description/index.html'), ref=ref)
                            manifest['web_description'] = web_description.decoded_content if web_description else False
                        except:
                            pass

                        addons.append(manifest)

                        break
                    except:
                        continue

            elif file_content.name == "requirements.txt":
                try:
                    f = repo.get_contents(os.path.join(file_content.path, "requirements.txt"))
                    # _logger.warning(f)
                    python_modules = f.decode().splitlines()
                    python_modules = ", ".join([e.decode() for e in python_modules]) if python_modules else ""
                    requirements = True
                except GithubException as message:
                    _logger.error(message)
                    continue


        vals = {
            'requirements': requirements,
            'python_modules': python_modules,
        }
        self.update(vals)

        # _logger.warning(addons)

        return addons

    def _convert_github_to_odoo(self, item):
        self.ensure_one()
        vals = {
            # 'branch_ids': [(4, self.id)],
            'name': item.get('name'),
            'technical_name': item.get('technical_name'),
            'version': item.get('version'),
            'author': item.get('author'),
            'description': item.get('description'),
            'web_description': item.get('web_description'),
            'summary': item.get('summary'),
            'category': item.get('category'),
        }

        # category = item.get('category')
        # if category:
        #     category_id = self.env['ir.module.category'].search([('name', 'ilike', category)], limit=1)
        #     if category_id:
        #         vals.update({'category_id': category_id.id})

        return vals


