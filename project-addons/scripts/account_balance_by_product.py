#!/usr/bin/env python3
import odoorpc
import sys


accounts_to_balance = ['30000001', '30000004', '30000005', '30000006',
                       '30000007', '32200000', '32200001', '32210001',
                       '61000000', '61200000']


class AccountBalanceByProduct(object):
    def __init__(self, dbname, user, passwd, port):
        """método incial"""

        try:
            self.odoo = odoorpc.ODOO('localhost', port=int(port))
            self.odoo.login(dbname, user, passwd)

            res = self.action_account_balance()
            # con exito
            if res:
                print("All set")
        except Exception as e:
            print("ERROR: {}".format(e))
            sys.exit(1)

    def action_account_balance(self):
        journal_id = self.odoo.env['account.journal'].\
            search([('code', '=', 'STJ')])
        move_vals = {'name': u'Regularización valor de existencias',
                     'journal_id': journal_id[0],
                     'to_check': True,
                     'date': '2021-10-04'}
        debit = credit = 0
        lines_data = []
        for acc in accounts_to_balance:
            account_id = self.odoo.env["account.account"].\
                search([('code', '=', acc)], limit=1)
            move_data = self.odoo.env['account.move.line'].\
                read_group([('account_id', '=', account_id[0])],
                           ['account_id', 'balance'], ['account_id'])
            if move_data[0]['balance'] < 0.0:
                field = 'debit'
                contrafield = 'credit'
                debit += abs(move_data[0]['balance'])
            elif move_data[0]['balance'] > 0.0:
                field = 'credit'
                contrafield = 'debit'
                credit += abs(move_data[0]['balance'])
            else:
                continue
            lines_data.append((0, 0, {'name': move_data[0]['account_id'][1],
                                      field: abs(move_data[0]['balance']),
                                      contrafield: 0.0,
                                      'account_id':
                                      move_data[0]['account_id'][0]}))
        all_products = self.odoo.env['product.product'].\
            search([('type', '=', 'product'), ('qty_available', '!=', 0.0)])
        cont = 1
        count = len(all_products)
        for prod_id in all_products:
            prod = self.odoo.env['product.product'].browse(prod_id)
            try:
                quants_data = self.odoo.env['stock.quant'].\
                    read_group([('product_id', '=', prod.id),
                                ('location_id.usage', '=', 'internal')],
                               ['location_id', 'quantity'], ['location_id'])
                for quant_data in quants_data:
                    value = quant_data['quantity'] * prod.standard_price
                    warehouse_id = self.odoo.env['stock.warehouse'].\
                        search([('lot_stock_id', '=',
                                 quant_data['location_id'][0])], limit=1)
                    if value > 0:
                        debit += round(value, 2)
                    else:
                        credit += round(abs(value), 2)
                    lines_data.\
                        append((0, 0,
                                {'name': prod.name + " en " +
                                 quant_data['location_id'][1],
                                 'debit': value > 0 and round(value, 2) or 0.0,
                                 'credit': value <= 0 and
                                 round(abs(value), 2) or 0.0,
                                 'account_id':
                                 prod.categ_id.
                                 property_stock_valuation_account_id.id,
                                 'quantity': quant_data['quantity'],
                                 'product_uom_id': prod.uom_id.id,
                                 'product_id': prod.id,
                                 'warehouse_id': warehouse_id[0]}))
                print("{} de {}".format(cont, count))
                cont += 1
            except Exception as e:
                print("EXCEPTION: {}".format(repr(e)))
        if debit - credit != 0:
            if debit > credit:
                field = 'credit'
                contrafield = 'debit'
            else:
                field = 'debit'
                contrafield = 'credit'
            account_id = self.odoo.env['account.account'].\
                search([('code', '=', '91000000')])
            lines_data.append((0, 0, {'name': "Saldo final",
                                      field: abs(debit - credit),
                                      contrafield: 0.0,
                                      'account_id': account_id[0]}))
        move_vals['line_ids'] = lines_data
        self.odoo.env['account.move'].create(move_vals)

        return True


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Uso: %s <dbname> <user> <password> <port>" % sys.argv[0])
    else:
        AccountBalanceByProduct(sys.argv[1], sys.argv[2], sys.argv[3],
                                sys.argv[4])
