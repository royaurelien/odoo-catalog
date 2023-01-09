odoo.define('custom_dashboard.dashboard_action', function (require){
    "use strict";
    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var QWeb = core.qweb;
    var rpc = require('web.rpc');
    var ajax = require('web.ajax');
    var CatalogDashBoard = AbstractAction.extend({
       template: 'CatalogDashBoard',
       init: function(parent, context) {
           this._super(parent, context);
           this.dashboards_templates = ['DashboardCatalog'];
           this.today_sale = [];
       },
           willStart: function() {
           var self = this;
           return $.when(ajax.loadLibs(this), this._super()).then(function() {
               return self.fetch_data();
           });
       },
       start: function() {
               var self = this;
               this.set("title", 'Dashboard');
               return this._super().then(function() {
                   self.render_dashboards();
               });
           },
           render_dashboards: function(){
           var self = this;
           _.each(this.dashboards_templates, function(template) {
                   self.$('.o_pj_dashboard').append(QWeb.render(template, {widget: self}));
               });
       },
    fetch_data: function() {
           var self = this;
           var def1 =  this._rpc({
                   model: 'custom.addon',
                   method: 'retrieve_dashboard'
       }).then(function(result)
        {
            self.values = result;
        //   self.total_projects = result['total_projects'],
        //   self.total_tasks = result['total_tasks'],
        //   self.total_employees = result['total_employees']
       });
           return $.when(def1);
       },
    })
    core.action_registry.add('catalog_dashboard_tags', CatalogDashBoard);
    return CatalogDashBoard;
})