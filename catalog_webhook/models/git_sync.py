from odoo import models


class GitSync(models.AbstractModel):
    _inherit = "git.sync"

    def _convert_webhook_to_odoo(self, data, **kwargs):
        return self.__get_method(
            "_convert_{}_webhook_to_odoo", self.service, {}, data, **kwargs
        )
