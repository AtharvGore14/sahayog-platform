#!/usr/bin/env python
"""
Populate Sahayog Marketplace with exciting sample data
"""
import os
import sys
import django
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
import random

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sahayog_marketplace.settings')
django.setup()

from django.contrib.auth.models import User, Group
from marketplace.models import (
    Commodity, SupplyListing, Bid, UserProfile,
    MarketAnalytics, AIRecommendation, Notification
)

def create_sample_data():
    print("Creating CRAZY PROFESSIONAL marketplace data...")
    
    # Create user groups
    seller_group, _ = Group.objects.get_or_create(name='seller')
    buyer_group, _ = Group.objects.get_or_create(name='buyer')
    
    # Create commodities with AI-enhanced data
    commodities_data = [
        {
            'name': 'High-Quality Cardboard',
            'market_price': Decimal('12.50'),
            'price_trend': 'RISING',
            'demand_score': 0.85,
            'supply_score': 0.60,
            'volatility_index': 0.15
        },
        {
            'name': 'Premium Paper',
            'market_price': Decimal('18.75'),
            'price_trend': 'STABLE',
            'demand_score': 0.75,
            'supply_score': 0.70,
            'volatility_index': 0.10
        },
        {
            'name': 'Recycled Plastic',
            'market_price': Decimal('25.30'),
            'price_trend': 'VOLATILE',
            'demand_score': 0.90,
            'supply_score': 0.45,
            'volatility_index': 0.25
        },
        {
            'name': 'Aluminum Cans',
            'market_price': Decimal('35.80'),
            'price_trend': 'RISING',
            'demand_score': 0.80,
            'supply_score': 0.55,
            'volatility_index': 0.20
        },
        {
            'name': 'Steel Scrap',
            'market_price': Decimal('42.15'),
            'price_trend': 'FALLING',
            'demand_score': 0.65,
            'supply_score': 0.80,
            'volatility_index': 0.18
        }
    ]
    
    commodities = []
    for data in commodities_data:
        commodity, created = Commodity.objects.get_or_create(
            name=data['name'],
            defaults=data
        )
        commodities.append(commodity)
        print(f"Created commodity: {commodity.name}")
    
    # Create sample users
    users_data = [
        {'username': 'eco_seller', 'user_type': 'seller'},
        {'username': 'green_recycler', 'user_type': 'buyer'},
        {'username': 'waste_warrior', 'user_type': 'seller'},
        {'username': 'circular_buyer', 'user_type': 'buyer'},
        {'username': 'sustainable_seller', 'user_type': 'seller'},
    ]
    
    users = []
    for data in users_data:
        user, created = User.objects.get_or_create(
            username=data['username'],
            defaults={'email': f"{data['username']}@sahayog.com"}
        )
        if created:
            user.set_password('demo123')
            user.save()
        
        # Create profile
        profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'user_type': data['user_type'],
                'ai_trust_score': random.uniform(0.7, 0.95),
                'ai_success_rate': random.uniform(0.6, 0.9),
                'ai_behavior_score': random.uniform(0.8, 0.95),
                'preferred_bid_strategy': random.choice(['AGGRESSIVE', 'CONSERVATIVE', 'OPTIMAL', 'SNIPE'])
            }
        )
        
        # Add to group
        group = seller_group if data['user_type'] == 'seller' else buyer_group
        user.groups.add(group)
        
        users.append(user)
        print(f"Created user: {user.username} ({data['user_type']})")
    
    # Create exciting listings
    sellers = [u for u in users if u.profile.user_type == 'seller']
    buyers = [u for u in users if u.profile.user_type == 'buyer']
    
    listings_data = [
        {
            'commodity': commodities[0],
            'quantity_kg': Decimal('500.0'),
            'quality_score': 0.92,
            'starting_price': Decimal('11.50'),
            'auction_ends_at': timezone.now() + timedelta(hours=2),
            'ai_competitiveness_score': 0.88,
            'ai_fraud_risk': 0.02
        },
        {
            'commodity': commodities[1],
            'quantity_kg': Decimal('750.0'),
            'quality_score': 0.85,
            'starting_price': Decimal('17.25'),
            'auction_ends_at': timezone.now() + timedelta(hours=6),
            'ai_competitiveness_score': 0.75,
            'ai_fraud_risk': 0.05
        },
        {
            'commodity': commodities[2],
            'quantity_kg': Decimal('300.0'),
            'quality_score': 0.95,
            'starting_price': Decimal('24.80'),
            'auction_ends_at': timezone.now() + timedelta(hours=1),
            'ai_competitiveness_score': 0.95,
            'ai_fraud_risk': 0.01
        },
        {
            'commodity': commodities[3],
            'quantity_kg': Decimal('200.0'),
            'quality_score': 0.88,
            'starting_price': Decimal('33.50'),
            'auction_ends_at': timezone.now() + timedelta(hours=4),
            'ai_competitiveness_score': 0.82,
            'ai_fraud_risk': 0.03
        },
        {
            'commodity': commodities[4],
            'quantity_kg': Decimal('1000.0'),
            'quality_score': 0.78,
            'starting_price': Decimal('40.00'),
            'auction_ends_at': timezone.now() + timedelta(hours=8),
            'ai_competitiveness_score': 0.70,
            'ai_fraud_risk': 0.08
        }
    ]
    
    listings = []
    for i, data in enumerate(listings_data):
        seller = sellers[i % len(sellers)]
        listing = SupplyListing.objects.create(
            seller=seller,
            status='LIVE',
            **data
        )
        
        # Calculate AI suggested price
        if listing.commodity.market_price:
            quality_multiplier = 0.8 + (listing.quality_score * 0.4)
            suggested_price = float(listing.commodity.market_price) * quality_multiplier
            listing.ai_suggested_price = Decimal(str(round(suggested_price, 2)))
            listing.save()
        
        listings.append(listing)
        print(f"Created listing: {listing.commodity.name} by {listing.seller.username}")
    
    # Create exciting bids
    for listing in listings[:3]:  # Add bids to first 3 listings
        used_buyers = set()
        num_bids = min(random.randint(2, 4), len(buyers))  # Don't exceed number of buyers
        for i in range(num_bids):
            available_buyers = [b for b in buyers if b not in used_buyers]
            if not available_buyers:
                break
            buyer = random.choice(available_buyers)
            used_buyers.add(buyer)
            
            base_amount = float(listing.starting_price)
            bid_amount = base_amount * random.uniform(1.05, 1.25)
            
            bid, created = Bid.objects.get_or_create(
                listing=listing,
                bidder=buyer,
                defaults={
                    'amount': Decimal(str(round(bid_amount, 2))),
                    'ai_bid_confidence': random.uniform(0.7, 0.95),
                    'ai_bid_strategy': random.choice(['AGGRESSIVE', 'OPTIMAL', 'CONSERVATIVE']),
                    'ai_success_probability': random.uniform(0.6, 0.9)
                }
            )
            if created:
                print(f"Created bid: Rs{bid.amount} by {bid.bidder.username}")
    
    # Create market analytics
    for commodity in commodities:
        analytics = MarketAnalytics.objects.create(
            commodity=commodity,
            average_price=commodity.market_price,
            price_volatility=commodity.volatility_index,
            demand_trend=commodity.price_trend,
            supply_level='HIGH' if commodity.supply_score > 0.7 else 'MEDIUM' if commodity.supply_score > 0.4 else 'LOW',
            predicted_price_7d=commodity.market_price * Decimal('1.05'),
            predicted_price_30d=commodity.market_price * Decimal('1.10'),
            market_sentiment='BULLISH' if commodity.demand_score > 0.8 else 'BEARISH' if commodity.demand_score < 0.6 else 'NEUTRAL',
            best_buy_time="Early morning" if commodity.supply_score > 0.7 else "Evening",
            optimal_bid_range={
                'min': round(float(commodity.market_price) * 0.95, 2),
                'max': round(float(commodity.market_price) * 1.15, 2),
                'recommended': round(float(commodity.market_price) * 1.02, 2)
            }
        )
        print(f"Created analytics for {commodity.name}")
    
    # Create AI recommendations
    for buyer in buyers:
        for listing in listings[:2]:  # Recommend first 2 listings
            recommendation = AIRecommendation.objects.create(
                user=buyer,
                listing=listing,
                recommendation_type=random.choice(['BID_NOW', 'WATCH', 'HIGH_VALUE']),
                confidence_score=random.uniform(0.7, 0.95),
                reason=f"High quality {listing.commodity.name} with competitive pricing. AI confidence: {random.randint(75, 95)}%",
                suggested_bid=listing.ai_suggested_price or listing.starting_price
            )
            print(f"Created recommendation for {buyer.username}: {listing.commodity.name}")
    
    # Create notifications
    notification_types = [
        ('BID_PLACED', 'New Bid Placed', 'Someone placed a bid on your listing!'),
        ('AUCTION_ENDING', 'Auction Ending Soon', 'Your auction ends in 30 minutes!'),
        ('AI_INSIGHT', 'AI Market Insight', 'New market opportunities detected!'),
        ('PRICE_ALERT', 'Price Alert', 'Commodity prices have changed significantly!'),
    ]
    
    for user in users:
        for i in range(random.randint(2, 4)):
            notif_type, title, message = random.choice(notification_types)
            listing = random.choice(listings) if notif_type in ['BID_PLACED', 'AUCTION_ENDING'] else None
            
            Notification.objects.create(
                user=user,
                notification_type=notif_type,
                title=title,
                message=message,
                listing=listing,
                is_read=random.choice([True, False])
            )
        print(f"Created notifications for {user.username}")
    
    print("\nCRAZY PROFESSIONAL MARKETPLACE DATA CREATED!")
    print("=" * 50)
    print("Summary:")
    print(f"   - {len(commodities)} AI-enhanced commodities")
    print(f"   - {len(users)} professional users")
    print(f"   - {len(listings)} live auction listings")
    print(f"   - {Bid.objects.count()} competitive bids")
    print(f"   - {MarketAnalytics.objects.count()} market analytics")
    print(f"   - {AIRecommendation.objects.count()} AI recommendations")
    print(f"   - {Notification.objects.count()} notifications")
    print("\nYour marketplace is ready to rock!")

if __name__ == '__main__':
    create_sample_data()
