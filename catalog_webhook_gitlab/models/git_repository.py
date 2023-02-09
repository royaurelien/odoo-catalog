# -*- coding: utf-8 -*-

from multiprocessing import synchronize
import logging
from uuid import uuid4
from functools import reduce

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


def deep_get(dictionary, keys, default=None, func=None):
    value = reduce(
        lambda d, key: d.get(key, default) if isinstance(d, dict) else default,
        keys.split("."),
        dictionary,
    )
    if value and func:
        try:
            value = func(value)
        except:
            pass
    return value


class GitRepository(models.Model):
    _inherit = "git.repository"

    # 'kyc_status': dict(self._fields['kyc_status'].selection)[kyc_status]

    def _convert_gitlab_webhook_to_odoo(self, data, **kwargs):
        object_kind = data.get("object_kind")
        event_type = data.get("event_type")
        # event = data.get('event')

        # assert event, "No event provided."

        _gitlab_date_to_datetime = self.organization_id._gitlab_date_to_datetime

        # 2015-05-17 18:08:09 UTC

        # _logger.error(data['object_attributes'].keys())

        vals = {
            "object": object_kind.upper(),
            "username": data.get("user_name", False),
            "email": data.get("user_email", False),
            "project_name": deep_get(data, "project.name", False),
            "url": deep_get(data, "object_attributes.url", False),
            "created_at": deep_get(
                data, "object_attributes.created_at", False, _gitlab_date_to_datetime
            ),
            "updated_at": deep_get(
                data, "object_attributes.updated_at", False, _gitlab_date_to_datetime
            ),
            "description": deep_get(data, "changes.description.current", False),
            "title": deep_get(data, "changes.title.current", False),
            "note": deep_get(data, "object_attributes.note", False),
            "merge_request": False,
        }

        if event_type == "merge_request":
            vals["merge_request"] = {
                "target_branch": deep_get(
                    data, "object_attributes.target_branch", False
                ),
                "source_branch": deep_get(
                    data, "object_attributes.source_branch", False
                ),
                "state": deep_get(data, "object_attributes.state", False),
            }
            vals["title"] = deep_get(data, "object_attributes.title", False)

        # _logger.warning(vals)

        return vals
