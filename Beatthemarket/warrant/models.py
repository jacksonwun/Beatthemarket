from django.db import models
from django.conf import settings
from django.forms.models import model_to_dict
from django.db.models import Q

from timescale.db.models.fields import TimescaleDateTimeField
from timescale.db.models.managers import TimescaleManager
from timescale.db.models.models import TimescaleModel

# ? HK Stock Related

class hk_stock_timescale_manager(models.Manager):
    def update(self, **kwargs):
        print(**kwargs)

class hk_stock_timescale(models.Model): # Source: get_cur_kline
    time                    = TimescaleDateTimeField(interval="1 min")
    code                    = models.ForeignKey('hk_stock', on_delete=models.PROTECT)
    # Price Related
    last_price              = models.FloatField(null=True)
    open_price              = models.FloatField(null=True)
    high_price              = models.FloatField(null=True)
    low_price               = models.FloatField(null=True)
    price_spread            = models.FloatField(null=True)
    # Volume Related
    volume                  = models.PositiveBigIntegerField(null=True)  
    turnover                = models.PositiveBigIntegerField(null=True)  
    turnover_rate           = models.FloatField(null=True)
    amplitude               = models.FloatField(null=True)
    # Capital Flow
    # ask_price               = models.FloatField(null=True, default=None)
    # bid_price               = models.FloatField(null=True, default=None)
    # ask_vol                 = models.FloatField(null=True, default=None)
    # bid_vol                 = models.FloatField(null=True, default=None)

    technical_analysis      = models.JSONField(blank=True, null=True, default=None)

    objects = hk_stock_timescale_manager()
    timescale = TimescaleManager()

    class Meta:
        pass

class hk_stock_Manager(models.Manager):
    def check_message_mid(self, audience_id, message_mid):
        qs = hk_stock.objects.filter(audience_id=audience_id, message_mid=message_mid)
        if not qs:
            return True
        else:
            return False
    def all_list(self) -> list:
        all_list = hk_stock.objects.all().values_list('code')
        all_list = [i[0] for i in all_list]
        return all_list
    def all_with_warrant_list(self) -> list:
        all_list = list(hk_stock.objects.filter(include_warrant=True).values_list('code'))
        all_list = [i[0] for i in all_list]
        all_list = [i for i in all_list if i]
        return all_list

class hk_stock(models.Model):
    code               = models.CharField(max_length=7, blank=False, primary_key = True)
    include_warrant    = models.BooleanField(default=True)
    include_call       = models.IntegerField(null=True, default=None, blank=True)
    include_put        = models.IntegerField(null=True, default=None, blank=True)
    include_bull       = models.IntegerField(null=True, default=None, blank=True)
    include_bear       = models.IntegerField(null=True, default=None, blank=True)

    objects = hk_stock_Manager()

# ? HK Warrant Related

class hk_warrant_timescale(models.Model): # Source: get_market_snapshot
    time                    = TimescaleDateTimeField(interval="1 min")
    update_time             = models.DateField(auto_now=False, auto_now_add=False, null=True)

    # Warrant Snapshot
    code                    = models.ForeignKey('hk_warrant', on_delete=models.CASCADE)
    bid_price               = models.FloatField(null=True, default=None)    
    ask_price               = models.FloatField(null=True, default=None)
    bid_vol                 = models.FloatField(null=True, default=None)
    ask_vol                 = models.FloatField(null=True, default=None)
    price_spread            = models.FloatField(null=True, default=None)
    wrt_sensitivity         = models.FloatField(null=True, default=None)

    # Stock Snapshot
    stock_owner             = models.ForeignKey('hk_stock', on_delete=models.CASCADE)
    stock_bid_price         = models.FloatField(null=True, default=None)    
    stock_ask_price         = models.FloatField(null=True, default=None)
    stock_bid_vol           = models.FloatField(null=True, default=None)
    stock_ask_vol           = models.FloatField(null=True, default=None)
    stock_price_spread      = models.FloatField(null=True, default=None)

    objects = models.Manager()
    timescale = TimescaleManager()

    class Meta:
        pass

class hk_warrant_Manager(models.Manager):
    def all_list(self):
        all_list = hk_warrant.objects.all().values_list('code')
        all_list = [i[0] for i in all_list]
        return all_list
    def all_status_list(self):
        all_list = hk_warrant.objects.filter(~Q(wrt_status= 'NORMAL'))
        all_list = [i[0] for i in all_list]
        return all_list

class hk_warrant(models.Model):
    code                    = models.CharField(max_length=7, blank=False, primary_key = True)
    name                    = models.CharField(max_length=63, null=True, default=None)  
    stock_owner             = models.ForeignKey('hk_stock', on_delete=models.CASCADE, default=None, null=True)
    # Status Related
    wrt_status              = models.CharField(max_length=31, null=True)
    wrt_strike_price        = models.FloatField(null=True)
    wrt_conversion_ratio    = models.FloatField(null=True)
    wrt_type                = models.CharField(max_length=7, null=True)
    wrt_issuer_code         = models.CharField(max_length=7, null=True)
    # Date Related
    listing_date            = models.DateField(auto_now=False, auto_now_add=False, null=True)
    wrt_maturity_date       = models.DateField(auto_now=False, auto_now_add=False, null=True)
    wrt_end_trade           = models.DateField(auto_now=False, auto_now_add=False, null=True)

    objects = hk_warrant_Manager()

class warrant_market_closed_Manager(models.Manager):
    def get_volume(self, code ,time__range):
        qs = warrant_market_closed.objects.filter(code=code, update_timestamp__range=time__range).last()
        return model_to_dict(qs)['volume']

class warrant_market_closed(models.Model): # Source: get_market_snapshot
    code                    = models.CharField(max_length=7, blank=False)
    update_timestamp        = models.DateField(auto_now=False, auto_now_add=False)
    name                    = models.CharField(max_length=63, blank=False)    
    stock_owner             = models.ForeignKey('hk_stock', on_delete=models.CASCADE)
    # Price Related
    last_price              = models.FloatField(null=True)
    open_price              = models.FloatField(null=True)
    high_price              = models.FloatField(null=True)
    low_price               = models.FloatField(null=True)
    prev_close_price        = models.FloatField(null=True)
    price_spread            = models.FloatField(null=True)
    wrt_strike_price        = models.FloatField(null=True)
    wrt_break_even_point    = models.FloatField(null=True)
    wrt_conversion_price    = models.FloatField(null=True)
    # Volume Related
    volume                  = models.PositiveBigIntegerField(null=True)  
    wrt_street_vol          = models.PositiveBigIntegerField(null=True)  
    wrt_issue_vol           = models.PositiveBigIntegerField(null=True)  
    wrt_street_ratio        = models.FloatField(null=True)
    # Date Related
    listing_date            = models.DateField(auto_now=False, auto_now_add=False, null=True)
    wrt_maturity_date       = models.DateField(auto_now=False, auto_now_add=False, null=True)
    wrt_end_trade           = models.DateField(auto_now=False, auto_now_add=False, null=True)
    # Status Related
    wrt_status              = models.CharField(max_length=31, null=True)
    wrt_conversion_ratio    = models.FloatField(null=True)
    wrt_type                = models.CharField(max_length=7, null=True)
    wrt_issuer_code         = models.CharField(max_length=7, null=True)
    # Wrt Static
    wrt_delta               = models.FloatField(null=True)
    wrt_implied_volatility  = models.FloatField(null=True)
    wrt_premium             = models.FloatField(null=True)
    wrt_leverage            = models.FloatField(null=True)
    wrt_ipop                = models.FloatField(null=True)
    wrt_score               = models.FloatField(null=True)

    wrt_transaction         = models.JSONField(blank=True, null=True, default=None)

    objects = warrant_market_closed_Manager()

    class Meta:
        db_table = "warrant_market_closed"

class warrant_recommend_Manager(models.Manager):
    def get_latest(self) -> dict:
        qs = warrant_recommend.objects.filter().last()
        return qs.output_dict

class warrant_recommend(models.Model):
    output_dict             = models.JSONField(blank=True, null=True, default=None)

    objects = warrant_recommend_Manager()

class warrant_setting_Manager(models.Manager):
    def get(self):
        qs = warrant_setting.objects.filter().last()
        return model_to_dict( qs )

class warrant_setting(models.Model):
    settings                 = models.JSONField(blank=True, null=True, default=None)

    objects = warrant_setting_Manager()