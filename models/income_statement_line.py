from odoo import models, fields, api, _
from odoo.exceptions import UserError


class IncomeStatementLine(models.TransientModel):
    _name = 'lms.income.statement.line'
    _description = 'Líneas Estado de Resultados'
    _order = 'sequence'

    wizard_id = fields.Many2one(
        'lms.income.statement.wizard',
        ondelete='cascade'
    )

    sequence = fields.Integer()

    name = fields.Char(string="Concepto")

    is_section = fields.Boolean(default=False)
    is_total = fields.Boolean(default=False)

    account_id = fields.Many2one(
        'account.account',
        string="Cuenta"
    )

    amount = fields.Float(string="Monto")

    is_account_line = fields.Boolean(
        string="Es línea de cuenta",
        compute="_compute_is_account_line",
        store=False
    )

    @api.depends('is_section', 'is_total', 'account_id')
    def _compute_is_account_line(self):
        for rec in self:
            rec.is_account_line = bool(rec.account_id and not rec.is_section and not rec.is_total)

    def action_open_account_moves(self):
        self.ensure_one()

        if not self.account_id or self.is_section or self.is_total:
            raise UserError(_("Esta fila no corresponde a una cuenta contable navegable."))

        if not self.wizard_id:
            raise UserError(_("No se encontró el asistente asociado a la línea."))

        if not self.wizard_id.date_from or not self.wizard_id.date_to:
            raise UserError(_("No se encontró el rango de fechas del reporte."))

        domain = [
            ('account_id', '=', self.account_id.id),
            ('date', '>=', self.wizard_id.date_from),
            ('date', '<=', self.wizard_id.date_to),
            ('move_id.state', '=', 'posted'),
        ]

        return {
            'type': 'ir.actions.act_window',
            'name': _('Movimientos de %s') % self.account_id.display_name,
            'res_model': 'account.move.line',
            'view_mode': 'list,form',
            'domain': domain,
            'context': {
                'default_account_id': self.account_id.id,
                'search_default_posted': 1,
            },
            'target': 'current',
        }