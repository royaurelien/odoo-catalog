# -*- coding: utf-8 -*-

import logging

from odoo import models

_logger = logging.getLogger(__name__)

MESSAGE_SYNC = "Synchronization completed : {}"


class QueueJobBatch(models.Model):
    _inherit = "queue.job.batch"

    def custom_check_state(self):
        """
        Custom checker to notify user after jobs done
        """
        self.ensure_one()
        res = super().check_state()

        if all(job.state == "done" for job in self.job_ids):
            self.user_id.notify_success(MESSAGE_SYNC.format(self.name))

        return res
