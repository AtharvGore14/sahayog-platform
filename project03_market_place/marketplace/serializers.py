from rest_framework import serializers
from decimal import Decimal
from .models import (
    SupplyListing, Bid, Commodity, UserProfile, 
    MarketAnalytics, AIRecommendation, Notification
)
from django.contrib.auth.models import User, Group
from django.db import transaction

class UserProfileSerializer(serializers.ModelSerializer):
    ai_trust_score = serializers.ReadOnlyField()
    ai_success_rate = serializers.ReadOnlyField()
    preferred_bid_strategy = serializers.ReadOnlyField()
    
    class Meta:
        model = UserProfile
        fields = ('user_type', 'ai_trust_score', 'ai_success_rate', 'preferred_bid_strategy')

class UserSerializer(serializers.ModelSerializer):
    user_type = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'user_type')
        extra_kwargs = {'password': {'write_only': True}}

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("A user with that username already exists.")
        return value
    
    def validate_user_type(self, value):
        if value not in ['seller', 'buyer']:
            raise serializers.ValidationError("User type must be either 'seller' or 'buyer'.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        user_type = validated_data.pop('user_type')
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password']
        )
        UserProfile.objects.create(user=user, user_type=user_type)
        try:
            group, _ = Group.objects.get_or_create(name=user_type)
            user.groups.add(group)
        except Exception as e:
            print(f"Warning: Could not add user to group. Error: {e}")
        return user

class BidSerializer(serializers.ModelSerializer):
    bidder_username = serializers.CharField(source='bidder.username', read_only=True)
    ai_bid_confidence = serializers.ReadOnlyField()
    ai_bid_strategy = serializers.ReadOnlyField()
    ai_success_probability = serializers.ReadOnlyField()
    is_winning_bid = serializers.ReadOnlyField()
    bid_competitiveness = serializers.ReadOnlyField()
    
    class Meta:
        model = Bid
        fields = [
            'id', 'listing', 'bidder', 'bidder_username', 'amount', 'timestamp',
            'ai_bid_confidence', 'ai_bid_strategy', 'ai_success_probability',
            'is_winning_bid', 'bid_competitiveness'
        ]
        read_only_fields = ['bidder']

    def create(self, validated_data):
        # Validate positive and higher-than-current bid
        listing = validated_data.get('listing')
        amount = validated_data.get('amount')
        if amount is None or amount <= 0:
            raise serializers.ValidationError({"amount": "Bid amount must be greater than 0."})
        current = listing.bids.order_by('-amount').first()
        if current and amount <= current.amount:
            raise serializers.ValidationError({"amount": f"Bid must be greater than current highest ({current.amount})."})
        bid, created = Bid.objects.update_or_create(
            listing=validated_data.get('listing'),
            bidder=validated_data.get('bidder'),
            defaults={'amount': validated_data.get('amount')}
        )
        
        # Trigger AI analysis of the bid
        from .tasks import analyze_bid_competitiveness
        analyze_bid_competitiveness.delay(bid.id)
        
        return bid

class CommoditySerializer(serializers.ModelSerializer):
    ai_suggested_price = serializers.ReadOnlyField()
    price_trend = serializers.ReadOnlyField()
    demand_score = serializers.ReadOnlyField()
    supply_score = serializers.ReadOnlyField()
    volatility_index = serializers.ReadOnlyField()
    
    class Meta:
        model = Commodity
        fields = [
            'id', 'name', 'market_price', 'last_updated',
            'ai_suggested_price', 'price_trend', 'demand_score',
            'supply_score', 'volatility_index'
        ]


# New AI-Enhanced Serializers


class ListingSerializer(serializers.ModelSerializer):
    bids = BidSerializer(many=True, read_only=True)
    seller_username = serializers.CharField(source='seller.username', read_only=True)
    commodity_name = serializers.CharField(source='commodity.name', read_only=True)
    commodity_details = CommoditySerializer(source='commodity', read_only=True)
    image = serializers.ImageField(required=False, allow_null=True)
    primary_image_url = serializers.SerializerMethodField()
    seller = serializers.PrimaryKeyRelatedField(read_only=True)
    starting_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    highest_bid_amount = serializers.SerializerMethodField()

    # AI-Enhanced Fields
    ai_quality_analysis = serializers.ReadOnlyField()
    ai_suggested_price = serializers.ReadOnlyField()
    ai_competitiveness_score = serializers.ReadOnlyField()
    ai_optimal_bid_range = serializers.ReadOnlyField()
    time_remaining_seconds = serializers.ReadOnlyField()
    urgency_factor = serializers.ReadOnlyField()
    view_count = serializers.ReadOnlyField()
    interest_score = serializers.ReadOnlyField()

    class Meta:
        model = SupplyListing
        fields = '__all__'

    def get_primary_image_url(self, obj):
        request = self.context.get('request')
        if obj.image:
            image_url = obj.image.url
            if request is not None:
                return request.build_absolute_uri(image_url)
            return image_url
        return None

    def get_highest_bid_amount(self, obj):
        winning = obj.bids.first()
        if winning:
            return Decimal(winning.amount)
        return Decimal(obj.starting_price)

    def validate(self, attrs):
        starting_price = attrs.get('starting_price')
        if starting_price in (None, ""):
            commodity = attrs.get('commodity')
            if commodity and commodity.market_price is not None:
                attrs['starting_price'] = Decimal(str(commodity.market_price))
            else:
                attrs['starting_price'] = Decimal('0')
        return attrs

    def create(self, validated_data):
        commodity = validated_data.get('commodity')
        starting_price = validated_data.get('starting_price')
        if starting_price in (None, ""):
            if commodity and commodity.market_price is not None:
                validated_data['starting_price'] = Decimal(str(commodity.market_price))
            else:
                validated_data['starting_price'] = Decimal('0')

        listing = super().create(validated_data)

        # Trigger AI analysis if image is uploaded
        if listing.image:
            from .tasks import analyze_listing_quality
            analyze_listing_quality.delay(listing.id)

        return listing

class MarketAnalyticsSerializer(serializers.ModelSerializer):
    commodity_name = serializers.CharField(source='commodity.name', read_only=True)
    
    class Meta:
        model = MarketAnalytics
        fields = '__all__'


class AIRecommendationSerializer(serializers.ModelSerializer):
    listing_title = serializers.CharField(source='listing.commodity.name', read_only=True)
    listing_quantity = serializers.DecimalField(source='listing.quantity_kg', max_digits=10, decimal_places=2, read_only=True)
    listing_quality = serializers.FloatField(source='listing.quality_score', read_only=True)
    
    class Meta:
        model = AIRecommendation
        fields = '__all__'


class NotificationSerializer(serializers.ModelSerializer):
    listing_title = serializers.CharField(source='listing.commodity.name', read_only=True)
    
    class Meta:
        model = Notification
        fields = '__all__'