from rest_framework import serializers
from warrant.models import warrant_market_closed #, #warrant_transaction


class warrant_market_closed_Serializer(serializers.ModelSerializer):
    class Meta:
        model = warrant_market_closed
        fields = '__all__'
        # fields = ('id', 'song', 'singer', 'last_modify_date', 'created')

# class warrant_transaction_Serializer(serializers.ModelSerializer):
#     class Meta:
#         model = warrant_transaction
#         fields = '__all__'
#         # fields = ('id', 'song', 'singer', 'last_modify_date', 'created')