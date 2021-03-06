# -*- coding: utf-8 -*-
# Copyright (C) DEC SARL, Inc - All Rights Reserved.
# Written by Yann Papouin <y.papouin at dec-industrie.com>, Dec 2020

from odoo import models, api, fields


class IrMailServer(models.Model):
    _inherit = "ir.mail_server"

    auto_add_sender = fields.Boolean(
        help="Automatically add sender to the list of hidden recipients",
    )
    auto_cc_addresses = fields.Text(
        'Auto CC addresses',
        help="Comma-separated list of auto Cc addresses",
    )
    auto_bcc_addresses = fields.Text(
        'Auto BCC addresses',
        help="Comma-separated list of auto Bcc addresses",
    )

    @api.model
    def send_email(
        self,
        message,
        mail_server_id=None,
        smtp_server=None,
        smtp_port=None,
        smtp_user=None,
        smtp_password=None,
        smtp_encryption=None,
        smtp_debug=False,
        smtp_session=None
    ):
        # Get mail_server like it's done in
        # addons/base/models/ir_mail_server.py
        if mail_server_id:
            mail_server = self.sudo().browse(mail_server_id)
        elif not smtp_server:
            mail_server = self.sudo().search([], order='sequence', limit=1)
        else:
            mail_server = False

        if mail_server and mail_server.auto_cc_addresses:
            if not message.get('Cc'):
                message['Cc'] = mail_server.auto_cc_addresses
            else:
                del message['Cc']  # avoid multiple Cc: headers!
                message['Cc'] += "," + mail_server.auto_cc_addresses

        auto_bcc_addresses = mail_server.auto_bcc_addresses
        if mail_server.auto_add_sender:
            if not auto_bcc_addresses:
                auto_bcc_addresses = message['From']
            else:
                auto_bcc_addresses += "," + message['From']

        if mail_server and auto_bcc_addresses:
            if not message.get('Bcc'):
                message['Bcc'] = auto_bcc_addresses
            else:
                del message['Bcc']  # avoid multiple Bcc: headers!
                message['Bcc'] += "," + auto_bcc_addresses

        message_id = super(IrMailServer, self).send_email(
            message,
            mail_server_id=mail_server_id,
            smtp_server=smtp_server,
            smtp_port=smtp_port,
            smtp_user=smtp_user,
            smtp_password=smtp_password,
            smtp_encryption=smtp_encryption,
            smtp_debug=smtp_debug,
            smtp_session=smtp_session
        )
        return message_id
