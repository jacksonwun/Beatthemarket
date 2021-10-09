from django.contrib import admin
from .models import *

# ? Stock

class hk_stock_Admin(admin.ModelAdmin):
    list_display = ['code']
    search_fields = ['code']
    class Meta:
        model = hk_stock
admin.site.register(hk_stock, hk_stock_Admin)

class hk_stock_timescale_Admin(admin.ModelAdmin):
    list_display = ['code','time']
    search_fields = ['code__code', 'time']
    class Meta:
        model = hk_stock_timescale
admin.site.register(hk_stock_timescale, hk_stock_timescale_Admin)

# ? Warrant

class hk_warrant_Admin(admin.ModelAdmin):
    list_display = ['code']
    search_fields = ['code']
    class Meta:
        model = hk_warrant
admin.site.register(hk_warrant, hk_warrant_Admin)

class hk_warrant_timescale_Admin(admin.ModelAdmin):
    list_display = ['code','time','stock_owner']
    search_fields = ['code__code', 'time','stock_owner__code']
    class Meta:
        model = hk_warrant_timescale
admin.site.register(hk_warrant_timescale, hk_warrant_timescale_Admin)

class warrant_market_closed_Admin(admin.ModelAdmin):
    list_display = ['code','update_timestamp','stock_owner']
    search_fields = ['code','update_timestamp','stock_owner__code']
    class Meta:
        model = warrant_market_closed
admin.site.register(warrant_market_closed, warrant_market_closed_Admin)

class warrant_recommend_Admin(admin.ModelAdmin):
    class Meta:
        model = warrant_recommend
admin.site.register(warrant_recommend, warrant_recommend_Admin)

class warrant_setting_Admin(admin.ModelAdmin):
    class Meta:
        model = warrant_setting
admin.site.register(warrant_setting, warrant_setting_Admin)

# class warrant_transaction_Admin(admin.ModelAdmin):
#     list_display = ['code']
#     class Meta:
#         model = warrant_transaction
# admin.site.register(warrant_transaction, warrant_transaction_Admin)