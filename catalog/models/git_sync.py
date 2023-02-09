# -*- coding: utf-8 -*-

from collections import OrderedDict
from datetime import datetime
import logging
import re
import time

from odoo import models, fields, api, _
from odoo.tools import safe_eval
from odoo.tools.misc import get_lang
from odoo.exceptions import UserError, ValidationError


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

    last_sync_date = fields.Datetime(readonly=True)
    service = fields.Selection([])
    sync_identifier = fields.Char(index=True)
    name = fields.Char(required=True)
    url = fields.Char()
    active = fields.Boolean(default=True)
    is_synchronized = fields.Boolean(default=False)
    partner_id = fields.Many2one(comodel_name='res.partner')
    rule_ids = fields.Many2many(comodel_name='git.rules')
    force_partner = fields.Boolean(default=False)

    exclude_names = fields.Char()


    def _update_tags(self, vals_list, records):
        def apply(vals):
            tags = [(4, tag.id) for tag in records]
            if tags:
                vals.setdefault('tag_ids', [])
                vals['tag_ids'] += tags
            return vals
        return list(map(apply, vals_list))


    def _prepare_module_info(self):
        info = {
            'application': False,
            'name': '',
            'technical_name': '',
            'author': 'Odoo S.A.',
            'auto_install': False,
            'category': 'Uncategorized',
            'depends': [],
            'description': '',
            'web_description': '',
            'icon_image': None,
            'installable': True,
            'post_load': None,
            # 'version': '1.0',
            'web': False,
            # 'sequence': 100,
            'summary': '',
            'website': '',
        }
        info.update(zip('depends data demo test init_xml update_xml demo_xml'.split(), iter(list, None)))

        return info.copy()

    def _get_manifest_mapping(self):
        info = {
            'application': 'application',
            'name': 'name',
            'technical_name': 'technical_name',
            'author': 'author',
            # 'auto_install': 'auto_install',
            'category': 'category',
            'depends': 'depends',
            'description': 'description',
            'web_description': 'web_description',
            'icon_image': 'icon_image',
            # 'installable': 'installable',
            # 'post_load': None,
            'version': 'version',
            # 'web': False,
            # 'sequence': 100,
            'summary': 'summary',
            'url': 'website',
            # 'external_dependencies': 'external_dependencies',
        }

        return info, list(info.keys())


    def _update_category(self, vals_list, categories):

        def apply(vals):
            search_key = vals.get('category', False)
            search_key = 'uncategorized' if not search_key else search_key.lower()

            # Exact match
            category = categories.get(search_key, False)

            if not category and '/' in search_key:
                items = search_key.split('/')
                category = categories.get(items[0], categories.get(items[-1], False))

            if not category:
                res = dict(filter(lambda item: search_key in item[0], categories.items()))
                category = list(res.values())[0] if res else False

            # _logger.warning(f"Search: {search_key}, Found: {category}")

            # del vals['category']
            vals['category_id'] = category

            return vals

        return list(map(apply, vals_list))

    def _update_depends(self, vals_list):
        def apply(vals):
            depends = vals.get('depends')
            if depends:
                vals['depends'] = ", ".join(depends)
            return vals
        return list(map(apply, vals_list))


    def _update_list_of_vals(self, vals_list, values):
        def apply(vals):
            vals.update(values)
            return vals
        return list(map(apply, vals_list))


    def _check_major_version(self, vals_list, regex=REGEX_MAJOR_VERSION):
        def apply(vals):
            vals['major'] = bool(regex.match(vals.get('name', False)))
            return vals
        return list(map(apply, vals_list))


    def _get_service(self, name):
        pass


    def __get_method(self, name, value, default_value, *args, **kwargs):
        method = name.format(value)
        # found = hasattr(self, method)
        # _logger.debug("Search {} in {}: {}".format(method, self._name, found))

        raise_if_not_exists = kwargs.get('raise_if_not_exists', False)
        # _logger.error(kwargs)

        if not hasattr(self, method):
            if raise_if_not_exists:
                raise NotImplementedError(f"Method not implemented for {self._description} on {self.service}.")

            _logger.error("No method '%s' found for %s", method, self._name)
            return default_value

        try:
            res = getattr(self, method)(*args, **kwargs)
        except Exception as error:
            _logger.error(error)
            res = default_value

        return res


    def _convert_to_odoo(self, item, **kwargs):
        return self.__get_method("_convert_{}_to_odoo", self.service, {}, item, **kwargs)


    def _get_item_for_odoo(self, **kwargs):
        return self.__get_method("_get_item_from_{}", self.service, {}, **kwargs)


    def _get_items_for_odoo(self, **kwargs):
        return self.__get_method("_get_items_from_{}", self.service, {}, **kwargs)


    def _get_commits_for_odoo(self, **kwargs):
        return self.__get_method("_get_commits_from_{}", self.service, {}, **kwargs)


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


    def _get_eval_context(self):
        """ Prepare the context used when evaluating python code
            :returns: dict -- evaluation context given to safe_eval
        """
        return {
            'datetime': safe_eval.datetime,
            'dateutil': safe_eval.dateutil,
            'time': safe_eval.time,
            'uid': self.env.uid,
            'user': self.env.user,
            'env': self.env,
        }


    def _apply_rule(self, rule, vals_list, context={}):
        def apply(vals):
            # _logger.error("Rule {o.name} : {o.condition}".format(o=rule))
            try:
                condition = eval(rule.condition, context, vals)

                if rule.action == 'ignore':
                    if not condition:
                        return vals
                else:
                    if condition:
                        if rule.code:
                            vals.update(eval(rule.code))
                        if rule.tag_ids:
                            vals.update({'tag_ids': [(4, tag.id) for tag in rule.tag_ids]})
                        if rule.partner_id:
                            vals.update({'partner_id': rule.partner_id.id})
                    return vals
            except ValueError as error:
                _logger.error(error)

        # return list(map(apply, vals_list))
        return list(filter(bool, map(apply, vals_list)))


    def _apply_rules(self, vals_list):
        self.ensure_one()

        rules = self._get_rules()

        if not rules:
            return vals_list

        # to_skip, to_delete = [], []
        context = self._get_eval_context()

        for action in ['ignore', 'update']:
            for current_rule in rules.get(action, []):
                vals_list = self._apply_rule(current_rule, vals_list, context)

            # _logger.warning("ignore: {}/{}".format(len(to_ignore), len(vals_list)))
        return vals_list


    def _filter_on_delay(self, delay):
        now = fields.Datetime.now()
        items = self.filtered(lambda x: not x.last_sync_date)

        for record in (self - items):
            delta = now - record.last_sync_date
            if delta.days >= 0 and delta.seconds >= delay:
                items |= record

        return items


    # @api.model
    def action_toggle_sync(self):
        for record in self:
            record.write({'is_synchronized': not record.is_synchronized})


    @api.model
    def _get_sync_delay(self):
        delay = self.env["ir.config_parameter"].sudo().get_param('catalog.sync_delay')
        return int(delay) if delay else 0


    @api.model
    def _get_major_version_regex(self):
        regex = self.env["ir.config_parameter"].sudo().get_param('catalog.odoo_major_version')
        return re.compile(regex)


    @api.model
    def _get_icon_search(self):
        res = self.env["ir.config_parameter"].sudo().get_param('catalog.enable_icon_search')
        return bool(res) or False


    @api.model
    def _get_test_mode(self):
        res = self.env["ir.config_parameter"].sudo().get_param('catalog.enable_test')
        try:
            test = bool(eval(res))
        except:
            test = False

        res = self.env["ir.config_parameter"].sudo().get_param('catalog.limit_test')
        limit = int(res) or 10

        return test, limit


    @api.model
    def _format_category(self, record):
        items = [record.name]
        if record.parent_id:
            items.insert(0, record.parent_id.name)

        return "/".join(map(lambda x: x.lower(), items))


    @api.model
    def _get_categories(self):
        """
        Return dict of ir.module categories (name & id) in english and current language if not the same
        """
        default_lang = get_lang(self.env).code
        languages = [default_lang]
        categories = {}

        languages = ['en_US']

        # if not default_lang.startswith('en_'):
        #     languages.append('en_US')

        # for lang in languages:
        #     records = self.env['ir.module.category'].with_context({'lang': lang}).search([]).read(['name', 'id'])
        #     categories.update({item['name'].lower():item['id'] for item in records})

        for lang in languages:
            records = self.env['ir.module.category'].with_context(**{'lang': lang}).search([])
            categories.update({self._format_category(record):record.id for record in records})

        categories = OrderedDict(sorted(categories.items()))
        # _logger.warning(list(categories.keys()))

        return categories


    @api.model
    def _prepare_sync_values(self, kwargs={}):
        vals = kwargs.copy()
        subtypes = self.env['mail.message.subtype'].search([]).read(['res_model'])

        vals['cron_mode'] = kwargs.get('cron', False)
        vals['job_count'] = kwargs.get('job_count', 10)
        vals['force_update'] = kwargs.get('force_update', False)
        vals['sync_delay'] = kwargs.get('delay', self._get_sync_delay())
        vals['regex'] = self._get_major_version_regex()
        vals['subtypes'] = {item['res_model']:item['id'] for item in subtypes}

        if self._name == 'git.branch':
            vals['categories'] = self._get_categories()

        return vals


    def _group_records_by_identidier(self, values):

        identifiers = list(set(self.mapped('sync_identifier')))
        # records_by_sync = [self.filtered(lambda rec: rec.sync_identifier == id) for id in identifiers]
        records_by_sync = [self.filtered_domain(['sync_identifier', '=', id]) for id in identifiers]

        result = []

        for records in records_by_sync:
            records = records.sorted()
            # prev_count = len(records)

            # records = records._filter_on_delay(values['sync_delay'])
            # _logger.warning("Filter items on delay: {}/{}".format(len(records), prev_count))

            chunked_ids = [records.ids[i:i+values['job_count']] for i in range(0, len(records.ids), values['job_count'])]
            for current_ids in chunked_ids:
                # current_records = records.browse(current_ids)
                result.append(current_ids)

        # _logger.warning("Group records: %s" % result)

        return result


    def action_update_commits(self):
        self.ensure_one()
        try:
            vals_list = self._get_commits_for_odoo(raise_if_not_exists=True)
        except NotImplementedError as error:
            raise UserError(error)
        except Exception as error:
            _logger.error(error)
            vals_list = []

        # _logger.error(f"{self._name}: {self.id} / {len(vals_list)}")


        self.write({'commit_ids': [(5, False, False)] + [(0, False, vals) for vals in vals_list]})
        return True


    @api.model
    def _action_sync(self, ids=[], **kwargs):

        values = self._prepare_sync_values(kwargs)
        result = []
        all_records = self.browse(ids)
        chunk_ids = all_records._group_records_by_identidier(values)

        # if values['cron_mode']:
        #     return True

        for current_ids in chunk_ids:
            records = all_records.browse(current_ids)
            for record in records:
                res = record._action_process(**values)
                result.append(res)

            # records_by_service.write({'last_sync_date': datetime.now()})
        # return all(result) if result else False
        return True


    def _action_process(self, **kwargs):
        self.ensure_one()
        # use_new_cursor = kwargs.get('use_new_cursor', False)
        force_update = kwargs.get('force_update', False)

        # if use_new_cursor:
        #     cr = registry(self._cr.dbname).cursor()
        #     self = self.with_env(self.env(cr=cr))

        # excludes = self._get_excludes()
        subtypes = kwargs.get('subtypes', {})
        regex = kwargs.get('regex')
        categories = kwargs.get('categories', {})

        # _logger.warning("Excludes: {}".format(excludes))

        # Get items from specific methods
        start = time.time()
        items = self._get_items_for_odoo()
        end = time.time()
        end -= start

        # try:
        #     items = [item for item in items if item.name not in excludes]
        # except AttributeError:
        #     items = [item for item in items if item.get('name') not in excludes]

        # Prepare values, aka convert Git(hub/lab) values to Odoo values
        vals_list = [self._convert_to_odoo(item) for item in items]

        _logger.warning("Execution time: %s, %s items", end, len(vals_list))

        # << No values, end of treatment >>
        if not vals_list:
            self.write({'last_sync_date': datetime.now()})
            return True

        if self._name == 'git.branch':
            tags = self.repository_id.tag_ids
            vals_list = self._update_category(vals_list, categories)
            vals_list = self._update_tags(vals_list, tags)
            vals_list = self._update_depends(vals_list)
            vals_list = self._update_list_of_vals(vals_list, {'last_sync_date': datetime.now()})

        if self._name == 'git.repository':
            vals_list = self._check_major_version(vals_list, regex)

        # Apply rules and filter
        vals_list = self._apply_rules(vals_list)

        _logger.warning("After rules: %s items", len(vals_list))

        # Prepare for create or update
        match_field = self._git_field_name
        rel_field = self._git_field_rel
        model_name = self[rel_field]._name
        model_desc = self[rel_field]._description
        parent = self[self._git_parent_field] if self._git_parent_field else False

        # Set origin from current record
        vals_list = self._update_list_of_vals(vals_list, {'origin': f"{self.name} (Id: {self.id})"})

        if self.partner_id and self.force_partner:
            vals_list = self._update_list_of_vals(vals_list, {'partner_id': self.partner_id.id})

        # if not force_update:
        #     vals_list = self._update_list_of_vals(vals_list, {'last_sync_date': datetime.now()})

        # Simple search from current record
        if self._git_type_rel == 'o2m':
            object_ids = {e[match_field]:e['id'] for e in self[rel_field].read([match_field])}
            to_update = [(1, object_ids.get(vals[match_field]), vals) for vals in vals_list if vals[match_field] in object_ids.keys()]
        # More complex, search for all records from rel model
        elif self._git_type_rel == 'm2m':
            object_ids = {e[match_field]:e['id'] for e in self.env[model_name].search([]).read([match_field])}
            to_update = [(4, object_ids.get(vals[match_field])) for vals in vals_list if vals[match_field] in object_ids.keys()]

        to_create = [(0, False, vals) for vals in vals_list if vals[match_field] not in object_ids]


        sync_message = f"Synchronize {self._name} '{self.name}': {len(vals_list)} {model_name} found (updated: {len(to_update)}, created: {len(to_create)})"


        self.message_post(body=sync_message, message_type='notification')

        child_ids = self[rel_field]
        self.update({rel_field: to_update + to_create})

        # if use_new_cursor:
        #     self._cr.commit()

        new_childs = self[rel_field] - child_ids

        # [record]                  [child]             [parent field]
        # git.organization  -->     git.repository
        # git.repository    -->     git.branch          organization_id
        # git.branch        -->     custom.addon        repository_id


        parent_name = parent.name if parent else ''

        subtype_id = True
        if subtype_id and new_childs:
            names = ", ".join(new_childs.mapped('name'))
            # names = "".join(["<li>{}</li>".format(name) for name in new_childs.mapped('name')])
            message = {
                'subject': 'GIT',
                'body': BODY.format(_(model_desc), self.name, parent_name, names),
                'message_type': 'notification',
                # 'subtype_id': subtype_id.id
            }
            if self._name == 'git.branch' and parent:
                subtype_id = subtypes.get(parent._name)
                if subtype_id:
                    message['subtype_id'] = subtype_id
                parent.message_post(**message)
            else:
                subtype_id = subtypes.get(self._name)
                if subtype_id:
                    message['subtype_id'] = subtype_id
                self.message_post(**message)

        if force_update:
            to_update = {object_ids.get(vals[match_field]):vals for vals in vals_list if vals[match_field] in object_ids.keys()}
            record_ids = self.env[model_name].browse(to_update.keys())
            for rec in record_ids:
                # _logger.warning("Update forced on {} {}".format(model_name, rec.id))
                vals = to_update.get(rec.id)
                # vals['last_sync_date'] = datetime.now()
                rec.update(vals)

        self.write({'last_sync_date': datetime.now()})

        # if use_new_cursor:
        #     self._cr.commit()

        #     try:
        #         self._cr.close()
        #     except Exception:
        #         pass

        return True


    def action_sync(self):
        # self.with_delay()._action_sync(self.ids, force_update=False)
        self._action_sync(self.ids, force_update=True)


    def _action_update(self, **kwargs):
        self.ensure_one()
        vals = {}

        parent = self[self._git_parent_field] if self._git_parent_field else False
        # _logger.error(parent)
        if parent:
            item = self._get_item_for_odoo(raise_if_not_exists=True)
            vals = parent._convert_to_odoo(item, contributors=True)
            # _logger.warning(vals)

        vals['last_sync_date'] =  datetime.now()
        self.write(vals)


    def action_update(self):
        for record in self:
            try:
                record._action_update()
            except Exception as error:
                raise ValidationError(error)
