# -*- coding: utf-8 -*-


import logging

from odoo import models

_logger = logging.getLogger(__name__)


class GitSync(models.AbstractModel):
    _inherit = "git.sync"

    def _create_repository_from_odoo(self, data, **kwargs):
        return self.__get_method(
            "_create_repository_from_{}", self.service, {}, data, **kwargs
        )

    def _create_branch_from_odoo(self, data, **kwargs):
        return self.__get_method(
            "_create_branch_from_{}", self.service, {}, data, **kwargs
        )
