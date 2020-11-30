# -*- coding: utf-8 -*-
# Copyright (C) DEC SARL, Inc - All Rights Reserved.
# Written by Yann Papouin <y.papouin at dec-industrie.com>, Nov 2020

from odoo import models, api, fields
from odoo.tools import html2plaintext


def activity_state_to_emoji(state):
    res = state
    if res == 'overdue':
        res = '🕸️'
    elif res == 'today':
        res = '✅'
    elif res == 'planned':
        res = '📅'
    return res


class MailActivity(models.Model):
    _inherit = "mail.activity"

    state_emoji = fields.Char(compute='_compute_state_emoji')

    @api.multi
    def _compute_state_emoji(self):
        for rec in self:
            rec.state_emoji = activity_state_to_emoji(rec.state)

    def get_head_desc(self):
        state = dict(self._fields['state']._description_selection(self.env)
                    ).get(self.state)
        product_name = self.product_id.product_tmpl_id.display_name
        activity_text = html2plaintext(self.note or self.summary)
        activity_text = activity_text.replace(product_name, '')
        head = '⚠️{0}'.format(activity_text)
        desc = '{0}{1}'.format(self.state_emoji, state)
        return head, desc