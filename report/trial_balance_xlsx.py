from odoo import models


class TrialBalanceXlsx(models.AbstractModel):
    _name = 'report.lms_financial_reports.trial_balance_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Balanza de Comprobación XLSX'

    def generate_xlsx_report(self, workbook, data, wizard):

        groups = wizard._get_trial_balance_data()
        company = wizard.env.company

        sheet_name = f"Balanza {wizard.date_to.year}"
        sheet = workbook.add_worksheet(sheet_name[:31])

        # ==========================
        # FORMATOS
        # ==========================

        header_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'border': 1,
        })

        title_format = workbook.add_format({
            'bold': True,
            'font_size': 14
        })

        number_format = workbook.add_format({
            'num_format': '#,##0.00',
            'align': 'right'
        })

        bold_number_format = workbook.add_format({
            'bold': True,
            'num_format': '#,##0.00',
            'align': 'right'
        })

        bold_format = workbook.add_format({
            'bold': True
        })

        class_format = workbook.add_format({
            'bold': True,
            'bg_color': '#EAEAEA'
        })

        subtotal_format = workbook.add_format({
            'bold': True,
            'bg_color': '#F2F2F2'
        })

        # ==========================
        # ENCABEZADO
        # ==========================

        row = 0

        sheet.write(row, 0, f"Balanza de Comprobación {wizard.date_to.year}", title_format)
        row += 1

        sheet.write(row, 0, f"Empresa: {company.name}")
        row += 1

        sheet.write(row, 0, f"Rango: {wizard.date_from} - {wizard.date_to}")
        row += 2

        headers = [
            "Cuenta",
            "Descripción",
            "Acum. Año Débitos",
            "Acum. Año Créditos",
            "Acum. Año Balance",
            "Período Débitos",
            "Período Créditos",
            "Balance Período",
        ]

        for col, header in enumerate(headers):
            sheet.write(row, col, header, header_format)

        row += 1

        # ==========================
        # CUERPO
        # ==========================

        total_general = {
            'debit_year': 0.0,
            'credit_year': 0.0,
            'debit_period': 0.0,
            'credit_period': 0.0,
        }

        for group in groups:

            class_name = group['class_name']
            accounts = group['accounts']
            totals = group['totals']

            # Línea clase
            sheet.write(row, 0, f"CLASE {group['class_code']} - {class_name}", class_format)
            row += 1

            for line in accounts:

                sheet.write(row, 0, line['account'].code)
                sheet.write(row, 1, line['account'].name)

                sheet.write(row, 2, line['debit_year'], number_format)
                sheet.write(row, 3, line['credit_year'], number_format)
                sheet.write(row, 4, line['balance_year'], number_format)

                sheet.write(row, 5, line['debit_period'], number_format)
                sheet.write(row, 6, line['credit_period'], number_format)
                sheet.write(row, 7, line['balance_period'], number_format)

                row += 1

            # Subtotal por clase
            sheet.write(row, 0, f"SUBTOTAL {class_name}", subtotal_format)

            sheet.write(row, 2, totals['debit_year'], bold_number_format)
            sheet.write(row, 3, totals['credit_year'], bold_number_format)
            sheet.write(row, 4, totals['debit_year'] - totals['credit_year'], bold_number_format)

            sheet.write(row, 5, totals['debit_period'], bold_number_format)
            sheet.write(row, 6, totals['credit_period'], bold_number_format)
            sheet.write(row, 7, totals['debit_period'] - totals['credit_period'], bold_number_format)

            total_general['debit_year'] += totals['debit_year']
            total_general['credit_year'] += totals['credit_year']
            total_general['debit_period'] += totals['debit_period']
            total_general['credit_period'] += totals['credit_period']

            row += 2

        # ==========================
        # TOTALES GENERALES
        # ==========================

        sheet.write(row, 0, "TOTALES GENERALES", bold_format)

        sheet.write(row, 2, total_general['debit_year'], bold_number_format)
        sheet.write(row, 3, total_general['credit_year'], bold_number_format)
        sheet.write(row, 4, total_general['debit_year'] - total_general['credit_year'], bold_number_format)

        sheet.write(row, 5, total_general['debit_period'], bold_number_format)
        sheet.write(row, 6, total_general['credit_period'], bold_number_format)
        sheet.write(row, 7, total_general['debit_period'] - total_general['credit_period'], bold_number_format)

        # ==========================
        # AJUSTE COLUMNAS
        # ==========================

        sheet.set_column(0, 0, 15)
        sheet.set_column(1, 1, 40)
        sheet.set_column(2, 7, 18)
