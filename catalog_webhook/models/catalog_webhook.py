# -*- coding: utf-8 -*-

import logging
import threading

from odoo import models, fields, api, registry, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

DEFAULT_MESSAGE = "<strong>{}</strong>: {} ({}), on {}"

class CatalogWebhook(models.Model):
    _name = 'catalog.webhook'
    _description = 'Catalog Webhook'

    def _default_uuid(self):
        return self.env['git.organization'].sudo()._generate_token()[:20]

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    hook_id = fields.Char(string="Hook ID")
    res_id = fields.Integer()
    res_model = fields.Char()
    repository_id = fields.Many2one('git.repository')
    organization_id = fields.Many2one(related='repository_id.organization_id')
    uuid = fields.Char(default=_default_uuid, required=True)
    webhook_url = fields.Char(compute='_compute_url')
    branch_filter = fields.Char(string="Branch filter")
    url = fields.Char()
    action = fields.Selection([('post', 'Post message')])

    allowed_event_ids = fields.One2many('catalog.webhook.event', compute='_compute_event_ids')
    event_ids = fields.Many2many(
        string="Events",
        comodel_name="catalog.webhook.event",
        relation="git_webhook_event_rel",
        column1="webhook_id",
        column2="event_id",
        tracking=True,
    )

    line_ids = fields.One2many('catalog.webhook.line', inverse_name='webhook_id')

    @api.depends('uuid', 'repository_id')
    def _compute_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        base_url = base_url.replace("http://localhost:8069", "https://test.com")
        for record in self:
            record.webhook_url = "{}/webhook/catalog/{}".format(base_url, record.uuid)


    @api.depends('repository_id')
    def _compute_event_ids(self):
        events = self.env['catalog.webhook.event'].search([])
        for record in self:
            record.allowed_event_ids = events.filtered_domain([('service', '=', record.organization_id.service)])


    def _get_valid_events(self):
        self.ensure_one()
        return self.event_ids.mapped('event')

    @api.model
    def _get_by_id(self, id):
        record = self.search([('uuid', '=', id)], limit=1)
        return record


    def _action_post_message(self, data, use_new_cursor=False):
        if use_new_cursor:
            cr = registry(self._cr.dbname).cursor()
            self = self.with_env(self.env(cr=cr))

		# working
        repository = self.repository_id
        user_name = data.get('user_name', 'Unknown user')
        user_email = data.get('user_email', '')
        project_name = data.get('project', {}).get('name', 'project')
        object_kind = data.get('object_kind', '???')

        try:
            body = DEFAULT_MESSAGE.format(object_kind, user_name, user_email, project_name)
            repository.message_post(body=body, message_type='comment')
        except Exception as error:
            _logger.error(error)
            if use_new_cursor:
                cr.rollback()
            else:
                raise

        if use_new_cursor:
            cr.commit()
            cr.close()


    def _run_postprocess_thread(self, data):
        _logger.error(data)
        with api.Environment.manage():
            new_cr = self.pool.cursor()
            self = self.with_env(self.env(cr=new_cr))

            if self.action == 'post':
                self._action_post_message(data, use_new_cursor=self._cr.dbname)

        new_cr.close()

        return {}

    def action_postprocess_thread(self, data):
        threaded_calculation = threading.Thread(target=self._run_postprocess_thread, kwargs=dict(data=data))
        threaded_calculation.start()
        return {}


    def _prepare_webhook_values(self):
        self.ensure_one()

        token = self.repository_id.organization_id.webhook_token

        if not token:
            raise ValidationError("No token provided.")

        vals = self._get_event_values()
        vals.update({
            'url': self.webhook_url,
            'token': token,
            'enable_ssl_verification': True,
            'push_events_branch_filter': self.branch_filter,
        })

        return vals


    def action_open_url(self):
        self.ensure_one()

        if not self.repository_id.url:
            return False

        action = {
            "type": "ir.actions.act_url",
            "url": self.repository_id.url,
            "target": "new",
        }

        return action

    def _get_event_values(self):
        vals = {k:False for k in self.allowed_event_ids.mapped('code')}
        vals.update({k:True for k in self.event_ids.mapped('code')})

        return vals


    def action_update(self):
        """
            {
                'id': 333333,
                'url': 'https://xxxxxxxx/xxxxxxx-10cc-4c1a-a',
                'created_at': '2023-01-16T22:51:13.309Z',
                'push_events': True,
                'tag_push_events': False,
                'merge_requests_events': False,
                'repository_update_events': False,
                'enable_ssl_verification': True,
                'alert_status': 'executable',
                'disabled_until': None,
                'url_variables': [],
                'project_id': 99999999,
                'issues_events': False,
                'confidential_issues_events': False,
                'note_events': False,
                'confidential_note_events': None,
                'pipeline_events': False,
                'wiki_page_events': False,
                'deployment_events': False,
                'job_events': True,
                'releases_events': False,
                'push_events_branch_filter': None
                }
        """
        vals = self._prepare_webhook_values()
        # _logger.warning(vals)

        project = self.repository_id._get_item_for_odoo()

        if not self.hook_id:
            hook = project.hooks.create(vals)
        else:
            hook = project.hooks.get(self.hook_id)
            new_values = hook.asdict()
            new_values.update(vals)

            # _logger.warning(hook.asdict())
            # hook._update_attrs(new_values)

            hook.push_events = new_values.get('push_events')
            hook.push_events_branch_filter = new_values.get('push_events_branch_filter')

            hook.tag_push_events = new_values.get('tag_push_events')
            hook.merge_requests_events = new_values.get('merge_requests_events')
            hook.repository_update_events = new_values.get('repository_update_events')
            hook.issues_events = new_values.get('issues_events')
            hook.confidential_issues_events = new_values.get('confidential_issues_events')
            hook.note_events = new_values.get('note_events')
            hook.confidential_note_events = new_values.get('confidential_note_events')
            hook.pipeline_events = new_values.get('pipeline_events')
            hook.wiki_page_events = new_values.get('wiki_page_events')
            hook.job_events = new_values.get('job_events')
            hook.deployment_events = new_values.get('deployment_events')

            hook.url = new_values.get('url')
            hook.enable_ssl_verification = new_values.get('enable_ssl_verification')

            # _logger.error(new_values)
            # hook.url = self.webhook_url
            hook.save()

            # _logger.warning(hook.asdict())

        if hook:
            self.write({
                'hook_id': hook.id,
                'url': hook.url,
            })