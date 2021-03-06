# -*- coding: utf-8 -*-
# Copyright (C) DEC SARL, Inc - All Rights Reserved.
# Written by Yann Papouin <y.papouin at dec-industrie.com>, Mar 2020

from odoo import fields, models


class RefAttribute(models.Model):
    """ Description """

    _name = 'ref.attribute'
    _description = 'Attribute'
    _rec_name = 'name'
    _order = 'value'

    property_id = fields.Many2one(
        'ref.property',
        'Property (owner)',
        required=True,
        oldname='owner',
    )
    value = fields.Text(
        'Value',
        required=True,
    )
    name = fields.Text(
        'Name',
        required=True,
    )
