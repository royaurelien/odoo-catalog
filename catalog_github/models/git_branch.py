import logging
import os

from github import GithubException

from odoo import models

from ..utils import prepare_commit

MANIFEST_NAMES = ["__manifest__.py", "__openerp__.py"]


_logger = logging.getLogger(__name__)


class GitBranch(models.Model):
    _inherit = "git.branch"

    def _get_commits_from_github(self, **kwargs):
        self.ensure_one()
        org = self.organization_id._get_github()
        repo = org.get_repo(self.path)
        max_count = 100
        # commits = repo.get_commits(self.name)
        vals_list = []

        for item in repo.get_commits(self.name)[:max_count]:
            vals_list.append(prepare_commit(item))

        return vals_list

    def _get_items_from_github(self):
        self.ensure_one()
        org = self.organization_id._get_github()
        repo = org.get_repo(self.path)
        branch = repo.get_branch(self.name)
        icon_search = self._get_icon_search()
        test, limit = self._get_test_mode()
        # test = True
        count = 0

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
            if file_content.name.startswith("."):
                continue

            if file_content.type == "dir":
                # _logger.warning(file_content.name)
                for filename in MANIFEST_NAMES:
                    try:
                        manifest = repo.get_contents(
                            os.path.join(file_content.path, filename), ref=ref
                        )
                        manifest = eval(manifest.decoded_content)
                        # ast.literal_eval(manifest_data)
                        manifest["technical_name"] = file_content.path.split("/")[-1]

                        try:
                            web_description = repo.get_contents(
                                os.path.join(
                                    file_content.path, "static/description/index.html"
                                ),
                                ref=ref,
                            )
                            manifest["web_description"] = (
                                web_description.decoded_content
                                if web_description
                                else False
                            )
                        except:
                            pass

                        if icon_search:
                            try:
                                icon = repo.get_contents(
                                    os.path.join(
                                        file_content.path, "static/description/icon.png"
                                    ),
                                    ref=ref,
                                )
                                manifest["icon_image"] = icon.content
                            except:
                                pass

                        addons.append(manifest)
                        break
                    except:
                        continue
                count += 1

            if test and count >= limit:
                break

            if file_content.name == "requirements.txt":
                try:
                    content = repo.get_contents(
                        os.path.join(file_content.path, "requirements.txt")
                    )
                    python_modules = content.decode().splitlines()
                    python_modules = (
                        ", ".join([e.decode() for e in python_modules])
                        if python_modules
                        else ""
                    )
                    requirements = True
                except GithubException as message:
                    _logger.error(message)
                    continue

        vals = {
            "requirements": requirements,
            "python_modules": python_modules,
        }
        self.update(vals)

        return addons

    def _convert_github_to_odoo(self, item, **kwargs):
        self.ensure_one()

        mapping, keys = self._get_manifest_mapping()
        vals = {k: item.get(v, False) for k, v in mapping.items()}

        return vals
