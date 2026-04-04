from odoo import models


class IncomeStatementXlsx(models.AbstractModel):
    _name = 'report.lms_financial_reports.income_statement_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, wizard):

        sheet = workbook.add_worksheet("Estado de Resultados")

        # === FORMATOS ===

        title_format = workbook.add_format({
            'bold': True,
            'font_size': 16,
            'align': 'center'
        })

        subtitle_format = workbook.add_format({
            'italic': True,
            'align': 'center'
        })

        header_format = workbook.add_format({
            'bold': True,
            'bottom': 1
        })

        section_format = workbook.add_format({
            'bold': True
        })

        money_format = workbook.add_format({
            'num_format': '#,##0.00',
            'align': 'right'
        })

        total_format = workbook.add_format({
            'bold': True,
            'top': 1,
            'num_format': '#,##0.00',
            'align': 'right'
        })

        net_total_format = workbook.add_format({
            'bold': True,
            'top': 1,
            'bottom': 6,  # doble línea contable
            'num_format': '#,##0.00',
            'align': 'right'
        })

        # === ANCHO DE COLUMNAS ===
        sheet.set_column('A:A', 50)
        sheet.set_column('B:B', 20)

        row = 0

        # === TÍTULO ===
        sheet.merge_range(row, 0, row, 1, "ESTADO DE RESULTADOS", title_format)
        row += 1

        sheet.merge_range(
            row, 0, row, 1,
            f"Desde {wizard.date_from} hasta {wizard.date_to}",
            subtitle_format
        )
        row += 2

        # === ENCABEZADOS ===
        sheet.write(row, 0, "Concepto", header_format)
        sheet.write(row, 1, "Monto", header_format)
        row += 1

        # === DATOS ===
        for line in wizard._get_income_statement_data():

            # SECCIÓN
            if line.get('is_section'):
                sheet.write(row, 0, line['name'], section_format)
                row += 1
                continue

            # UTILIDAD NETA
            if line.get('is_total') and line['name'] == 'UTILIDAD NETA':
                sheet.write(row, 0, line['name'], section_format)
                sheet.write(row, 1, line['amount'], net_total_format)
                row += 1
                continue

            # OTROS TOTALES
            if line.get('is_total'):
                sheet.write(row, 0, line['name'], section_format)
                sheet.write(row, 1, line['amount'], total_format)
                row += 1
                continue

            # LÍNEAS NORMALES
            sheet.write(row, 0, line['name'])
            sheet.write(row, 1, line['amount'], money_format)

            row += 1