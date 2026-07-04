
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class LmsPosCashClosingActWizard(models.TransientModel):
    _name = "lms.pos.cash.closing.act.wizard"
    _description = "Acta de Cierre Caja POS"

    session_id = fields.Many2one(
        "pos.session",
        string="Sesion POS",
        required=True,
        domain=[("state", "=", "closed")],
    )

    # Solo CxC se captura en este wizard. El POS se toma del cierre oficial Odoo POS.
    cxc_cash_counted = fields.Float(
        string="Efectivo CxC contado",
        help="Monto fisico contado en la cajita separada de cobros CxC en efectivo.",
    )
    cxc_card_counted = fields.Float(
        string="Tarjeta CxC validada",
        help="Monto validado de cobros CxC por tarjeta.",
    )
    cxc_transfer_counted = fields.Float(
        string="Transferencia CxC validada",
        help="Monto validado de cobros CxC por transferencia.",
    )
    cxc_other_counted = fields.Float(
        string="Otros CxC validado",
        help="Monto validado de cobros CxC por otros metodos.",
    )

    @api.onchange("session_id")
    def _onchange_session_id(self):
        """Prellenar solo los valores de CxC para que el supervisor ajuste si hay diferencia."""
        for wizard in self:
            if not wizard.session_id:
                continue
            cxc_amounts = wizard._get_cxc_receipt_amounts(wizard.session_id)
            wizard.cxc_cash_counted = cxc_amounts["cash_total"]
            wizard.cxc_card_counted = cxc_amounts["card_total"]
            wizard.cxc_transfer_counted = cxc_amounts["transfer_total"]
            wizard.cxc_other_counted = cxc_amounts["other_total"]

    def action_print_report(self):
        self.ensure_one()
        if not self.session_id:
            raise UserError(_("Debe seleccionar una sesion POS."))

        return self.env.ref(
            "lms_financial_reports.action_report_lms_pos_cash_closing_act"
        ).report_action(self)

    def _amount(self, value):
        return float(value or 0.0)

    def _fmt_money(self, value):
        return "RD$ {:,.2f}".format(self._amount(value))

    def _fmt_datetime(self, value):
        if not value:
            return ""
        local_dt = fields.Datetime.context_timestamp(self, value)
        return local_dt.strftime("%d/%m/%Y %I:%M:%S %p")

    def _fmt_date(self, value):
        if not value:
            return ""
        local_dt = fields.Datetime.context_timestamp(self, value)
        return local_dt.strftime("%d/%m/%Y")

    def _is_cash_payment_method(self, method):
        return bool(getattr(method, "is_cash_count", False))

    def _is_cod_delivery_payment_method(self, method):
        """Metodo usado para ventas contra entrega de pedidos telefonicos.

        Aunque normalmente esta marcado como conteo de efectivo en POS,
        operativamente no representa dinero fisico recibido en caja hasta que
        el chofer liquide. Por eso el acta lo separa del efectivo contado.
        """
        return bool(getattr(method, "is_cod_delivery", False))

    def _classify_payment_method(self, method):
        name = (method.name or "").lower()
        if self._is_cash_payment_method(method):
            return "cash"
        if "tarjeta" in name or "card" in name:
            return "card"
        if "transfer" in name or "transf" in name:
            return "transfer"
        return "other"

    def _get_payment_amounts(self, session):
        payments = self.env["pos.payment"].search([
            ("session_id", "=", session.id),
        ])

        result = {
            "cash_total": 0.0,
            "card_total": 0.0,
            "transfer_total": 0.0,
            "other_total": 0.0,
            # Total real que debe validarse en caja/medios del cierre.
            "total": 0.0,
            # Total bruto POS incluyendo contra entrega, solo informativo.
            "gross_total": 0.0,
            # Contra entrega pendiente de chofer: no es efectivo fisico de caja.
            "cod_delivery_total": 0.0,
        }

        for payment in payments:
            amount = self._amount(payment.amount)
            method = payment.payment_method_id
            result["gross_total"] += amount

            if self._is_cod_delivery_payment_method(method):
                result["cod_delivery_total"] += amount
                continue

            method_type = self._classify_payment_method(method)
            key = "%s_total" % method_type
            if key not in result:
                key = "other_total"
            result[key] += amount
            result["total"] += amount

        return result

    def _get_phone_order_by_pos_order(self, pos_order):
        if not pos_order or "lms.phone.order" not in self.env:
            return False

        phone_model = self.env["lms.phone.order"]
        phone = phone_model.search([("pos_order_id", "=", pos_order.id)], limit=1)
        if not phone and "pos_order_ids" in phone_model._fields:
            phone = phone_model.search([("pos_order_ids", "in", pos_order.ids)], limit=1)
        return phone

    def _selection_label(self, record, field_name, value):
        if not record or field_name not in record._fields or not value:
            return value or ""
        selection = record._fields[field_name].selection
        if callable(selection):
            selection = selection(record)
        return dict(selection or []).get(value, value)

    def _get_cod_delivery_lines(self, session):
        """Detalle informativo de pagos contra entrega de la sesion.

        Estos pagos quedan registrados en POS para completar la factura, pero no
        deben formar parte del efectivo fisico contado en caja mientras el
        chofer no los liquide.
        """
        result = {
            "lines": [],
            "cod_total": 0.0,
            "cod_total_fmt": self._fmt_money(0.0),
            "non_cod_total": 0.0,
            "non_cod_total_fmt": self._fmt_money(0.0),
            "order_total": 0.0,
            "order_total_fmt": self._fmt_money(0.0),
        }

        payments = self.env["pos.payment"].search([
            ("session_id", "=", session.id),
        ], order="id asc")

        processed_order_ids = set()

        for payment in payments:
            if not self._is_cod_delivery_payment_method(payment.payment_method_id):
                continue

            order = payment.pos_order_id
            if order and order.id in processed_order_ids:
                continue
            if order:
                processed_order_ids.add(order.id)
                order_payments = order.payment_ids
            else:
                order_payments = payment

            cod_amount = sum(
                self._amount(pay.amount)
                for pay in order_payments
                if self._is_cod_delivery_payment_method(pay.payment_method_id)
            )
            non_cod_amount = sum(
                self._amount(pay.amount)
                for pay in order_payments
                if not self._is_cod_delivery_payment_method(pay.payment_method_id)
            )

            non_cod_methods = []
            for pay in order_payments:
                if self._is_cod_delivery_payment_method(pay.payment_method_id):
                    continue
                non_cod_methods.append("%s %s" % (pay.payment_method_id.name or "", self._fmt_money(pay.amount)))

            phone = self._get_phone_order_by_pos_order(order) if order else False
            invoice = False
            if phone and "invoice_id" in phone._fields:
                invoice = phone.invoice_id
            if not invoice and order:
                invoice = getattr(order, "account_move", False)

            driver = ""
            if phone and "driver_id" in phone._fields and phone.driver_id:
                driver = phone.driver_id.display_name

            cash_state = ""
            cash_state_label = ""
            if phone and "delivery_cash_state" in phone._fields:
                cash_state = phone.delivery_cash_state or ""
                cash_state_label = self._selection_label(phone, "delivery_cash_state", cash_state)

            order_total = self._amount(getattr(order, "amount_total", 0.0)) if order else (cod_amount + non_cod_amount)

            line = {
                "phone_name": phone.name if phone else "",
                "pos_order_name": order.name if order else "",
                "pos_reference": getattr(order, "pos_reference", "") if order else "",
                "invoice_name": invoice.name if invoice else "",
                "partner": (phone.partner_id.display_name if phone and phone.partner_id else (order.partner_id.display_name if order and order.partner_id else "")),
                "driver": driver,
                "cash_state": cash_state,
                "cash_state_label": cash_state_label or "COD pendiente",
                "non_cod_detail": ", ".join(non_cod_methods),
                "non_cod_amount": non_cod_amount,
                "non_cod_amount_fmt": self._fmt_money(non_cod_amount),
                "cod_amount": cod_amount,
                "cod_amount_fmt": self._fmt_money(cod_amount),
                "order_total": order_total,
                "order_total_fmt": self._fmt_money(order_total),
            }
            result["lines"].append(line)
            result["cod_total"] += cod_amount
            result["non_cod_total"] += non_cod_amount
            result["order_total"] += order_total

        result["cod_total_fmt"] = self._fmt_money(result["cod_total"])
        result["non_cod_total_fmt"] = self._fmt_money(result["non_cod_total"])
        result["order_total_fmt"] = self._fmt_money(result["order_total"])
        return result

    def _get_official_pos_counted(self, session, pos_amounts):
        """
        Valores oficiales del cierre nativo Odoo POS.
        - Efectivo: usa cash_register_balance_end_real guardado al cerrar caja.
        - Tarjeta/Transferencia/Otros: se toman del cierre POS por metodo. En Odoo,
          estos metodos quedan validados contra los pagos registrados de la sesion.
        """
        return {
            "cash_counted": self._amount(getattr(session, "cash_register_balance_end_real", 0.0)),
            "card_counted": self._amount(pos_amounts.get("card_total")),
            "transfer_counted": self._amount(pos_amounts.get("transfer_total")),
            "other_counted": self._amount(pos_amounts.get("other_total")),
        }

    def _get_cxc_receipt_amounts(self, session):
        result = {
            "cash_total": 0.0,
            "card_total": 0.0,
            "transfer_total": 0.0,
            "other_total": 0.0,
            "total": 0.0,
            "lines": [],
        }

        if "lms.pos.cxc.receipt" not in self.env:
            return result

        receipts = self.env["lms.pos.cxc.receipt"].search([
            ("pos_session_id", "=", session.id),
            ("state", "=", "posted"),
        ], order="date_order asc, id asc")

        for receipt in receipts:
            amount = self._amount(receipt.amount)
            method = receipt.payment_method_id
            method_type = self._classify_payment_method(method)
            key = "%s_total" % method_type
            if key not in result:
                key = "other_total"
            result[key] += amount
            result["total"] += amount
            result["lines"].append({
                "name": receipt.name,
                "date": self._fmt_datetime(receipt.date_order),
                "partner": receipt.partner_id.display_name or "",
                "method": method.name or "",
                "method_type": method_type,
                "reference": receipt.reference or "",
                "amount": amount,
                "amount_fmt": self._fmt_money(amount),
            })

        return result

    def _build_cuadre_rows(self, values, counted_values):
        base = [
            ("Efectivo", "cash_total", "cash_counted"),
            ("Tarjeta", "card_total", "card_counted"),
            ("Transferencias", "transfer_total", "transfer_counted"),
        ]
        if self._amount(values.get("other_total")) or self._amount(counted_values.get("other_counted")):
            base.append(("Otros", "other_total", "other_counted"))

        rows = []
        expected_total = 0.0
        counted_total = 0.0
        difference_total = 0.0

        for label, expected_key, counted_key in base:
            expected = self._amount(values.get(expected_key))
            counted = self._amount(counted_values.get(counted_key))
            difference = counted - expected

            expected_total += expected
            counted_total += counted
            difference_total += difference

            rows.append({
                "label": label,
                "expected": expected,
                "expected_fmt": self._fmt_money(expected),
                "counted": counted,
                "counted_fmt": self._fmt_money(counted),
                "difference": difference,
                "difference_fmt": self._fmt_money(difference),
            })

        return {
            "rows": rows,
            "expected_total": expected_total,
            "expected_total_fmt": self._fmt_money(expected_total),
            "counted_total": counted_total,
            "counted_total_fmt": self._fmt_money(counted_total),
            "difference_total": difference_total,
            "difference_total_fmt": self._fmt_money(difference_total),
        }

    def _get_totals_by_method(self, pos_amounts, cxc_amounts, pos_counted, cxc_counted):
        rows = [
            ("Efectivo", "cash_total", "cash_counted"),
            ("Tarjeta", "card_total", "card_counted"),
            ("Transferencias", "transfer_total", "transfer_counted"),
        ]
        if (
            self._amount(pos_amounts.get("other_total"))
            or self._amount(cxc_amounts.get("other_total"))
            or self._amount(pos_counted.get("other_counted"))
            or self._amount(cxc_counted.get("other_counted"))
        ):
            rows.append(("Otros", "other_total", "other_counted"))

        result_rows = []
        pos_total = 0.0
        cxc_total = 0.0
        system_total = 0.0
        counted_total = 0.0
        difference_total = 0.0

        for label, amount_key, counted_key in rows:
            pos_value = self._amount(pos_amounts.get(amount_key))
            cxc_value = self._amount(cxc_amounts.get(amount_key))
            system_value = pos_value + cxc_value
            counted_value = self._amount(pos_counted.get(counted_key)) + self._amount(cxc_counted.get(counted_key))
            difference = counted_value - system_value

            pos_total += pos_value
            cxc_total += cxc_value
            system_total += system_value
            counted_total += counted_value
            difference_total += difference

            result_rows.append({
                "label": label,
                "pos_value": pos_value,
                "pos_fmt": self._fmt_money(pos_value),
                "cxc_value": cxc_value,
                "cxc_fmt": self._fmt_money(cxc_value),
                "system_value": system_value,
                "system_fmt": self._fmt_money(system_value),
                "counted_value": counted_value,
                "counted_fmt": self._fmt_money(counted_value),
                "difference": difference,
                "difference_fmt": self._fmt_money(difference),
            })

        return {
            "rows": result_rows,
            "pos_total": pos_total,
            "pos_total_fmt": self._fmt_money(pos_total),
            "cxc_total": cxc_total,
            "cxc_total_fmt": self._fmt_money(cxc_total),
            "system_total": system_total,
            "system_total_fmt": self._fmt_money(system_total),
            "counted_total": counted_total,
            "counted_total_fmt": self._fmt_money(counted_total),
            "difference_total": difference_total,
            "difference_total_fmt": self._fmt_money(difference_total),
        }

    def _get_report_values(self):
        self.ensure_one()

        session = self.session_id
        company = self.env.company

        pos_amounts = self._get_payment_amounts(session)
        cod_delivery = self._get_cod_delivery_lines(session)
        cxc_amounts = self._get_cxc_receipt_amounts(session)

        # POS oficial no se captura ni se modifica en este wizard.
        pos_counted = self._get_official_pos_counted(session, pos_amounts)

        # Solo CxC se captura en el wizard.
        cxc_counted = {
            "cash_counted": self.cxc_cash_counted,
            "card_counted": self.cxc_card_counted,
            "transfer_counted": self.cxc_transfer_counted,
            "other_counted": self.cxc_other_counted,
        }

        pos_cuadre = self._build_cuadre_rows(pos_amounts, pos_counted)
        cxc_cuadre = self._build_cuadre_rows(cxc_amounts, cxc_counted)
        totals_by_method = self._get_totals_by_method(pos_amounts, cxc_amounts, pos_counted, cxc_counted)

        difference_total = self._amount(totals_by_method["difference_total"])
        if abs(difference_total) <= 0.01:
            result_label = "CUADRADO"
        elif difference_total < -0.01:
            result_label = "FALTANTE"
        else:
            result_label = "SOBRANTE"

        order_count = len(session.order_ids)

        return {
            "wizard": self,
            "company": company,
            "session": session,
            "pos_config": session.config_id,
            "cashier": session.user_id,
            "order_count": order_count,
            "date_fmt": self._fmt_date(session.start_at),
            "start_fmt": self._fmt_datetime(session.start_at),
            "stop_fmt": self._fmt_datetime(session.stop_at),

            "pos_amounts": pos_amounts,
            "cod_delivery": cod_delivery,
            "cxc_amounts": cxc_amounts,
            "pos_cuadre": pos_cuadre,
            "cxc_cuadre": cxc_cuadre,
            "totals_by_method": totals_by_method,
            "result_label": result_label,

            "cash_system_fmt": self._fmt_money(pos_amounts["cash_total"]),
            "card_total_fmt": self._fmt_money(pos_amounts["card_total"]),
            "transfer_total_fmt": self._fmt_money(pos_amounts["transfer_total"]),
            "other_total_fmt": self._fmt_money(pos_amounts["other_total"]),
            "cod_delivery_total_fmt": self._fmt_money(pos_amounts["cod_delivery_total"]),
            "pos_total_fmt": self._fmt_money(pos_amounts["total"]),
            "pos_gross_total_fmt": self._fmt_money(pos_amounts["gross_total"]),
            "cxc_cash_total_fmt": self._fmt_money(cxc_amounts["cash_total"]),
            "cxc_card_total_fmt": self._fmt_money(cxc_amounts["card_total"]),
            "cxc_transfer_total_fmt": self._fmt_money(cxc_amounts["transfer_total"]),
            "cxc_other_total_fmt": self._fmt_money(cxc_amounts["other_total"]),
            "cxc_total_fmt": self._fmt_money(cxc_amounts["total"]),
        }
