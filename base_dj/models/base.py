# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.addons.website.models.website import slugify


class Base(models.AbstractModel):

    _inherit = 'base'

    def _dj_xmlid_export_module(self):
        """Customize module name for dj compilation.

        By default is `__setup__` but you can force it via
        `dj_xmlid_module` context var.
        """
        return self.env.context.get('dj_xmlid_module', '__setup__')

    def _dj_xmlid_global_config(self):
        """Retrieve default global config for xmlid fields."""
        config = self.env['dj.equalizer.xmlid'].search([
            ('model', '=', self._name),
        ], limit=1)
        _fields = config and config.get_xmlid_fields() or []
        if not _fields and 'name' in self and 'name' not in _fields:
            # we assume we can use name as default
            _fields.append('name')
        return _fields

    def _dj_xmlid_export_name(self):
        """Customize xmlid name for dj compilation.

        You can specify field names by model name
        into context variable `dj_xmlid_fields_map`
        to be used for xmlid generation.
        Strings will be normalized.
        """
        name = [self._table, str(self.id)]
        mapping = self.env.context.get('dj_xmlid_fields_map', {})
        xmlid_fields = \
            mapping.get(self._name) or self._dj_xmlid_global_config()
        if xmlid_fields:
            name = [self._table, ]
            for key in xmlid_fields:
                if not self[key]:
                    continue
                value = self[key]
                if isinstance(value, basestring):
                    value = slugify(value).replace('-', '_')
                elif isinstance(value, models.BaseModel):
                    value = slugify(value.display_name).replace('-', '_')
                elif isinstance(value, (int, float)):
                    value = str(value)
                name.append(value)
        if (self.env.context.get('dj_multicompany') and
                'company_id' in self and self.company_id.aka):
            # discriminate by company `aka` code
            name.insert(0, self.company_id.normalized_aka())
        return '_'.join(name)

    def _dj_export_xmlid(self):
        """Shortcut to force dj xmlid generation."""
        return self.with_context(dj_export=1)._BaseModel__export_xml_id()

    def _BaseModel__export_xml_id(self):
        """Customize xmlid creation.

        Barely copied from `odoo.models` and hacked a bit.

        Being a private method we are forced to name it like this.
        See https://docs.python.org/2/tutorial/classes.html#private-variables-and-class-local-references
        """  # noqa
        if not self.env.context.get('dj_export'):
            return super(Base, self)._BaseModel__export_xml_id()

        module = self._dj_xmlid_export_module()
        base_name = self._dj_xmlid_export_name()

        if not self._is_an_ordinary_table():
            raise Exception(
                "You can not export the column ID of model %s, because the "
                "table %s is not an ordinary table."
                % (self._name, self._table))
        ir_model_data = self.sudo().env['ir.model.data']

        # we want to discard autogenerated xmlids
        # and keep only modules' ones
        data = ir_model_data.search([
            ('model', '=', self._name),
            ('res_id', '=', self.id),
            ('module', 'not in', ('__export__', module)),
        ], order='create_date desc', limit=1)
        if data:
            if data.module:
                return '%s.%s' % (data.module, data.name)
            else:
                return data.name
        else:
            name = base_name[:]

            # same name, same record
            existing = ir_model_data.search([
                ('module', '=', module),
                ('name', '=', name),
                ('model', '=', self._name),
                ('res_id', '=', self.id),
            ], limit=1)
            if existing:
                # cool, use it
                return module + '.' + name

            # in case of collision, generate a new one
            postfix = 0
            while ir_model_data.search([('module', '=', module),
                                        ('name', '=', name)], limit=1):
                postfix += 1
                name = '%s_%d' % (base_name, postfix)
            ir_model_data.create({
                'model': self._name,
                'res_id': self.id,
                'module': module,
                'name': name,
            })
            return module + '.' + name
