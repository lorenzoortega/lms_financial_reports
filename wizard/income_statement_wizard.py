from odoo import models, fields


class IncomeStatementWizard(models.TransientModel):
    _name = 'lms.income.statement.wizard'
    _description = 'Estado de Resultados'

    date_from = fields.Date(string="Fecha Inicio", required=True)
    date_to = fields.Date(string="Fecha Fin", required=True)

    def action_print_pdf(self):
        self.ensure_one()
        return self.env.ref(
            'lms_financial_reports.action_income_statement_pdf'
        ).report_action(self)

    def action_export_xlsx(self):
        self.ensure_one()
        return self.env.ref(
            'lms_financial_reports.action_income_statement_xlsx'
        ).report_action(self)

    def _get_income_statement_data(self):
        self.ensure_one()

        MoveLine = self.env['account.move.line']

        domain = [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('move_id.state', '=', 'posted'),
        ]

        grouped = MoveLine.read_group(
            domain,
            ['debit', 'credit', 'account_id'],
            ['account_id']
        )

        data = {}
        for g in grouped:
            if g.get('account_id'):
                data[g['account_id'][0]] = {
                    'debit': g['debit'],
                    'credit': g['credit'],
                }

        accounts = self.env['account.account'].search([], order='code')

        ingresos = []
        costos = []
        gastos = []

        for acc in accounts:
            if acc.id not in data:
                continue

            if acc.code.startswith('4'):  # ingresos
                balance = data[acc.id]['credit'] - data[acc.id]['debit']
                ingresos.append({
                    'account_id': acc.id,
                    'name': acc.display_name,
                    'amount': balance,
                })

            elif acc.code.startswith('5'):  # costos
                balance = data[acc.id]['debit'] - data[acc.id]['credit']
                costos.append({
                    'account_id': acc.id,
                    'name': acc.display_name,
                    'amount': balance,
                })

            elif acc.code.startswith('6'):  # gastos
                balance = data[acc.id]['debit'] - data[acc.id]['credit']
                gastos.append({
                    'account_id': acc.id,
                    'name': acc.display_name,
                    'amount': balance,
                })

        result = []

        # INGRESOS
        result.append({
            'name': 'INGRESOS',
            'amount': 0.0,
            'is_section': True,
            'is_total': False,
            'account_id': False,
        })

        total_ingresos = 0.0
        for item in ingresos:
            result.append({
                'name': item['name'],
                'amount': item['amount'],
                'is_section': False,
                'is_total': False,
                'account_id': item['account_id'],
            })
            total_ingresos += item['amount']

        result.append({
            'name': 'TOTAL INGRESOS',
            'amount': total_ingresos,
            'is_section': False,
            'is_total': True,
            'account_id': False,
        })

        # COSTOS
        result.append({
            'name': 'COSTOS',
            'amount': 0.0,
            'is_section': True,
            'is_total': False,
            'account_id': False,
        })

        total_costos = 0.0
        for item in costos:
            result.append({
                'name': item['name'],
                'amount': item['amount'],
                'is_section': False,
                'is_total': False,
                'account_id': item['account_id'],
            })
            total_costos += item['amount']

        result.append({
            'name': 'TOTAL COSTOS',
            'amount': total_costos,
            'is_section': False,
            'is_total': True,
            'account_id': False,
        })

        utilidad_bruta = total_ingresos - total_costos
        result.append({
            'name': 'UTILIDAD BRUTA',
            'amount': utilidad_bruta,
            'is_section': False,
            'is_total': True,
            'account_id': False,
        })

        # GASTOS
        result.append({
            'name': 'GASTOS',
            'amount': 0.0,
            'is_section': True,
            'is_total': False,
            'account_id': False,
        })

        total_gastos = 0.0
        for item in gastos:
            result.append({
                'name': item['name'],
                'amount': item['amount'],
                'is_section': False,
                'is_total': False,
                'account_id': item['account_id'],
            })
            total_gastos += item['amount']

        result.append({
            'name': 'TOTAL GASTOS',
            'amount': total_gastos,
            'is_section': False,
            'is_total': True,
            'account_id': False,
        })

        utilidad_neta = utilidad_bruta - total_gastos
        result.append({
            'name': 'UTILIDAD NETA',
            'amount': utilidad_neta,
            'is_section': False,
            'is_total': True,
            'account_id': False,
        })

        return result

    def action_view_screen(self):
        self.ensure_one()

        Line = self.env['lms.income.statement.line']
        Line.search([('wizard_id', '=', self.id)]).unlink()

        data_lines = self._get_income_statement_data()

        seq = 1
        for line in data_lines:
            Line.create({
                'wizard_id': self.id,
                'sequence': seq,
                'name': line['name'],
                'amount': line['amount'],
                'is_section': line['is_section'],
                'is_total': line['is_total'],
                'account_id': line.get('account_id') or False,
            })
            seq += 1

        return {
            'type': 'ir.actions.act_window',
            'name': 'Estado de Resultados',
            'res_model': 'lms.income.statement.line',
            'view_mode': 'list',
            'views': [
                (self.env.ref('lms_financial_reports.view_income_statement_line_list').id, 'list')
            ],
            'domain': [('wizard_id', '=', self.id)],
            'target': 'current',
        }