from collections import OrderedDict
from datetime import datetime, time

from odoo import models, fields, _


class AgingPayableSummaryWizard(models.TransientModel):
    _name = 'lms.aging.payable.summary.wizard'
    _description = 'Balance por Antigüedad Resumido (Proveedores)'

    date_to = fields.Date(string="Fecha de corte", required=True)

    def _get_days_overdue(self, move):
        cutoff_date = self.date_to
        due_date = move.invoice_date_due or move.invoice_date

        if not due_date:
            return 0

        days = (cutoff_date - due_date).days
        return days if days > 0 else 0

    def _get_bucket_values(self, amount, days_overdue):
        return {
            'not_due': amount if days_overdue <= 0 else 0.0,
            'bucket_1_30': amount if 1 <= days_overdue <= 30 else 0.0,
            'bucket_31_60': amount if 31 <= days_overdue <= 60 else 0.0,
            'bucket_61_90': amount if 61 <= days_overdue <= 90 else 0.0,
            'bucket_90_plus': amount if days_overdue > 90 else 0.0,
        }

    def _get_moves_domain(self):
        date_to_end = datetime.combine(self.date_to, time.max)

        return [
            ('move_type', '=', 'in_invoice'),
            ('state', '=', 'posted'),
            ('amount_residual', '>', 0),
            ('invoice_date', '!=', False),
            ('invoice_date', '<=', self.date_to),
            ('date', '<=', fields.Datetime.to_string(date_to_end)),
        ]

    def _get_report_data(self):
        Move = self.env['account.move']
        moves = Move.search(
            self._get_moves_domain(),
            order='partner_id asc, invoice_date asc, name asc'
        )

        vendor_totals = OrderedDict()
        grand_total = {
            'balance_pending': 0.0,
            'not_due': 0.0,
            'bucket_1_30': 0.0,
            'bucket_31_60': 0.0,
            'bucket_61_90': 0.0,
            'bucket_90_plus': 0.0,
        }

        for move in moves:
            partner = move.partner_id
            vendor_key = partner.id or 0
            vendor_name = partner.display_name or _('Proveedor sin nombre')
            balance_pending = move.amount_residual or 0.0
            days_overdue = self._get_days_overdue(move)
            buckets = self._get_bucket_values(balance_pending, days_overdue)

            if vendor_key not in vendor_totals:
                vendor_totals[vendor_key] = {
                    'partner_id': partner.id if partner else False,
                    'vendor_name': vendor_name,
                    'balance_pending': 0.0,
                    'not_due': 0.0,
                    'bucket_1_30': 0.0,
                    'bucket_31_60': 0.0,
                    'bucket_61_90': 0.0,
                    'bucket_90_plus': 0.0,
                }

            vendor_totals[vendor_key]['balance_pending'] += balance_pending
            vendor_totals[vendor_key]['not_due'] += buckets['not_due']
            vendor_totals[vendor_key]['bucket_1_30'] += buckets['bucket_1_30']
            vendor_totals[vendor_key]['bucket_31_60'] += buckets['bucket_31_60']
            vendor_totals[vendor_key]['bucket_61_90'] += buckets['bucket_61_90']
            vendor_totals[vendor_key]['bucket_90_plus'] += buckets['bucket_90_plus']

            grand_total['balance_pending'] += balance_pending
            grand_total['not_due'] += buckets['not_due']
            grand_total['bucket_1_30'] += buckets['bucket_1_30']
            grand_total['bucket_31_60'] += buckets['bucket_31_60']
            grand_total['bucket_61_90'] += buckets['bucket_61_90']
            grand_total['bucket_90_plus'] += buckets['bucket_90_plus']

        return {
            'lines': list(vendor_totals.values()),
            'totals': grand_total,
            'date_to': self.date_to,
        }

    def action_view_screen(self):
        Line = self.env['lms.aging.payable.summary.line']
        Line.search([('wizard_id', '=', self.id)]).unlink()

        data = self._get_report_data()
        sequence = 1

        for line in data['lines']:
            vals = dict(line)
            vals.update({
                'wizard_id': self.id,
                'sequence': sequence,
                'is_total': False,
                'total_label': False,
            })
            Line.create(vals)
            sequence += 1

        Line.create({
            'wizard_id': self.id,
            'sequence': sequence,
            'is_total': True,
            'total_label': 'TOTAL GENERAL',
            'balance_pending': data['totals']['balance_pending'],
            'not_due': data['totals']['not_due'],
            'bucket_1_30': data['totals']['bucket_1_30'],
            'bucket_31_60': data['totals']['bucket_31_60'],
            'bucket_61_90': data['totals']['bucket_61_90'],
            'bucket_90_plus': data['totals']['bucket_90_plus'],
        })

        return {
            'type': 'ir.actions.act_window',
            'name': _('Balance por Antigüedad Resumido (Proveedores)'),
            'res_model': 'lms.aging.payable.summary.line',
            'view_mode': 'list',
            'views': [
                (self.env.ref('lms_financial_reports.view_aging_payable_summary_line_list').id, 'list')
            ],
            'domain': [('wizard_id', '=', self.id)],
            'target': 'current',
        }

    def action_print_pdf(self):
        return self.env.ref(
            'lms_financial_reports.action_aging_payable_summary_pdf'
        ).report_action(self)

    def action_export_xlsx(self):
        return self.env.ref(
            'lms_financial_reports.action_aging_payable_summary_xlsx'
        ).report_action(self)