# -*- coding: utf-8 -*-
# Copyright 2021 Apulia Software s.r.l. (<info@apuliasoftware.it>)
# License AGPL-3 or later (https://www.gnu.org/licenses/agpl-3.0).

from odoo import models, fields, api
from odoo.exceptions import UserError


class AccountInvoiceLine(models.Model):

    _inherit = 'account.invoice.line'

    is_details = fields.Boolean(default=True)

    @api.onchange('is_details')
    def onchange_is_details(self):
        if self.is_details and not self.invoice_id.use_line_details:
            raise UserError(
                    ("Active Use line details"))

class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    use_line_details = fields.Boolean(default=True)

    @api.onchange('use_line_details')
    def onchange_use_line_details(self):
        for line in self.invoice_line_ids:
            line.is_details =  self.use_line_details
