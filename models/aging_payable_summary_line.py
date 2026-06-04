from odoo import models, fields


class AgingPayableSummaryLine(models.TransientModel):
    _name = 'lms.aging.payable.summary.line'
    _description = 'Balance Antigüedad Proveedores - Resumen'
    _order = 'sequence asc'

    wizard_id = fields.Many2one('lms.aging.payable.summary.wizard', ondelete='cascade')

    sequence = fields.Integer()

    is_total = fields.Boolean()
    total_label = fields.Char()

    vendor_name = fields.Char(string="Proveedor")
    partner_id = fields.Many2one('res.partner')

    balance_pending = fields.Float(string="Balance Pendiente")

    not_due = fields.Float(string="No Vencida")
    bucket_1_30 = fields.Float(string="1-30")
    bucket_31_60 = fields.Float(string="31-60")
    bucket_61_90 = fields.Float(string="61-90")
    bucket_90_plus = fields.Float(string="90+")

    def action_view_invoices(self):
        self.ensure_one()

        if self.is_total or not self.partner_id or not self.wizard_id:
            return False

        return {
            'type': 'ir.actions.act_window',
            'name': 'Facturas Proveedor',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'views': [
                (self.env.ref('lms_financial_reports.view_account_move_payable_drilldown_list').id, 'list'),
                (False, 'form'),
            ],
            'domain': [
                ('move_type', '=', 'in_invoice'),
                ('state', '=', 'posted'),
                ('amount_residual', '>', 0),
                ('partner_id', '=', self.partner_id.id),
                ('invoice_date', '!=', False),
                ('invoice_date', '<=', self.wizard_id.date_to),
            ],
            'context': {
                'create': False,
            },
            'target': 'current',
        }