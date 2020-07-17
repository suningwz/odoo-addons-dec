# -*- coding: utf-8 -*-
# Copyright (C) DEC SARL, Inc - All Rights Reserved.
# Written by Yann Papouin <y.papouin at dec-industrie.com>, Mar 2020

from odoo import fields, models


class RefCategoryLine(models.Model):
    """ Description """

    _name = 'ref.category.line'
    _description = 'Category line'
    _rec_name = 'description'
    _order = 'sequence'

    category = fields.Many2one('ref.category', 'Category', required=True)
    property = fields.Many2one('ref.property', 'Property', required=True)
    description = fields.Char('Property description', size=128)
    sequence = fields.Integer('Position', required=True)
