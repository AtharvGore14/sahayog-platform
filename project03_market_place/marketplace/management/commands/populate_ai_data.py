from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from marketplace.models import (
    Commodity, SupplyListing, Bid, UserProfile,
    MarketAnalytics, AIRecommendation, Notification
)
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
import random

class Command(BaseCommand):
    help = 'Populate database with AI-enhanced sample data'

    def handle(self, *args, **options):
        self.stdout.write('Creating AI-enhanced sample data...')
        
        # Create commodities with AI data
        commodities_data = [
            {'name': 'Cardboard', 'market_price': 15.50},
            {'name': 'Paper', 'market_price': 18.75},
            {'name': 'Plastic', 'market_price': 12.30},
            {'name': 'Metal', 'market_price': 25.80},
            {'name': 'Glass', 'market_price': 8.90},
            {'name': 'Electronics', 'market_price': 45.60},
        ]
        
        commodities = []
        for data in commodities_data:
            commodity, created = Commodity.objects.get_or_create(
                name=data['name'],
                defaults={
                    'market_price': Decimal(str(data['market_price'])),
                    'price_trend': random.choice(['RISING', 'FALLING', 'STABLE', 'VOLATILE']),
                    'demand_score': random.uniform(0.3, 0.9),
                    'supply_score': random.uniform(0.4, 0.8),
                    'volatility_index': random.uniform(0.05, 0.3),
                }
            )
            commodities.append(commodity)
            if created:
                self.stdout.write(f'Created commodity: {commodity.name}')
        
        # Create users with profiles
        users_data = [
            {'username': 'seller1', 'user_type': 'seller'},
            {'username': 'seller2', 'user_type': 'seller'},
            {'username': 'buyer1', 'user_type': 'buyer'},
            {'username': 'buyer2', 'user_type': 'buyer'},
            {'username': 'buyer3', 'user_type': 'buyer'},
        ]
        
        users = []
        for data in users_data:
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={'password': 'pbkdf2_sha256$260000$test$test'}
            )
            if created:
                user.set_password('password123')
                user.save()
                
                profile, _ = UserProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'user_type': data['user_type'],
                        'ai_trust_score': random.uniform(0.6, 0.95),
                        'ai_success_rate': random.uniform(0.3, 0.8),
                        'ai_behavior_score': random.uniform(0.5, 0.9),
                        'preferred_bid_strategy': random.choice(['AGGRESSIVE', 'CONSERVATIVE', 'OPTIMAL', 'SNIPE']),
                    }
                )
            else:
                profile, _ = UserProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'user_type': data['user_type'],
                        'ai_trust_score': random.uniform(0.6, 0.95),
                        'ai_success_rate': random.uniform(0.3, 0.8),
                        'ai_behavior_score': random.uniform(0.5, 0.9),
                        'preferred_bid_strategy': random.choice(['AGGRESSIVE', 'CONSERVATIVE', 'OPTIMAL', 'SNIPE']),
                    }
                )
            
            users.append(user)
            if created:
                self.stdout.write(f'Created user: {user.username}')
        
        # Create sample listings with AI analysis
        sellers = [u for u in users if u.profile.user_type == 'seller']
        buyers = [u for u in users if u.profile.user_type == 'buyer']
        
        listings = []
        for i in range(10):
            seller = random.choice(sellers)
            commodity = random.choice(commodities)
            quantity = Decimal(str(random.uniform(50, 500)))
            
            # AI-enhanced listing data
            quality_score = random.uniform(0.3, 0.95)
            ai_quality_analysis = {
                'clarity': random.uniform(0.7, 0.95),
                'lighting': random.uniform(0.6, 0.9),
                'angle': random.uniform(0.8, 0.95),
                'material_visibility': random.uniform(0.7, 0.9),
                'contamination_detected': random.choice([True, False])
            }
            
            # Calculate AI suggested price
            base_price = float(commodity.market_price)
            quality_multiplier = 0.8 + (quality_score * 0.4)
            ai_suggested_price = Decimal(str(round(base_price * quality_multiplier, 2)))
            
            listing = SupplyListing.objects.create(
                seller=seller,
                commodity=commodity,
                quantity_kg=quantity,
                starting_price=ai_suggested_price * Decimal('0.9'),  # Start 10% below AI price
                quality_score=quality_score,
                ai_quality_analysis=ai_quality_analysis,
                ai_suggested_price=ai_suggested_price,
                ai_competitiveness_score=random.uniform(0.4, 0.9),
                ai_fraud_risk=0.1 if ai_quality_analysis['contamination_detected'] else 0.05,
                status='LIVE',
                auction_ends_at=timezone.now() + timedelta(hours=random.randint(1, 72)),
                view_count=random.randint(0, 50),
                interest_score=random.uniform(0.2, 0.8),
            )
            listings.append(listing)
            self.stdout.write(f'Created listing: {listing.commodity.name} by {seller.username}')
        
        # Create sample bids with AI analysis
        for i in range(15):
            listing = random.choice(listings)
            bidder = random.choice(buyers)
            
            # Ensure bidder doesn't already have a bid on this listing
            if Bid.objects.filter(listing=listing, bidder=bidder).exists():
                continue
            
            # Create realistic bid amounts
            base_amount = float(listing.ai_suggested_price or listing.starting_price)
            bid_amount = Decimal(str(round(base_amount * random.uniform(0.95, 1.15), 2)))
            
            bid = Bid.objects.create(
                listing=listing,
                bidder=bidder,
                amount=bid_amount,
                ai_bid_confidence=random.uniform(0.4, 0.9),
                ai_bid_strategy=random.choice(['AGGRESSIVE', 'CONSERVATIVE', 'OPTIMAL', 'SNIPE']),
                ai_success_probability=random.uniform(0.3, 0.8),
            )
            self.stdout.write(f'Created bid: ₹{bid_amount} by {bidder.username}')
        
        # Create market analytics
        for commodity in commodities:
            MarketAnalytics.objects.create(
                commodity=commodity,
                average_price=commodity.market_price,
                price_volatility=random.uniform(0.05, 0.25),
                demand_trend=random.choice(['INCREASING', 'DECREASING', 'STABLE']),
                supply_level=random.choice(['HIGH', 'MEDIUM', 'LOW']),
                predicted_price_7d=commodity.market_price * Decimal('1.05'),
                predicted_price_30d=commodity.market_price * Decimal('1.1'),
                market_sentiment=random.choice(['BULLISH', 'BEARISH', 'NEUTRAL']),
                best_buy_time="Early morning",
                optimal_bid_range={
                    'min': round(float(commodity.market_price) * 0.95, 2),
                    'max': round(float(commodity.market_price) * 1.15, 2),
                    'recommended': round(float(commodity.market_price) * 1.02, 2)
                }
            )
        
        # Create AI recommendations
        for buyer in buyers:
            for listing in listings[:3]:  # Recommend first 3 listings
                recommendation_type = random.choice(['BID_NOW', 'WATCH', 'HIGH_VALUE'])
                confidence_score = random.uniform(0.6, 0.9)
                
                AIRecommendation.objects.create(
                    user=buyer,
                    listing=listing,
                    recommendation_type=recommendation_type,
                    confidence_score=confidence_score,
                    reason=f"AI recommends this {listing.commodity.name} based on quality and market conditions",
                    suggested_bid=listing.ai_optimal_bid_range.get('recommended'),
                )
        
        # Create sample notifications
        for user in users:
            Notification.objects.create(
                user=user,
                notification_type='AI_INSIGHT',
                title='🎯 Welcome to AI-Powered Sahayog!',
                message='Your marketplace now has advanced AI features for smarter trading!',
            )
            
            if user.profile.user_type == 'buyer':
                Notification.objects.create(
                    user=user,
                    notification_type='NEW_LISTING',
                    title='🆕 New High-Quality Listing',
                    message='A premium quality listing matching your preferences is now available!',
                    listing=random.choice(listings) if listings else None,
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created:\n'
                f'- {len(commodities)} commodities with AI data\n'
                f'- {len(users)} users with enhanced profiles\n'
                f'- {len(listings)} listings with AI analysis\n'
                f'- {Bid.objects.count()} bids with AI insights\n'
                f'- {MarketAnalytics.objects.count()} market analytics records\n'
                f'- {AIRecommendation.objects.count()} AI recommendations\n'
                f'- {Notification.objects.count()} notifications\n\n'
                f'🎉 Your AI-powered marketplace is ready!'
            )
        )
