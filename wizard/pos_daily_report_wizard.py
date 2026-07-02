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

    def _classify_payment_method(self, method):
        method_name = (method.name or '').strip().lower()

        if getattr(method, 'is_cod_delivery', False):
            return 'cod'
        if getattr(method, 'is_cash_count', False):
            return 'cash'
        if 'efectivo' in method_name or 'cash' in method_name:
            return 'cash'
        if 'tarjeta' in method_name or 'card' in method_name:
            return 'card'
        if 'transfer' in method_name or 'transf' in method_name or 'transferencia' in method_name:
            return 'transfer'
        return 'other'

    def _classify_payments(self, orders):
        cash_amount = 0.0
        card_amount = 0.0
        transfer_amount = 0.0
        other_amount = 0.0

        payments = orders.mapped('payment_ids')

        for payment in payments:
            method_type = self._classify_payment_method(payment.payment_method_id)
            amount = payment.amount or 0.0

            # Los pagos COD / Contra Entrega no se cuentan aquí.
            # Se reportan como Liquidación Chofer cuando el chofer entrega
            # el dinero en una sesión POS.
            if method_type == 'cod':
                continue
            if method_type == 'cash':
                cash_amount += amount
            elif method_type == 'card':
                card_amount += amount
            elif method_type == 'transfer':
                transfer_amount += amount
            else:
                other_amount += amount

        return cash_amount, card_amount, transfer_amount, other_amount

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

    def _get_cxc_receipt_amounts_by_session(self, sessions):
        result = {
            session.id: {
                'cxc_receipt_count': 0,
                'cxc_cash_amount': 0.0,
                'cxc_card_amount': 0.0,
                'cxc_transfer_amount': 0.0,
                'cxc_other_amount': 0.0,
                'cxc_total_amount': 0.0,
            }
            for session in sessions
        }

        if not sessions:
            return result

        if 'lms.pos.cxc.receipt' not in self.env.registry.models:
            return result

        Receipt = self.env['lms.pos.cxc.receipt']
        receipts = Receipt.search([
            ('pos_session_id', 'in', sessions.ids),
            ('state', '=', 'posted'),
        ])

        for receipt in receipts:
            session = receipt.pos_session_id
            if not session:
                continue

            vals = result.setdefault(session.id, {
                'cxc_receipt_count': 0,
                'cxc_cash_amount': 0.0,
                'cxc_card_amount': 0.0,
                'cxc_transfer_amount': 0.0,
                'cxc_other_amount': 0.0,
                'cxc_total_amount': 0.0,
            })

            amount = receipt.amount or 0.0
            method_type = self._classify_payment_method(receipt.payment_method_id)

            if method_type == 'cash':
                vals['cxc_cash_amount'] += amount
            elif method_type == 'card':
                vals['cxc_card_amount'] += amount
            elif method_type == 'transfer':
                vals['cxc_transfer_amount'] += amount
            else:
                vals['cxc_other_amount'] += amount

            vals['cxc_total_amount'] += amount
            vals['cxc_receipt_count'] += 1

        return result

    def _get_session_cash_counted(self, session):
        """
        Efectivo contado físicamente al cierre.

        En Odoo POS normalmente el efectivo contado al cierre queda en
        cash_register_balance_end_real. Si la sesión está abierta, no se
        considera diferencia todavía para no mostrar faltantes falsos.
        """
        if session.state != 'closed':
            return 0.0, False

        if 'cash_register_balance_end_real' in session._fields:
            return session.cash_register_balance_end_real or 0.0, True

        return 0.0, False

    def _empty_totals(self):
        return {
            'order_count': 0,
            'cxc_receipt_count': 0,
            'cash_amount': 0.0,
            'driver_liquidation_amount': 0.0,
            'cxc_cash_amount': 0.0,
            'total_cash_collected': 0.0,
            'cash_counted': 0.0,
            'cash_difference': 0.0,
            'card_amount': 0.0,
            'cxc_card_amount': 0.0,
            'total_card_collected': 0.0,
            'transfer_amount': 0.0,
            'cxc_transfer_amount': 0.0,
            'total_transfer_collected': 0.0,
            'other_amount': 0.0,
            'cxc_other_amount': 0.0,
            'total_other_collected': 0.0,
            'cxc_total_amount': 0.0,
            'total_sales': 0.0,
        }

    def _accumulate_totals(self, target, source):
        for key in target.keys():
            target[key] += source.get(key, 0.0) or 0.0

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
        cxc_by_session = self._get_cxc_receipt_amounts_by_session(sessions)

        pos_groups = OrderedDict()
        totals = self._empty_totals()

        for session in sessions:
            session_orders = session.order_ids.filtered(lambda o: o.state in ['paid', 'done', 'invoiced'])
            driver_liquidation_amount = driver_liquidation_by_session.get(session.id, 0.0)
            cxc_vals = cxc_by_session.get(session.id, {})
            cxc_total_amount = cxc_vals.get('cxc_total_amount', 0.0)

            if not session_orders and not driver_liquidation_amount and not cxc_total_amount:
                continue

            pos = session.config_id
            pos_key = pos.id if pos else 0
            pos_name = pos.display_name if pos else _('Sin Punto de Venta')

            if pos_key not in pos_groups:
                pos_groups[pos_key] = {
                    'pos': pos,
                    'pos_name': pos_name,
                    'sessions': [],
                    'subtotal': self._empty_totals(),
                }

            order_count = len(session_orders)
            cash_amount, card_amount, transfer_amount, other_amount = self._classify_payments(session_orders)

            cxc_cash_amount = cxc_vals.get('cxc_cash_amount', 0.0)
            cxc_card_amount = cxc_vals.get('cxc_card_amount', 0.0)
            cxc_transfer_amount = cxc_vals.get('cxc_transfer_amount', 0.0)
            cxc_other_amount = cxc_vals.get('cxc_other_amount', 0.0)
            cxc_receipt_count = cxc_vals.get('cxc_receipt_count', 0)

            # La liquidación de chofer ya entra como pago real de efectivo dentro de
            # los pagos POS cuando se registra con el método Efectivo POSxx. Por eso
            # no se suma nuevamente; queda solo como desglose informativo.
            total_cash_collected = cash_amount + cxc_cash_amount
            total_card_collected = card_amount + cxc_card_amount
            total_transfer_collected = transfer_amount + cxc_transfer_amount
            total_other_collected = other_amount + cxc_other_amount

            cash_counted, has_cash_counted = self._get_session_cash_counted(session)
            cash_difference = cash_counted - total_cash_collected if has_cash_counted else 0.0

            # Total Efectivo y Equivalentes representa lo recibido por caja:
            # ventas POS + Recibos CxC Clientes, separado por método de cobro.
            total_sales = (
                total_cash_collected
                + total_card_collected
                + total_transfer_collected
                + total_other_collected
            )

            local_start = fields.Datetime.context_timestamp(self, session.start_at) if session.start_at else False

            session_vals = {
                'date': local_start.date() if local_start else self.date,
                'session_range': self._format_session_range(session),
                'session_name': session.name or '',
                'session_state': session.state or '',
                'cashier_name': session.user_id.display_name or '',
                'order_count': order_count,
                'cxc_receipt_count': cxc_receipt_count,
                'cash_amount': cash_amount,
                'driver_liquidation_amount': driver_liquidation_amount,
                'cxc_cash_amount': cxc_cash_amount,
                'total_cash_collected': total_cash_collected,
                'cash_counted': cash_counted,
                'cash_difference': cash_difference,
                'has_cash_counted': has_cash_counted,
                'card_amount': card_amount,
                'cxc_card_amount': cxc_card_amount,
                'total_card_collected': total_card_collected,
                'transfer_amount': transfer_amount,
                'cxc_transfer_amount': cxc_transfer_amount,
                'total_transfer_collected': total_transfer_collected,
                'other_amount': other_amount,
                'cxc_other_amount': cxc_other_amount,
                'total_other_collected': total_other_collected,
                'cxc_total_amount': cxc_total_amount,
                'total_sales': total_sales,
                'session_id': session.id,
                'pos_config_id': pos.id if pos else False,
                'cashier_id': session.user_id.id if session.user_id else False,
                'pos_name': pos_name,
            }

            pos_groups[pos_key]['sessions'].append(session_vals)
            self._accumulate_totals(pos_groups[pos_key]['subtotal'], session_vals)
            self._accumulate_totals(totals, session_vals)

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

            subtotal = group.get('subtotal') or self._empty_totals()
            Line.create({
                'wizard_id': self.id,
                'sequence': sequence,
                'is_group': False,
                'is_subtotal': True,
                'subtotal_label': 'SUBTOTAL %s' % group['pos_name'],
                **subtotal,
                'has_cash_counted': True,
            })
            sequence += 1

        Line.create({
            'wizard_id': self.id,
            'sequence': sequence,
            'is_group': False,
            'is_subtotal': True,
            'subtotal_label': 'TOTAL EFECTIVO Y EQUIVALENTES POS DIA',
            **data['totals'],
            'has_cash_counted': True,
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
