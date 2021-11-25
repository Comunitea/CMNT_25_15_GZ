/*
Copyright 2019 Comunitea.
License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
*/
odoo.define('account_bank_statement_business_line.abs', function (require) {
    "use strict";

    var core = require('web.core');
    var relational_fields = require('web.relational_fields');
    var ReconciliationRenderer = require('account.ReconciliationRenderer');
    var ReconciliationModel = require('account.ReconciliationModel');
    var _t = core._t;

    ReconciliationModel.StatementModel.include({

        init: function (parent, options) {
            this._super.apply(this, arguments);
            this.extra_field_names = ['analytic_tag_id'];
            this.extra_fields = [{
                relation: 'account.analytic.tag',
                type: 'many2one',
                name: 'analytic_tag_id',
            }];
            this.extra_fieldInfo = {
                analytic_tag_id: { string: _t("Business Line") },
            };
            this.quickCreateFields = this.quickCreateFields.concat(this.extra_field_names);
        },

        makeRecord: function (model, fields, fieldInfo) {
            var self = this;
            if (model === 'account.bank.statement.line' && fields.length === 6) {
                fields = fields.concat(this.extra_fields);
                _.extend(fieldInfo, this.extra_fieldInfo);
            };
            return this._super(model, fields, fieldInfo);
        },

        _formatToProcessReconciliation: function (line, prop) {
            var result = this._super(line, prop);
            if (prop.analytic_tag_id) result.analytic_tag_ids = [[4, prop.analytic_tag_id.id, null]];
            return result;
        },

        _formatQuickCreate: function (line, values) {
            var prop = this._super(line, values);
            prop.analytic_tag_id = '';
            return prop;
        },

    });

    ReconciliationRenderer.LineRenderer.include({

        _renderCreate: function (state) {
            this._super(state);
            var record = this.model.get(this.handleCreateRecord);
            this.fields.analytic_tag_id = new relational_fields.FieldMany2One(this,
                'analytic_tag_id', record, { mode: 'edit' });
            this.fields.analytic_tag_id.appendTo(this.$el.find('.create_analytic_tag_id .o_td_field'));
        },

    });

});
