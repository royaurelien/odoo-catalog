# -*- coding: utf-8 -*-
# from odoo import http


# class ApikAddons(http.Controller):
#     @http.route('/apik_addons/apik_addons/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/apik_addons/apik_addons/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('apik_addons.listing', {
#             'root': '/apik_addons/apik_addons',
#             'objects': http.request.env['apik_addons.apik_addons'].search([]),
#         })

#     @http.route('/apik_addons/apik_addons/objects/<model("apik_addons.apik_addons"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('apik_addons.object', {
#             'object': obj
#         })
