# -*- coding: utf-8 -*-

import logging
import threading

from odoo import models, fields, api, registry, _

_logger = logging.getLogger(__name__)

DEFAULT_MESSAGE = "<strong>{}</strong>: {} ({}), on {}"

class CatalogWebhook(models.Model):
    _name = 'catalog.webhook'
    _description = 'Catalog Webhook'

    def _default_uuid(self):
        return self.env['git.organization'].sudo()._generate_token()[:20]

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    res_id = fields.Integer()
    res_model = fields.Char()
    repository_id = fields.Many2one('git.repository')
    organization_id = fields.Many2one(related='repository_id.organization_id')
    uuid = fields.Char(default=_default_uuid, required=True)
    webhook_url = fields.Char(compute='_compute_url', store=True)
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

    @api.depends('uuid')
    def _compute_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        # base_url = "https://recette-catalog.apik.cloud"
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
                _logger.warning('POST')

                self._action_post_message(data, use_new_cursor=self._cr.dbname)
        new_cr.close()

        return {}

    def action_postprocess_thread(self, data):
        threaded_calculation = threading.Thread(target=self._run_postprocess_thread, kwargs=dict(data=data))
        threaded_calculation.start()
        return {}


    def _prepare_webhook_values(self):
        self.ensure_one()

        vals = {value: 1 for value in self.event_ids.mapped('code')}
        vals.update({
            'url': self.webhook_url,
            'token': self.repository_id.organization_id.webhook_token,
            'enable_ssl_verification': True,
        })

        return vals


    def action_update(self):
        vals = self._prepare_webhook_values()
        _logger.warning(vals)

        project = self.repository_id._get_item_for_odoo()
        hook = project.hooks.create(vals)

        _logger.error(hook)

        if hook:
            self.url = hook.url