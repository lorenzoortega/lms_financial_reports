from collections import OrderedDict
from datetime import datetime, time

import pytz

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PosDailyReportWizard(models.TransientModel):
    _name = 'lms.pos.daily.report.wizard'
    _description = 'Reporte Ventas POS Día'

    date = fields.Date(string="Fecha", required=True)
    pos_config_id = fields.Many2one('pos.config', string="Punto de Venta")

    @api.constrains('date')
    def _check_date(self):
        for rec in self:
            if not rec.date:
                raise ValidationError(_("Debe seleccionar una fecha."))

    def _get_local_day_utc_range(self):
        """Convierte el día local seleccionado por el usuario a rango UTC."""
        self.ensure_one()

        user_tz_name = self.env.user.tz or self._context.get('tz') or 'UTC'
        user_tz = pytz.timezone(user_tz_name)

        local_start = user_tz.localize(datetime.combine(self.date, time.min))
        local_end = user_tz.localize(datetime.combine(self.date, time.max))

        utc_start = local_start.astimezone(pytz.UTC).replace(tzinfo=None)
        utc_end = local_end.astimezone(pytz.UTC).replace(tzinfo=None)

        return utc_start, utc_end

    def _format_session_range(self, session):
        def _to_local_str(dt_value):
            if not dt_value:
                return ''
            local_dt = fields.Datetime.context_timestamp(self, dt_value)
            return local_dt.strftime('%Y-%m-%d %I:%M:%S %p')

        start_txt = _to_local_str(session.start_at)
        stop_txt = _to_local_str(session.stop_at)

        if start_txt and stop_txt:
            return f"{start_txt} - {stop_txt}"
        return start_txt or stop_txt or ''

    def _classify_payments(self, orders):
        cash_amount = 0.0
        card_amount = 0.0
        transfer_amount = 0.0

        payments = orders.mapped('payment_ids')

        for payment in payments:
            method = payment.payment_method_id
            method_name = (method.name or '').strip().lower()
            amount = payment.amount or 0.0

            # Los pagos COD / Contra Entrega no se cuentan aquí.
            # Se reportan como Liquidación Chofer cuando el chofer entrega
            # el dinero en una sesión POS.
            if getattr(method, 'is_cod_delivery', False):
                continue

            if 'efectivo' in method_name or 'cash' in method_name:
                cash_amount += amount
            elif 'tarjeta' in method_name or 'card' in method_name:
                card_amount += amount
            elif 'transfer' in method_name or 'transferencia' in method_name:
                transfer_amount += amount
            else:
                transfer_amount += amount

        return cash_amount, card_amount, transfer_amount

    def _get_session_tax_amount(self, orders):
        amount_tax = 0.0
        for order in orders:
            if order.account_move:
                amount_tax += order.account_move.amount_tax or 0.0
            else:
                amount_tax += order.amount_tax or 0.0
        return amount_tax

    def _get_driver_liquidation_amounts_by_session(self, sessions):
        result = {session.id: 0.0 for session in sessions}

        if not sessions:
            return result

        if 'lms.phone.order' not in self.env.registry.models:
            return result

        PhoneOrder = self.env['lms.phone.order']

        domain = [
            ('delivery_liquidation_pos_session_id', 'in', sessions.ids),
            ('delivery_cash_state', 'in', ['settled', 'difference']),
        ]

        phone_orders = PhoneOrder.search(domain)

        for order in phone_orders:
            session = order.delivery_liquidation_pos_session_id
            if session:
                result[session.id] = result.get(session.id, 0.0) + (order.driver_cash_received or 0.0)

        return result

    def _get_report_data(self):
        self.ensure_one()

        Session = self.env['pos.session']
        utc_start, utc_end = self._get_local_day_utc_range()

        domain = [
            ('start_at', '>=', fields.Datetime.to_string(utc_start)),
            ('start_at', '<=', fields.Datetime.to_string(utc_end)),
        ]

        if self.pos_config_id:
            domain.append(('config_id', '=', self.pos_config_id.id))

        sessions = Session.search(domain, order='config_id asc, start_at asc, name asc')
        driver_liquidation_by_session = self._get_driver_liquidation_amounts_by_session(sessions)

        pos_groups = OrderedDict()

        totals = {
            'cash_amount': 0.0,
            'cash_real': 0.0,
            'cash_diff': 0.0,
            'card_amount': 0.0,
            'transfer_amount': 0.0,
            'tax_amount': 0.0,
            'total_amount': 0.0,
        }

        for session in sessions:
            session_orders = session.order_ids.filtered(lambda o: o.state in ['paid', 'done', 'invoiced'])
            driver_liquidation_amount = driver_liquidation_by_session.get(session.id, 0.0)

            if not session_orders and not driver_liquidation_amount:
                continue

            pos = session.config_id
            pos_key = pos.id if pos else 0
            pos_name = pos.display_name if pos else _('Sin Punto de Venta')

            if pos_key not in pos_groups:
                pos_groups[pos_key] = {
                    'pos': pos,
                    'pos_name': pos_name,
                    'sessions': [],
                    'subtotal': {
                        'cash_amount': 0.0,
                        'cash_real': 0.0,
                        'cash_diff': 0.0,
                        'card_amount': 0.0,
                        'transfer_amount': 0.0,
                        'tax_amount': 0.0,
                        'total_amount': 0.0,
                    }
                }

            order_count = len(session_orders)
            cash_amount, card_amount, transfer_amount = self._classify_payments(session_orders)
            tax_amount = self._get_session_tax_amount(session_orders)

            # Reutilizamos campos técnicos existentes para no romper vistas/Excel:
            # cash_diff = Liquidación Chofer
            # cash_real = Total Efectivo Cobrado
            cash_diff = driver_liquidation_amount
            cash_real = cash_amount + driver_liquidation_amount

            total_amount = cash_amount + driver_liquidation_amount + card_amount + transfer_amount

            local_start = fields.Datetime.context_timestamp(self, session.start_at) if session.start_at else False

            session_vals = {
                'date': local_start.date() if local_start else self.date,
                'session_range': self._format_session_range(session),
                'session_name': session.name or '',
                'session_state': session.state or '',
                'cashier_name': session.user_id.display_name or '',
                'order_count': order_count,
                'cash_amount': cash_amount,
                'cash_real': cash_real,
                'cash_diff': cash_diff,
                'card_amount': card_amount,
                'transfer_amount': transfer_amount,
                'tax_amount': tax_amount,
                'total_amount': total_amount,
                'session_id': session.id,
                'pos_config_id': pos.id if pos else False,
                'cashier_id': session.user_id.id if session.user_id else False,
                'pos_name': pos_name,
            }
            pos_groups[pos_key]['sessions'].append(session_vals)

            for key in ['cash_amount', 'cash_real', 'cash_diff', 'card_amount', 'transfer_amount', 'tax_amount', 'total_amount']:
                pos_groups[pos_key]['subtotal'][key] += session_vals[key]
                totals[key] += session_vals[key]

        return {
            'pos_groups': list(pos_groups.values()),
            'totals': totals,
        }

    def action_view_screen(self):
        self.ensure_one()

        Line = self.env['lms.pos.daily.report.line']
        Line.search([('wizard_id', '=', self.id)]).unlink()

        data = self._get_report_data()

        sequence = 1
        for group in data['pos_groups']:
            Line.create({
                'wizard_id': self.id,
                'sequence': sequence,
                'is_group': True,
                'group_name': group['pos_name'],
                'pos_name': group['pos_name'],
            })
            sequence += 1

            for session_line in group['sessions']:
                vals = dict(session_line)
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
                'subtotal_label': 'SUBTOTAL %s' % group['pos_name'],
                'pos_name': group['pos_name'],
                'cash_amount': group['subtotal']['cash_amount'],
                'cash_real': group['subtotal']['cash_real'],
                'cash_diff': group['subtotal']['cash_diff'],
                'card_amount': group['subtotal']['card_amount'],
                'transfer_amount': group['subtotal']['transfer_amount'],
                'tax_amount': group['subtotal']['tax_amount'],
                'total_amount': group['subtotal']['total_amount'],
            })
            sequence += 1

        Line.create({
            'wizard_id': self.id,
            'sequence': sequence,
            'is_group': False,
            'is_subtotal': True,
            'subtotal_label': 'TOTAL VENTAS POS DIA',
            'cash_amount': data['totals']['cash_amount'],
            'cash_real': data['totals']['cash_real'],
            'cash_diff': data['totals']['cash_diff'],
            'card_amount': data['totals']['card_amount'],
            'transfer_amount': data['totals']['transfer_amount'],
            'tax_amount': data['totals']['tax_amount'],
            'total_amount': data['totals']['total_amount'],
        })

        return {
            'type': 'ir.actions.act_window',
            'name': _('Reporte Ventas POS Día'),
            'res_model': 'lms.pos.daily.report.line',
            'view_mode': 'list',
            'views': [
                (self.env.ref('lms_financial_reports.view_pos_daily_report_line_list').id, 'list')
            ],
            'domain': [('wizard_id', '=', self.id)],
            'target': 'current',
        }

    def action_export_xlsx(self):
        self.ensure_one()
        return self.env.ref(
            'lms_financial_reports.action_pos_daily_report_xlsx'
        ).report_action(self)
