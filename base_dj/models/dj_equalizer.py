# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval


class DJEqualizer(models.Model):
    """Hold models' global configuration."""

    _name = 'dj.equalizer'

    model = fields.Char(default='')
    xmlid_fields = fields.Char(default='')
    xmlid_table_name = fields.Char(
        default='',
        help='Sometimes the xmlid can be veeeeery long, like for companies. '
             'You can use this field to short a bit the result. '
             'For instance: `res_company` -> `company`.')
    model_context = fields.Char(default='{}')

    @api.multi
    def get_xmlid_fields(self):
        self.ensure_one()
        return [x.strip() for x in self.xmlid_fields.split(',')
                if x.strip()] if self.xmlid_fields else []

    @api.multi
    def get_model_context(self):
        self.ensure_one()
        return safe_eval(self.model_context) if self.model_context else {}

    def get_conf(self):
        return {
            'xmlid_fields': self.get_xmlid_fields(),
            'xmlid_table_name': self.xmlid_table_name,
            'model_context': self.get_model_context(),
        }
