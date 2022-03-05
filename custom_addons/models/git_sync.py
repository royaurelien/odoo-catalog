# -*- coding: utf-8 -*-

from multiprocessing import synchronize
from odoo import models, fields, api, _

from datetime import datetime
import logging
from random import randint
import re

_logger = logging.getLogger(__name__)
REGEX_MAJOR_VERSION = re.compile("^(0|[1-9]\d*)\.(0|[1-9]\d*)$")
BODY = """
<html>
New <b>{}</b> from {} ({}): <ul><li>{}</li></ul>
</html>
"""

class GitSync(models.AbstractModel):
    _name = "git.sync"
    _description = "Git Sync"

    # _github_type = "repository"

    _git_service = ""
    _git_field_rel = ""
    _git_field_name = ""
    _git_type_rel = ""
    _git_parent_field = False

    last_sync_date = fields.Datetime(string="Last Sync Date", readonly=True)
    service = fields.Selection([])
    name = fields.Char(required=True)
    url = fields.Char()
    active = fields.Boolean(default=True)
    is_synchronized = fields.Boolean(default=False)
    partner_id = fields.Many2one(comodel_name='res.partner')
    rule_ids = fields.Many2many(comodel_name='git.rules')

    exclude_names = fields.Char()


    def _get_service(self, name):
        pass

    def __get_method(self, name, value, default_value, *args, **kwargs):
        method = name.format(value)
        found = hasattr(self, method)
        _logger.debug("Search {} in {}: {}".format(method, self._name, found))
        return getattr(self, method)(*args) if hasattr(self, method) else default_value

    def _convert_to_odoo(self, item):
        return self.__get_method("_convert_{}_to_odoo", self.service, {}, item)

    def _get_items_for_odoo(self, service=None):
        return self.__get_method("_get_items_from_{}", self.service, {})

    def _get_rules(self):
        rules = self.env['git.rules'].search([('model', '=', self._name)])
        filtered_rules = rules.filtered(lambda rec: rec.is_global)

        if self._name != 'git.organization':
            filtered_rules+= rules.filtered(lambda rec: self.organization_id.id in rec.organization_ids.ids)

        actions = list(set(rules.mapped('action')))
        dict_rules = {action:rules.filtered(lambda rec: rec.action == action) for action in actions}

        return dict_rules

    def _get_excludes(self):
        return [name.strip() for name in self.exclude_names.split(",") if name] if self.exclude_names else []

    def _apply_rules(self, vals_list):
        self.ensure_one()

        rules = self._get_rules()
        if not rules:
            return vals_list

        to_skip, to_delete = [], []

        for current_rule in rules.get('delete', []):
            for index, vals in enumerate(vals_list):
                if eval(current_rule.condition):
                    _logger.debug("Skip {}".format(vals))
                    to_skip += [index]
                    to_delete += [vals]

        # exclude items
        vals_list = [vals for index, vals in enumerate(vals_list) if index not in to_skip]

        for vals in vals_list:
            for current_rule in rules.get('update', []):
                if eval(current_rule.condition):
                    vals.update(eval(current_rule.code))
            for current_rule in rules.get('add_tag', []):
                if eval(current_rule.condition):
                    vals.update({'tag_ids': [(4, tag.id) for tag in current_rule.tag_ids]})
            for current_rule in rules.get('add_partner', []):
                _logger.debug("Condition : {} = {}".format(current_rule.condition, eval(current_rule.condition)))
                if eval(current_rule.condition):
                    vals.update({'partner_id': current_rule.partner_id.id})

        return vals_list

    @api.model
    def _action_sync(self, ids, **kwargs):
        records = self.browse(ids)
        force_update = kwargs.get('force_update', False)

        # subtype_id = self.env['mail.message.subtype'].search([('res_model', '=', self._name)],limit=1)
        # subtype_id = self.env['mail.message.subtype'].search([('res_model', '=', 'git.repository')],limit=1)

        subtypes = self.env['mail.message.subtype'].search([]).read(['res_model'])
        subtypes = {item['res_model']:item['id'] for item in subtypes}
        _logger.error(subtypes)

        for service_name in list(set(records.mapped(self._git_service))):

            records_by_service = records.filtered(lambda rec: rec.service == service_name)
            _logger.warning("Run action sync for {} service on {} items.".format(service_name, len(records_by_service)))

            for record in records_by_service:
                excludes = record._get_excludes()

                _logger.debug("Excludes: {}".format(excludes))

                # Get items from specific methods
                items = record._get_items_for_odoo()
                try:
                    items = [item for item in items if item.name not in excludes]
                except AttributeError:
                    items = [item for item in items if item.get('name') not in excludes]

                # Prepare values, aka convert Git(hub/lab) values to Odoo values
                vals_list = [record._convert_to_odoo(item) for item in items]

                # Apply rules and filter
                vals_list = record._apply_rules(vals_list)

                # Prepare for create or update
                match_field = record._git_field_name
                rel_field = record._git_field_rel
                model_name = record[rel_field]._name
                model_desc = record[rel_field]._description
                parent = record[record._git_parent_field] if record._git_parent_field else False

                # Simple search from current record
                if record._git_type_rel == 'o2m':
                    object_ids = {e[match_field]:e['id'] for e in record[rel_field].read([match_field])}
                    to_update = [(1, object_ids.get(vals[match_field]), vals) for vals in vals_list if vals[match_field] in object_ids.keys()]
                # More complex, search for all records from rel model
                elif record._git_type_rel == 'm2m':
                    object_ids = {e[match_field]:e['id'] for e in self.env[model_name].search([]).read([match_field])}
                    to_update = [(4, object_ids.get(vals[match_field])) for vals in vals_list if vals[match_field] in object_ids.keys()]


                to_create = [(0, False, vals) for vals in vals_list if vals[match_field] not in object_ids]

                sync_message = "{} '{}' >> {} {} found (updated: {}, created: {})".format(self._name,
                                                                                     record.name,
                                                                                     len(vals_list),
                                                                                     model_name,
                                                                                     len(to_update),
                                                                                     len(to_create))


                _logger.warning(sync_message)
                record.message_post(body=sync_message, message_type='notification')

                child_ids = record[rel_field]
                record.update({rel_field: to_update + to_create})
                new_childs = record[rel_field] - child_ids
                _logger.error("Childs created: {}".format(new_childs.mapped('name')))

                # [record]                  [childs]            [parent field]
                # git.organization  -->     git.repository
                # git.repository    -->     git.branch          organization_id
                # git.branch        -->     custom.addon        repository_id


                parent_name = parent.name if parent else ''

                subtype_id = True
                if subtype_id:
                    names = ", ".join(new_childs.mapped('name'))
                    # names = "".join(["<li>{}</li>".format(name) for name in new_childs.mapped('name')])
                    message = {
                        'subject': 'GIT',
                        'body': BODY.format(_(model_desc), record.name, parent_name, names),
                        'message_type': 'notification',
                        # 'subtype_id': subtype_id.id
                    }
                    if self._name == 'git.branch' and parent:
                        subtype_id = subtypes.get(parent._name)
                        if subtype_id:
                            message['subtype_id'] = subtype_id
                        parent.message_post(**message)
                    else:
                        subtype_id = subtypes.get(record._name)
                        if subtype_id:
                            message['subtype_id'] = subtype_id
                        record.message_post(**message)

                if force_update:
                    to_update = {object_ids.get(vals[match_field]):vals for vals in vals_list if vals[match_field] in object_ids.keys()}
                    record_ids = self.env[model_name].browse(to_update.keys())
                    for rec in record_ids:
                        _logger.warning("Update forced on {} {}".format(model_name, rec.id))
                        vals = to_update.get(rec.id)
                        vals['last_sync_date'] = datetime.now()
                        rec.update(vals)


            records_by_service.write({'last_sync_date': datetime.now()})

    def action_sync(self):
        self._action_sync(self.ids, force_update=False)

