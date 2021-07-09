# -*- coding: utf-8 -*-
# Copyright 2021 Apulia Software s.r.l. (<info@apuliasoftware.it>)
# License AGPL-3 or later (https://www.gnu.org/licenses/agpl-3.0).

from odoo import models
from odoo.tools.translate import _
from odoo.tools.float_utils import float_round
from odoo.exceptions import UserError
from unidecode import unidecode
from odoo.addons.l10n_it_account.tools.account_tools import encode_for_export
from odoo.addons.l10n_it_fatturapa.bindings.fatturapa import (
    DettaglioLineeType,
    AltriDatiGestionaliType,
    CodiceArticoloType,
)


class WizardExportFatturapa(models.TransientModel):

    _inherit = "wizard.export.fatturapa"

    def setDettaglioLinee(self, invoice, body):
        res = super(WizardExportFatturapa, self).setDettaglioLinee(invoice, body)
        if not invoice.use_line_details:
            return res
        else:
            body.DatiBeniServizi.DettaglioLinee = []
            line_no = 1
            price_precision = self.env['decimal.precision'].precision_get(
                'Product Price for XML e-invoices')
            if price_precision < 2:
                # XML wants at least 2 decimals always
                price_precision = 2
            uom_precision = self.env['decimal.precision'].precision_get(
                'Product Unit of Measure')
            if uom_precision < 2:
                uom_precision = 2
            sum_subtotal = {}
            for line in invoice.invoice_line_ids:
                if line.is_details:
                    self.setDettaglioLineaMerge(
                        line_no, line, body, price_precision, uom_precision
                    )
                    if not sum_subtotal.get(
                        line.invoice_line_tax_ids[0].id, False):
                            sum_subtotal.update(
                                {line.invoice_line_tax_ids[0].id: 0.0})
                    sum_subtotal[
                        line.invoice_line_tax_ids[0].id] += line.price_subtotal
                    line_no += 1
                else:
                    self.setDettaglioLinea(
                        line_no, line, body, price_precision, uom_precision)
                    line_no += 1            
            for line_tax in invoice.tax_line_ids:
                sum_subt = 0.0
                if sum_subtotal.get(line_tax.tax_id.id, False):
                    sum_subt = sum_subtotal[line_tax.tax_id.id]
                self.setDettaglioLineaSummary(
                        line_no, line_tax, body, 
                        price_precision, sum_subt)
                line_no += 1
            
    def setDettaglioLineaSummary(
            self, line_no, line, body, price_precision, sum_subt=0.0):
        aliquota = line.tax_id.amount
        AliquotaIVA = '%.2f' % float_round(aliquota, 2)
        line.ftpa_line_number = line_no
        prezzo_unitario = sum_subt
        prezzo_tot = sum_subt
        DettaglioLinea = DettaglioLineeType(
            NumeroLinea=str(line_no),
            Descrizione=encode_for_export('VALORE COMPLESSIVO DETTAGLI', 1000),
            PrezzoUnitario='{prezzo:.{precision}f}'.format(
                prezzo=prezzo_unitario, precision=price_precision),
            Quantita='{qta:.{precision}f}'.format(
                qta=1.0, precision=2),
            UnitaMisura=None,
            PrezzoTotale='%.2f' % float_round(prezzo_tot, 2),
            AliquotaIVA=AliquotaIVA)
        if aliquota == 0.0:
            if not line.tax_id.kind_id:
                raise UserError(
                    _("No 'nature' field for tax %s.") %
                    line.tax_id.name)
            DettaglioLinea.Natura = line.tax_id.kind_id.code
            if line.tax_id.kind_id.code == 'N2.1' and \
                    line.invoice_id.partner_id.country_id.code in [
                'AT', 'BE', 'BG', 'CY', 'HR', 'DK', 'EE', 'FI', 'FR', 'DE', 'GR', 'IE',
                'IT', 'LV', 'LT', 'LU', 'MT', 'NL', 'PL', 'PT', 'CZ', 'RO', 'SK', 'SI',
                'ES', 'SE', 'HU'
            ]:
                dati_gestionali = AltriDatiGestionaliType()
                dati_gestionali.TipoDato = 'INVCONT'
                DettaglioLinea.AltriDatiGestionali.append(
                    dati_gestionali
                )
        body.DatiBeniServizi.DettaglioLinee.append(DettaglioLinea)
        return DettaglioLinea

    def setDettaglioLineaMerge(
            self, line_no, line, body, price_precision, uom_precision):
        if not line.invoice_line_tax_ids:
                raise UserError(
                    ("Invoice line %s does not have tax.") % line.name)
        if len(line.invoice_line_tax_ids) > 1:
            raise UserError(
                ("Too many taxes for invoice line %s.") % line.name)
        aliquota = line.invoice_line_tax_ids[0].amount
        AliquotaIVA = '%.2f' % float_round(aliquota, 2)
        line.ftpa_line_number = line_no
        prezzo_unitario = 0.0
        DettaglioLinea = DettaglioLineeType(
            NumeroLinea=str(line_no),
            Descrizione=encode_for_export(line.name, 1000),
            PrezzoUnitario='{prezzo:.{precision}f}'.format(
                prezzo=prezzo_unitario, precision=price_precision),
            Quantita='{qta:.{precision}f}'.format(
                qta=line.quantity, precision=uom_precision),
            UnitaMisura=line.uom_id and (
                unidecode(line.uom_id.name)) or None,
            PrezzoTotale='%.2f' % float_round(0.0, 2),
            AliquotaIVA=AliquotaIVA)
        DettaglioLinea.ScontoMaggiorazione.extend(
            self.setScontoMaggiorazione(line))
        if aliquota == 0.0:
            if not line.invoice_line_tax_ids[0].kind_id:
                raise UserError(
                    _("No 'nature' field for tax %s.") %
                    line.invoice_line_tax_ids[0].name)
            DettaglioLinea.Natura = line.invoice_line_tax_ids[
                0
            ].kind_id.code
            if line.invoice_line_tax_ids[0].kind_id.code == 'N2.1' and \
                    line.invoice_id.partner_id.country_id.code in [
                'AT', 'BE', 'BG', 'CY', 'HR', 'DK', 'EE', 'FI', 'FR', 'DE', 'GR', 'IE',
                'IT', 'LV', 'LT', 'LU', 'MT', 'NL', 'PL', 'PT', 'CZ', 'RO', 'SK', 'SI',
                'ES', 'SE', 'HU'
            ]:
                dati_gestionali = AltriDatiGestionaliType()
                dati_gestionali.TipoDato = 'INVCONT'
                DettaglioLinea.AltriDatiGestionali.append(
                    dati_gestionali
                )
        if line.admin_ref:
            DettaglioLinea.RiferimentoAmministrazione = line.admin_ref
        if line.product_id:
            product_code = line.product_id.default_code
            if product_code:
                CodiceArticolo = CodiceArticoloType(
                    CodiceTipo=self.env['ir.config_parameter'].sudo(
                    ).get_param('fatturapa.codicetipo.odoo', 'ODOO'),
                    CodiceValore=product_code[:35],
                )
                DettaglioLinea.CodiceArticolo.append(CodiceArticolo)
            product_barcode = line.product_id.barcode
            if product_barcode:
                CodiceArticolo = CodiceArticoloType(
                    CodiceTipo='EAN',
                    CodiceValore=product_barcode[:35],
                )
                DettaglioLinea.CodiceArticolo.append(CodiceArticolo)
        body.DatiBeniServizi.DettaglioLinee.append(DettaglioLinea)
        return DettaglioLinea
