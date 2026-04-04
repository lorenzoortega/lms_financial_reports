from collections import OrderedDict
from datetime import datetime, time

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PosReportWizard(models.TransientModel):
    _name = 'lms.pos.report.wizard'
    _description = 'Reporte por POS'

    date_from = fields.Date(string="Fecha Inicio", required=True)
    date_to = fields.Date(string="Fecha Fin", required=True)
    pos_config_id = fields.Many2one('pos.config', string="Punto de Venta")

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for rec in self:
            if not rec.date_from or not rec.date_to:
                raise ValidationError(_("Debe seleccionar Fecha Inicio y Fecha Fin."))
            if rec.date_from > rec.date_to:
                raise ValidationError(_("La Fecha Inicio no puede ser mayor que la Fecha Fin."))
            if (rec.date_to.year - rec.date_from.year) > 5:
                raise ValidationError(_("No se permite generar reportes mayores a 5 años."))

    def _get_orders_domain(self):
        self.ensure_one()

        date_start = datetime.combine(self.date_from, time.min)
        date_end = datetime.combine(self.date_to, time.max)

        domain = [
            ('date_order', '>=', fields.Datetime.to_string(date_start)),
            ('date_order', '<=', fields.Datetime.to_string(date_end)),
            ('state', 'in', ['paid', 'done', 'invoiced']),
        ]
        return domain

    def _format_session_header(self, session):
        start_txt = fields.Datetime.to_string(session.start_at) if session.start_at else ''
        stop_txt = fields.Datetime.to_string(session.stop_at) if session.stop_at else ''
        state_label = {
            'opening_control': 'ABIERTA',
            'opened': 'ABIERTA',
            'closing_control': 'EN CIERRE',
            'closed': 'CERRADA',
        }.get(session.state or '', (session.state or '').upper())

        if stop_txt and state_label == 'CERRADA':
            return f"SESSION #{session.name} / {state_label} / {start_txt} - {stop_txt}"
        if start_txt:
            return f"SESSION #{session.name} / {state_label} / {start_txt}"
        return f"SESSION #{session.name} / {state_label}"

    def _get_pos_report_data(self):
        self.ensure_one()

        Order = self.env['pos.order']
        orders = Order.search(self._get_orders_domain(), order='session_id asc, date_order asc, name asc')

        if self.pos_config_id:
            orders = orders.filtered(lambda o: o.session_id and o.session_id.config_id == self.pos_config_id)

        session_groups = OrderedDict()

        for order in orders:
            session = order.session_id
            if not session:
                continue

            key = session.id
            if key not in session_groups:
                session_groups[key] = {
                    'session': session,
                    'header': self._format_session_header(session),
                    'state': session.state,
                    'start_at': session.start_at,
                    'stop_at': session.stop_at,
                    'pos_name': session.config_id.display_name if session.config_id else '',
                    'lines': [],
                    'total_amount': 0.0,
                }

            payments = order.payment_ids.sorted(lambda p: (p.payment_date or order.date_order, p.id))
            if not payments:
                session_groups[key]['lines'].append({
                    'date': order.date_order,
                    'pos_name': session.config_id.display_name if session.config_id else '',
                    'session_name': session.name or '',
                    'session_state': session.state or '',
                    'cashier_name': order.user_id.display_name or '',
                    'order_name': order.name or '',
                    'invoice_name': order.account_move.name if order.account_move else '',
                    'ncf_number': getattr(order.account_move, 'ncf_number', '') if order.account_move else '',
                    'customer_name': order.partner_id.display_name or '',
                    'payment_method_name': '',
                    'amount': order.amount_total,
                    'session_id': session.id,
                    'order_id': order.id,
                    'invoice_id': order.account_move.id if order.account_move else False,
                })
                session_groups[key]['total_amount'] += order.amount_total
                continue

            for payment in payments:
                amount = payment.amount or 0.0
                session_groups[key]['lines'].append({
                    'date': payment.payment_date or order.date_order,
                    'pos_name': session.config_id.display_name if session.config_id else '',
                    'session_name': session.name or '',
                    'session_state': session.state or '',
                    'cashier_name': order.user_id.display_name or '',
                    'order_name': order.name or '',
                    'invoice_name': order.account_move.name if order.account_move else '',
                    'ncf_number': getattr(order.account_move, 'ncf_number', '') if order.account_move else '',
                    'customer_name': order.partner_id.display_name or '',
                    'payment_method_name': payment.payment_method_id.name or '',
                    'amount': amount,
                    'session_id': session.id,
                    'order_id': order.id,
                    'invoice_id': order.account_move.id if order.account_move else False,
                })
                session_groups[key]['total_amount'] += amount

        return list(session_groups.values())

    def action_view_screen(self):
        self.ensure_one()

        Line = self.env['lms.pos.report.line']
        Line.search([('wizard_id', '=', self.id)]).unlink()

        session_groups = self._get_pos_report_data()

        sequence = 1
        for group in session_groups:
            Line.create({
                'wizard_id': self.id,
                'sequence': sequence,
                'is_group': True,
                'group_name': group['header'],
                'session_name': group['session'].name or '',
                'session_state': group['session'].state or '',
                'pos_name': group['pos_name'],
                'session_id': group['session'].id,
                'amount': 0.0,
            })
            sequence += 1

            for line in group['lines']:
                vals = dict(line)
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
                'session_name': group['session'].name or '',
                'session_state': group['session'].state or '',
                'pos_name': group['pos_name'],
                'session_id': group['session'].id,
                'amount': group['total_amount'],
            })
            sequence += 1

        return {
            'type': 'ir.actions.act_window',
            'name': _('Reporte por POS'),
            'res_model': 'lms.pos.report.line',
            'view_mode': 'list',
            'views': [
                (self.env.ref('lms_financial_reports.view_pos_report_line_list').id, 'list')
            ],
            'domain': [('wizard_id', '=', self.id)],
            'target': 'current',
        }

    def action_print_pdf(self):
        self.ensure_one()
        return self.env.ref(
            'lms_financial_reports.action_pos_report_pdf'
        ).report_action(self)

    def action_export_xlsx(self):
        self.ensure_one()
        return self.env.ref(
            'lms_financial_reports.action_pos_report_xlsx'
        ).report_action(self)
