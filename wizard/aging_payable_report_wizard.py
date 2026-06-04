from collections import OrderedDict
from datetime import datetime, time

from odoo import models, fields, _


class AgingPayableReportWizard(models.TransientModel):
    _name = 'lms.aging.payable.report.wizard'
    _description = 'Balance por Antigüedad (Proveedores)'

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

        vendor_groups = OrderedDict()
        totals = {
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

            if vendor_key not in vendor_groups:
                vendor_groups[vendor_key] = {
                    'vendor_name': vendor_name,
                    'partner_id': partner.id if partner else False,
                    'lines': [],
                    'subtotal': {
                        'balance_pending': 0.0,
                        'not_due': 0.0,
                        'bucket_1_30': 0.0,
                        'bucket_31_60': 0.0,
                        'bucket_61_90': 0.0,
                        'bucket_90_plus': 0.0,
                    }
                }

            balance_pending = move.amount_residual or 0.0
            days_overdue = self._get_days_overdue(move)
            buckets = self._get_bucket_values(balance_pending, days_overdue)

            line_vals = {
                'vendor_name': vendor_name,
                'partner_id': partner.id if partner else False,
                'invoice_id': move.id,
                'invoice_name': move.name or move.ref or '/',
                'invoice_date': move.invoice_date,
                'due_date': move.invoice_date_due,
                'balance_pending': balance_pending,
                'days_overdue': days_overdue,
                'not_due': buckets['not_due'],
                'bucket_1_30': buckets['bucket_1_30'],
                'bucket_31_60': buckets['bucket_31_60'],
                'bucket_61_90': buckets['bucket_61_90'],
                'bucket_90_plus': buckets['bucket_90_plus'],
            }

            vendor_groups[vendor_key]['lines'].append(line_vals)

            for key in vendor_groups[vendor_key]['subtotal']:
                vendor_groups[vendor_key]['subtotal'][key] += line_vals.get(key, 0.0)
                totals[key] += line_vals.get(key, 0.0)

        return {
            'vendor_groups': list(vendor_groups.values()),
            'totals': totals,
            'date_to': self.date_to,
        }

    def action_view_screen(self):
        Line = self.env['lms.aging.payable.report.line']
        Line.search([('wizard_id', '=', self.id)]).unlink()

        data = self._get_report_data()
        sequence = 1

        for group in data['vendor_groups']:
            Line.create({
                'wizard_id': self.id,
                'sequence': sequence,
                'is_group': True,
                'is_subtotal': False,
                'group_name': group['vendor_name'],
                'vendor_name': group['vendor_name'],
            })
            sequence += 1

            for detail in group['lines']:
                vals = dict(detail)
                vals.update({
                    'wizard_id': self.id,
                    'sequence': sequence,
                    'is_group': False,
                    'is_subtotal': False,
                })
                Line.create(vals)
                sequence += 1

            Line.create({
                'wizard_id': self.id,
                'sequence': sequence,
                'is_group': False,
                'is_subtotal': True,
                'subtotal_label': 'SUBTOTAL %s' % group['vendor_name'],
                'vendor_name': group['vendor_name'],
                'balance_pending': group['subtotal']['balance_pending'],
                'not_due': group['subtotal']['not_due'],
                'bucket_1_30': group['subtotal']['bucket_1_30'],
                'bucket_31_60': group['subtotal']['bucket_31_60'],
                'bucket_61_90': group['subtotal']['bucket_61_90'],
                'bucket_90_plus': group['subtotal']['bucket_90_plus'],
            })
            sequence += 1

        Line.create({
            'wizard_id': self.id,
            'sequence': sequence,
            'is_group': False,
            'is_subtotal': True,
            'subtotal_label': 'TOTAL GENERAL',
            'balance_pending': data['totals']['balance_pending'],
            'not_due': data['totals']['not_due'],
            'bucket_1_30': data['totals']['bucket_1_30'],
            'bucket_31_60': data['totals']['bucket_31_60'],
            'bucket_61_90': data['totals']['bucket_61_90'],
            'bucket_90_plus': data['totals']['bucket_90_plus'],
        })

        return {
            'type': 'ir.actions.act_window',
            'name': _('Balance por Antigüedad (Proveedores)'),
            'res_model': 'lms.aging.payable.report.line',
            'view_mode': 'list',
            'views': [
                (self.env.ref('lms_financial_reports.view_aging_payable_report_line_list').id, 'list')
            ],
            'domain': [('wizard_id', '=', self.id)],
            'target': 'current',
        }

    def action_print_pdf(self):
        return self.env.ref(
            'lms_financial_reports.action_aging_payable_report_pdf'
        ).report_action(self)

    def action_export_xlsx(self):
        return self.env.ref(
            'lms_financial_reports.action_aging_payable_report_xlsx'
        ).report_action(self)