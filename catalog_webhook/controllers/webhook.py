# -*- coding: utf-8 -*-

import logging
import json

from odoo import models, fields, api, registry, SUPERUSER_ID
from odoo.http import Controller, request, route, Response

_logger = logging.getLogger(__name__)

NEW_COMMIT_MESSAGE = "{} ({}) just pushed new commits on {}."


class WebhookController(Controller):

	@route('/webhook/catalog/<string:id>', type='json', auth="public", website=True, csrf=False)
	def catalog_public_webhook(self, id, **kwargs):

		tokens = request.env['git.organization'].sudo()._get_tokens()

		if not tokens:
			raise ValueError('Please set Gitlab Token to use webhook.')

		# Parse json data not in params key
		data = request.jsonrequest
		# user_name = data.get('user_name', 'Unknown user')
		# user_email = data.get('user_email', '')
		# project_name = data.get('project', {}).get('name', 'project')

		received_token = request.httprequest.headers.get('X-Gitlab-Token')
		received_event = request.httprequest.headers.get('X-Gitlab-Event')

		# _logger.error(received_event)
		# _logger.debug(request)

		if not received_token or received_token not in tokens:
			_logger.error("Received token missing or not matching.")
			return {"status": "error"}

		webhook = request.env['catalog.webhook'].sudo()._get_by_id(id)

		if not webhook:
			_logger.error("No webhook.")
			return {"status": "error"}

		valid_events = webhook._get_valid_events()

		if not received_event or received_event not in valid_events:
			_logger.error("Received event missing or unknown.")
			return {"status": "error"}

		webhook.action_postprocess_thread(dict(received_event=received_event, **data))


		# database = request.env['saas.database'].sudo().search(domain, limit=1)
		# if not database or database.database_type_id.is_production:
		# 	_logger.error("Database not found, not active or production type.")
		# 	return {"status": "error"}

		# _logger.warning("Rebuild requested for database {}".format(database.name))

		# body = NEW_COMMIT_MESSAGE.format(user_name, user_email, project_name)
		# database.message_post(body=body, message_type='comment')

		# # FIXME: Commit is really necessary ?
		# request.env.cr.commit()

		# database.action_rebuild_thread()

		return {"status": "success"}


