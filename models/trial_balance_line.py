from odoo import models, fields, api, _
from odoo.exceptions import UserError


class TrialBalanceLine(models.TransientModel):
    _name = 'lms.trial.balance.line'
    _description = 'Líneas Balanza de Comprobación'
    _order = 'class_code, is_group desc, account_id'

    wizard_id = fields.Many2one(
        'lms.trial.balance.wizard',
        ondelete='cascade'
    )

    # Identifica si es cabecera de grupo
    is_group = fields.Boolean(default=False)

    # Nombre visible del grupo
    group_name = fields.Char(string="Grupo")

    # Tipo de fila (para decoración visual segura en Odoo 18)
    row_type = fields.Selection(
        [
            ('group', 'Grupo'),
            ('line', 'Línea'),
        ],
        compute="_compute_row_type",
        store=False
    )

    # Campo visual que muestra grupo o cuenta con sangría
    display_name_line = fields.Char(
        string="Grupo / Cuenta",
        compute="_compute_display_name",
        store=False
    )

    class_code = fields.Selection(
        [
            ('1', 'ACTIVOS'),
            ('2', 'PASIVOS'),
            ('3', 'PATRIMONIO'),
            ('4', 'INGRESOS'),
            ('5', 'COSTOS'),
            ('6', 'GASTOS'),
        ],
        required=True,
    )

    account_id = fields.Many2one(
        'account.account',
        string="Cuenta"
    )

    debit_year = fields.Float(string="Débitos Año")
    credit_year = fields.Float(string="Créditos Año")
    balance_year = fields.Float(string="Balance Año")

    debit_period = fields.Float(string="Débitos Período")
    credit_period = fields.Float(string="Créditos Período")
    balance_period = fields.Float(string="Balance Período")

    @api.depends('is_group')
    def _compute_row_type(self):
        for rec in self:
            rec.row_type = 'group' if rec.is_group else 'line'

    @api.depends('is_group', 'group_name', 'account_id')
    def _compute_display_name(self):
        for rec in self:
            if rec.is_group:
                # Mostrar nombre completo de la cabecera
                if rec.group_name == 'TOTALES GENERALES':
                    rec.display_name_line = rec.group_name
                else:
                    rec.display_name_line = f"CLASE {rec.class_code} - {rec.group_name}"
            else:
                account_name = rec.account_id.display_name or ''
                rec.display_name_line = f"   {account_name}"

    def action_open_account_moves(self):
        self.ensure_one()

        if self.is_group or not self.account_id:
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