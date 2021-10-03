#!/usr/bin/env python3
import odoorpc
import sys


class RegularizeRemainingFields(object):
    def __init__(self, dbname, user, passwd, port):
        """método incial"""

        try:
            self.odoo = odoorpc.ODOO('localhost', port=int(port))
            self.odoo.login(dbname, user, passwd)

            res = self.action_real_valuation()
            # con exito
            if res:
                print("All set")
        except Exception as e:
            print ("ERROR: ", (e))
            sys.exit(1)

    def action_real_valuation(self):
        all_moves = self.odoo.env['stock.move'].\
            search(['|', ('remaining_value', '!=', 0),
                    ('remaining_qty', '!=', 0)])
        all_moves = self.odoo.env['stock.move'].browse(all_moves)
        all_moves.write({'remaining_value': 0.0,
                         'remaining_qty': 0.0})
        all_products = self.odoo.env['product.product'].\
            search([('type', '=', 'product'),('qty_available', '!=', 0.0)])
        cont = 1
        company_id = self.odoo.env.user.company_id.id
        total_prod = len(all_products)
        for prod in all_products:
            prod = self.odoo.env['product.product'].browse(prod)
            move_ids = self.odoo.env['stock.move'].\
                search([
                    ('product_id', '=', prod.id),
                    ('state', '=', 'done'),
                    '|', '&', '|', ('location_id.company_id', '=', False),
                    '&', ('location_id.usage', 'in',
                          ['inventory', 'production']),
                    ('location_id.company_id', '=', company_id),
                    ('location_dest_id.company_id', '=', company_id),
                    '&', ('location_id.company_id', '=', company_id),
                    '|', ('location_dest_id.company_id', '=', False), '&',
                    ('location_dest_id.usage', 'in',
                     ['inventory', 'production']),
                    ('location_dest_id.company_id', '=', company_id)],
                        order="date desc, id", limit=1)
            if not move_ids:
                cont += 1
                continue
            move = self.odoo.env['stock.move'].browse(move_ids[0])
            move.write({'remaining_value':
                        prod.qty_available * prod.standard_price,
                        'remaining_qty': prod.qty_available})
            print("{} de {}".format(cont, total_prod))
            cont += 1

        return True


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Uso: %s <dbname> <user> <password> <port>" % sys.argv[0])
    else:
        RegularizeRemainingFields(sys.argv[1], sys.argv[2], sys.argv[3],
                                  sys.argv[4])
