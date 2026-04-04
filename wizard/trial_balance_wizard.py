from odoo import models, fields, api
from odoo.exceptions import ValidationError


class TrialBalanceWizard(models.TransientModel):
    _name = 'lms.trial.balance.wizard'
    _description = 'Balanza de Comprobación'

    date_from = fields.Date(string="Fecha Inicio", required=True)
    date_to = fields.Date(string="Fecha Fin", required=True)

    show_zero_accounts = fields.Boolean(
        string="Mostrar cuentas en cero",
        default=False
    )

    # =====================================================
    # VALIDACIÓN
    # =====================================================

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for rec in self:
            if not rec.date_from or not rec.date_to:
                raise ValidationError("Debe seleccionar Fecha Inicio y Fecha Fin.")

            if rec.date_from > rec.date_to:
                raise ValidationError("La Fecha Inicio no puede ser mayor que la Fecha Fin.")

            if (rec.date_to.year - rec.date_from.year) > 5:
                raise ValidationError("No se permite generar reportes mayores a 5 años.")

    # =====================================================
    # VER EN PANTALLA
    # =====================================================

    def action_view_screen(self):
        self.ensure_one()

        Line = self.env['lms.trial.balance.line']
        Line.search([('wizard_id', '=', self.id)]).unlink()

        data = self._get_trial_balance_data()

        total_general_debit_year = 0.0
        total_general_credit_year = 0.0
        total_general_debit_period = 0.0
        total_general_credit_period = 0.0

        for group in data:

            # Cabecera con totales por clase
            Line.create({
                'wizard_id': self.id,
                'class_code': group['class_code'],
                'is_group': True,
                'group_name': group['class_name'],
                'debit_year': group['totals']['debit_year'],
                'credit_year': group['totals']['credit_year'],
                'balance_year': group['totals']['debit_year'] - group['totals']['credit_year'],
                'debit_period': group['totals']['debit_period'],
                'credit_period': group['totals']['credit_period'],
                'balance_period': group['totals']['debit_period'] - group['totals']['credit_period'],
            })

            # Totales generales
            total_general_debit_year += group['totals']['debit_year']
            total_general_credit_year += group['totals']['credit_year']
            total_general_debit_period += group['totals']['debit_period']
            total_general_credit_period += group['totals']['credit_period']

            # Líneas por cuenta
            for acc in group['accounts']:
                Line.create({
                    'wizard_id': self.id,
                    'class_code': group['class_code'],
                    'is_group': False,
                    'account_id': acc['account'].id,
                    'debit_year': acc['debit_year'],
                    'credit_year': acc['credit_year'],
                    'balance_year': acc['balance_year'],
                    'debit_period': acc['debit_period'],
                    'credit_period': acc['credit_period'],
                    'balance_period': acc['balance_period'],
                })

        # Línea final de totales generales
        Line.create({
            'wizard_id': self.id,
            'class_code': '6',
            'is_group': True,
            'group_name': 'TOTALES GENERALES',
            'debit_year': total_general_debit_year,
            'credit_year': total_general_credit_year,
            'balance_year': total_general_debit_year - total_general_credit_year,
            'debit_period': total_general_debit_period,
            'credit_period': total_general_credit_period,
            'balance_period': total_general_debit_period - total_general_credit_period,
        })

        return {
            'type': 'ir.actions.act_window',
            'name': 'Balanza de Comprobación',
            'res_model': 'lms.trial.balance.line',
            'view_mode': 'list',
            'views': [
                (self.env.ref('lms_financial_reports.view_trial_balance_line_list').id, 'list')
            ],
            'domain': [('wizard_id', '=', self.id)],
            'target': 'current',
        }

    # =====================================================
    # PDF
    # =====================================================

    def action_print_pdf(self):
        self.ensure_one()
        return self.env.ref(
            'lms_financial_reports.action_trial_balance_pdf'
        ).report_action(self)

    # =====================================================
    # XLSX
    # =====================================================

    def action_export_xlsx(self):
        self.ensure_one()
        return self.env.ref(
            'lms_financial_reports.action_trial_balance_xlsx'
        ).report_action(self)

    # =====================================================
    # GENERADOR DATOS
    # =====================================================

    def _get_trial_balance_data(self):
        self.ensure_one()

        Account = self.env['account.account']
        MoveLine = self.env['account.move.line']

        fiscal_start = self.date_to.replace(month=1, day=1)

        domain_year = [
            ('date', '>=', fiscal_start),
            ('date', '<=', self.date_to),
            ('move_id.state', '=', 'posted'),
        ]

        domain_period = [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('move_id.state', '=', 'posted'),
        ]

        grouped_year = MoveLine.read_group(
            domain_year,
            ['debit', 'credit', 'account_id'],
            ['account_id']
        )

        grouped_period = MoveLine.read_group(
            domain_period,
            ['debit', 'credit', 'account_id'],
            ['account_id']
        )

        year_dict = {
            g['account_id'][0]: g
            for g in grouped_year if g.get('account_id')
        }

        period_dict = {
            g['account_id'][0]: g
            for g in grouped_period if g.get('account_id')
        }

        accounts = Account.search([], order="code")

        ordered_classes = [
            ('1', 'ACTIVOS'),
            ('2', 'PASIVOS'),
            ('3', 'PATRIMONIO'),
            ('4', 'INGRESOS'),
            ('5', 'COSTOS'),
            ('6', 'GASTOS'),
        ]

        class_groups = []

        for class_code, class_name in ordered_classes:

            class_accounts = accounts.filtered(
                lambda a: a.code and a.code.startswith(class_code)
            )

            lines = []

            totals = {
                'debit_year': 0.0,
                'credit_year': 0.0,
                'debit_period': 0.0,
                'credit_period': 0.0,
            }

            for account in class_accounts:

                debit_year = year_dict.get(account.id, {}).get('debit', 0.0)
                credit_year = year_dict.get(account.id, {}).get('credit', 0.0)

                debit_period = period_dict.get(account.id, {}).get('debit', 0.0)
                credit_period = period_dict.get(account.id, {}).get('credit', 0.0)

                balance_year = debit_year - credit_year
                balance_period = debit_period - credit_period

                if not self.show_zero_accounts:
                    if balance_year == 0.0 and balance_period == 0.0:
                        continue

                totals['debit_year'] += debit_year
                totals['credit_year'] += credit_year
                totals['debit_period'] += debit_period
                totals['credit_period'] += credit_period

                lines.append({
                    'account': account,
                    'debit_year': debit_year,
                    'credit_year': credit_year,
                    'balance_year': balance_year,
                    'debit_period': debit_period,
                    'credit_period': credit_period,
                    'balance_period': balance_period,
                })

            if lines:
                class_groups.append({
                    'class_code': class_code,
                    'class_name': class_name,
                    'accounts': lines,
                    'totals': totals
                })

        return class_groups