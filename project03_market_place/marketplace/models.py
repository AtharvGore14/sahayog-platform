from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
import json

class Commodity(models.Model):
    name = models.CharField(max_length=100, unique=True)
    market_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    # AI Market Analysis Fields
    price_trend = models.CharField(max_length=20, choices=[
        ('RISING', 'Rising'),
        ('FALLING', 'Falling'),
        ('STABLE', 'Stable'),
        ('VOLATILE', 'Volatile')
    ], default='STABLE')
    demand_score = models.FloatField(default=0.5, help_text="AI-calculated demand score (0-1)")
    supply_score = models.FloatField(default=0.5, help_text="AI-calculated supply score (0-1)")
    volatility_index = models.FloatField(default=0.1, help_text="Price volatility (0-1)")
    
    def __str__(self): return self.name
    
    @property
    def ai_suggested_price(self):
        """AI-calculated suggested price based on market conditions"""
        if not self.market_price:
            return Decimal('0')
        
        # Apply AI factors
        trend_multiplier = {
            'RISING': 1.1,
            'FALLING': 0.9,
            'STABLE': 1.0,
            'VOLATILE': 1.05
        }.get(self.price_trend, 1.0)
        
        demand_factor = 0.8 + (self.demand_score * 0.4)  # 0.8-1.2
        supply_factor = 1.2 - (self.supply_score * 0.4)  # 1.2-0.8
        
        suggested = float(self.market_price) * trend_multiplier * demand_factor * supply_factor
        return Decimal(str(round(suggested, 2)))
    
    class Meta: verbose_name_plural = "Commodities"

class SupplyListing(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        LIVE = 'LIVE', 'Live'
        SOLD = 'SOLD', 'Sold'
        EXPIRED = 'EXPIRED', 'Expired'
    
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name="listings")
    commodity = models.ForeignKey(Commodity, on_delete=models.PROTECT)
    quantity_kg = models.DecimalField(max_digits=10, decimal_places=2)
    starting_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quality_score = models.FloatField(default=0.0) # For our AI agent
    image = models.ImageField(upload_to='listings/', null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    auction_ends_at = models.DateTimeField()
    
    # AI-Enhanced Fields
    ai_quality_analysis = models.JSONField(default=dict, blank=True, help_text="AI analysis of image quality")
    ai_suggested_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ai_competitiveness_score = models.FloatField(default=0.0, help_text="AI score for listing competitiveness (0-1)")
    ai_fraud_risk = models.FloatField(default=0.0, help_text="AI-calculated fraud risk (0-1)")
    view_count = models.PositiveIntegerField(default=0)
    interest_score = models.FloatField(default=0.0, help_text="AI-calculated buyer interest score")
    
    def __str__(self): return f"{self.quantity_kg}kg of {self.commodity.name}"
    
    @property
    def ai_optimal_bid_range(self):
        """Calculate AI-optimal bid range for buyers"""
        if not self.ai_suggested_price:
            return {'min': self.starting_price, 'max': self.starting_price * 1.2}
        
        base_price = float(self.ai_suggested_price)
        quality_factor = 0.8 + (self.quality_score * 0.4)  # 0.8-1.2
        competitiveness_factor = 0.9 + (self.ai_competitiveness_score * 0.2)  # 0.9-1.1
        
        min_bid = base_price * quality_factor * competitiveness_factor * 0.95
        max_bid = base_price * quality_factor * competitiveness_factor * 1.15
        
        return {
            'min': Decimal(str(round(min_bid, 2))),
            'max': Decimal(str(round(max_bid, 2))),
            'recommended': Decimal(str(round(base_price * quality_factor * competitiveness_factor, 2)))
        }
    
    @property
    def time_remaining_seconds(self):
        """Calculate seconds remaining in auction"""
        remaining = self.auction_ends_at - timezone.now()
        return max(0, int(remaining.total_seconds()))
    
    @property
    def urgency_factor(self):
        """Calculate auction urgency for AI pricing"""
        if self.time_remaining_seconds < 3600:  # Less than 1 hour
            return 1.2
        elif self.time_remaining_seconds < 86400:  # Less than 1 day
            return 1.1
        else:
            return 1.0

    def save(self, *args, **kwargs):
        # Defensive default to avoid NULL inserts
        if self.starting_price in (None, ''):
            from decimal import Decimal
            fallback = getattr(self.commodity, 'market_price', None)
            self.starting_price = Decimal(str(fallback)) if fallback is not None else Decimal('0')
        super().save(*args, **kwargs)

class Bid(models.Model):
    listing = models.ForeignKey(SupplyListing, on_delete=models.CASCADE, related_name='bids')
    bidder = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bids')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # AI-Enhanced Bid Analysis
    ai_bid_confidence = models.FloatField(default=0.0, help_text="AI confidence in bid success (0-1)")
    ai_bid_strategy = models.CharField(max_length=20, choices=[
        ('AGGRESSIVE', 'Aggressive'),
        ('CONSERVATIVE', 'Conservative'),
        ('OPTIMAL', 'Optimal'),
        ('SNIPE', 'Last-minute snipe')
    ], default='OPTIMAL')
    ai_success_probability = models.FloatField(default=0.0, help_text="AI-calculated success probability")
    
    def clean(self):
        if self.bidder == self.listing.seller: 
            raise ValidationError("You cannot bid on your own listing.")
    
    @property
    def is_winning_bid(self):
        """Check if this is currently the highest bid"""
        return self == self.listing.bids.first()
    
    @property
    def bid_competitiveness(self):
        """Calculate how competitive this bid is"""
        if not self.listing.bids.count() > 1:
            return 1.0
        
        highest_amount = float(self.listing.bids.first().amount)
        my_amount = float(self.amount)
        
        if highest_amount == 0:
            return 1.0
        
        return my_amount / highest_amount
    
    class Meta:
        unique_together = ('listing', 'bidder')
        ordering = ['-amount']

class Deal(models.Model):
    listing = models.OneToOneField(SupplyListing, on_delete=models.CASCADE)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchases')
    final_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"Deal for {self.listing.commodity.name} won by {self.buyer.username}"

class UserProfile(models.Model):
    USER_TYPE_CHOICES = (("seller", "Seller"), ("buyer", "Buyer"))
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    
    # AI-Enhanced User Analytics
    ai_trust_score = models.FloatField(default=0.5, help_text="AI-calculated user trustworthiness (0-1)")
    ai_success_rate = models.FloatField(default=0.0, help_text="AI-calculated transaction success rate")
    ai_behavior_score = models.FloatField(default=0.5, help_text="AI-calculated behavior pattern score")
    preferred_bid_strategy = models.CharField(max_length=20, choices=[
        ('AGGRESSIVE', 'Aggressive'),
        ('CONSERVATIVE', 'Conservative'),
        ('OPTIMAL', 'Optimal'),
        ('SNIPE', 'Last-minute snipe')
    ], default='OPTIMAL')
    
    def __str__(self): return f"{self.user.username} - {self.user_type}"


class MarketAnalytics(models.Model):
    """AI-powered market analytics and insights"""
    commodity = models.ForeignKey(Commodity, on_delete=models.CASCADE, related_name='analytics')
    date = models.DateField(auto_now_add=True)
    
    # Market Intelligence
    average_price = models.DecimalField(max_digits=10, decimal_places=2)
    price_volatility = models.FloatField(default=0.0)
    demand_trend = models.CharField(max_length=20, choices=[
        ('INCREASING', 'Increasing'),
        ('DECREASING', 'Decreasing'),
        ('STABLE', 'Stable')
    ])
    supply_level = models.CharField(max_length=20, choices=[
        ('HIGH', 'High'),
        ('MEDIUM', 'Medium'),
        ('LOW', 'Low')
    ])
    
    # AI Predictions
    predicted_price_7d = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    predicted_price_30d = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    market_sentiment = models.CharField(max_length=20, choices=[
        ('BULLISH', 'Bullish'),
        ('BEARISH', 'Bearish'),
        ('NEUTRAL', 'Neutral')
    ], default='NEUTRAL')
    
    # Trading Insights
    best_buy_time = models.CharField(max_length=50, default="Anytime")
    optimal_bid_range = models.JSONField(default=dict)
    
    class Meta:
        unique_together = ('commodity', 'date')
        ordering = ['-date']


class AIRecommendation(models.Model):
    """AI-generated recommendations for users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_recommendations')
    listing = models.ForeignKey(SupplyListing, on_delete=models.CASCADE, related_name='ai_recommendations')
    recommendation_type = models.CharField(max_length=30, choices=[
        ('BID_NOW', 'Bid Now'),
        ('WATCH', 'Watch'),
        ('AVOID', 'Avoid'),
        ('SNIPE', 'Last-minute Bid'),
        ('HIGH_VALUE', 'High Value Opportunity')
    ])
    
    confidence_score = models.FloatField(default=0.0, help_text="AI confidence in recommendation (0-1)")
    reason = models.TextField(help_text="AI explanation for recommendation")
    suggested_bid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'listing')
        ordering = ['-confidence_score']


class Notification(models.Model):
    """Advanced notification system"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=[
        ('BID_PLACED', 'Bid Placed'),
        ('BID_OUTBID', 'Bid Outbid'),
        ('AUCTION_ENDING', 'Auction Ending Soon'),
        ('AUCTION_WON', 'Auction Won'),
        ('AUCTION_LOST', 'Auction Lost'),
        ('PRICE_ALERT', 'Price Alert'),
        ('NEW_LISTING', 'New Listing Match'),
        ('AI_INSIGHT', 'AI Market Insight')
    ])
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Related objects
    listing = models.ForeignKey(SupplyListing, on_delete=models.CASCADE, null=True, blank=True)
    bid = models.ForeignKey(Bid, on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']