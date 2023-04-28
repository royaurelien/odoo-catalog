from odoo import models


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
