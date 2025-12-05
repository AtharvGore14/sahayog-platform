from celery import shared_task
from django.utils import timezone
from datetime import timedelta, datetime
from django.contrib.auth.models import User, Group
from decimal import Decimal
import random
import json
from .models import (
    Commodity, SupplyListing, Bid, Deal, UserProfile, 
    MarketAnalytics, AIRecommendation, Notification
)

@shared_task
def scan_for_market_opportunities():
    print("Agent: Scanning for market opportunities...")
    try:
        seller_group = Group.objects.get(name='seller')
        sellers = User.objects.filter(groups=seller_group)
        if not sellers:
            print("Agent: No users found in the 'seller' group.")
            return "No sellers found."
        
        seller_user = sellers.first()
        cardboard, _ = Commodity.objects.get_or_create(name='Cardboard')
        
        if not SupplyListing.objects.filter(seller=seller_user, commodity=cardboard, status='DRAFT').exists():
            listing = SupplyListing.objects.create(
                seller=seller_user,
                commodity=cardboard,
                quantity_kg=550.0,
                quality_score=0.85,
                status='DRAFT',
                auction_ends_at=timezone.now() + timedelta(days=1)
            )
            print(f"Agent: Created new draft listing {listing.id} for seller {seller_user.username}")
            start_auction.delay(listing.id)
            return f"Created and started auction for listing {listing.id}"
        
        return "No new opportunities found."

    except Group.DoesNotExist:
        print("Agent: The 'seller' group does not exist. Please create it in the admin panel.")
        return "Seller group not found."
    except Exception as e:
        print(f"An error occurred: {e}")
        return "An error occurred."

@shared_task
def update_commodity_prices():
    print("Agent: Updating commodity prices...")
    paper, _ = Commodity.objects.get_or_create(name='Paper')
    paper.market_price = 15.50
    paper.save()
    return "Prices updated."

@shared_task
def start_auction(listing_id):
    try:
        listing = SupplyListing.objects.get(id=listing_id, status='DRAFT')
        listing.status = 'LIVE'
        listing.save()
        print(f"Agent: Auction for listing {listing.id} is now LIVE.")
        end_auction.apply_async(args=[listing.id], eta=listing.auction_ends_at)
        return f"Auction {listing.id} started."
    except SupplyListing.DoesNotExist:
        return f"Listing {listing.id} not found or not in draft state."

@shared_task
def end_auction(listing_id):
    try:
        listing = SupplyListing.objects.get(id=listing_id, status='LIVE')
        highest_bid = listing.bids.order_by('-amount').first()
        if highest_bid:
            Deal.objects.create(
                listing=listing,
                buyer=highest_bid.bidder,
                final_price=highest_bid.amount
            )
            listing.status = 'SOLD'
            print(f"Agent: Auction for listing {listing.id} sold to {highest_bid.bidder.username}.")
        else:
            listing.status = 'EXPIRED'
            print(f"Agent: Auction for listing {listing.id} expired with no bids.")
        listing.save()
        return f"Auction {listing.id} ended. Status: {listing.status}"
    except SupplyListing.DoesNotExist:
        return f"Listing {listing.id} not found or not live."


# 🧠 ADVANCED AI TASKS

@shared_task
def analyze_listing_quality(listing_id):
    """AI-powered quality analysis of listing images"""
    try:
        listing = SupplyListing.objects.get(id=listing_id)
        if not listing.image:
            return f"No image to analyze for listing {listing_id}"
        
        # Simulate AI image analysis
        # In production, this would use computer vision APIs
        quality_factors = {
            'clarity': random.uniform(0.7, 0.95),
            'lighting': random.uniform(0.6, 0.9),
            'angle': random.uniform(0.8, 0.95),
            'material_visibility': random.uniform(0.7, 0.9),
            'contamination_detected': random.choice([True, False])
        }
        
        # Calculate overall quality score
        contamination_penalty = 0.2 if quality_factors['contamination_detected'] else 0
        quality_score = (
            quality_factors['clarity'] * 0.3 +
            quality_factors['lighting'] * 0.25 +
            quality_factors['angle'] * 0.2 +
            quality_factors['material_visibility'] * 0.25
        ) - contamination_penalty
        
        quality_score = max(0.0, min(1.0, quality_score))
        
        # Update listing with AI analysis
        listing.quality_score = quality_score
        listing.ai_quality_analysis = quality_factors
        listing.ai_fraud_risk = 0.1 if quality_factors['contamination_detected'] else 0.05
        
        # Calculate AI suggested price
        if listing.commodity.market_price:
            quality_multiplier = 0.8 + (quality_score * 0.4)  # 0.8-1.2
            suggested_price = float(listing.commodity.market_price) * quality_multiplier
            listing.ai_suggested_price = Decimal(str(round(suggested_price, 2)))
        
        listing.save()
        
        print(f"AI: Analyzed listing {listing_id} - Quality: {quality_score:.2f}, Suggested Price: {listing.ai_suggested_price}")
        return f"Quality analysis complete for listing {listing_id}"
        
    except SupplyListing.DoesNotExist:
        return f"Listing {listing_id} not found"


@shared_task
def generate_market_analytics():
    """Generate comprehensive market analytics using AI"""
    print("AI: Generating market analytics...")
    
    for commodity in Commodity.objects.all():
        # Simulate AI market analysis
        base_price = float(commodity.market_price or 50)
        
        # Generate realistic market data
        price_volatility = random.uniform(0.05, 0.25)
        demand_trend = random.choice(['INCREASING', 'DECREASING', 'STABLE'])
        supply_level = random.choice(['HIGH', 'MEDIUM', 'LOW'])
        market_sentiment = random.choice(['BULLISH', 'BEARISH', 'NEUTRAL'])
        
        # Calculate predictions based on trends
        trend_multiplier = {
            'INCREASING': 1.1,
            'DECREASING': 0.9,
            'STABLE': 1.0
        }.get(demand_trend, 1.0)
        
        sentiment_multiplier = {
            'BULLISH': 1.08,
            'BEARISH': 0.92,
            'NEUTRAL': 1.0
        }.get(market_sentiment, 1.0)
        
        predicted_7d = base_price * trend_multiplier * sentiment_multiplier
        predicted_30d = base_price * (trend_multiplier ** 2) * sentiment_multiplier
        
        # Create or update analytics
        analytics, created = MarketAnalytics.objects.get_or_create(
            commodity=commodity,
            date=timezone.now().date(),
            defaults={
                'average_price': commodity.market_price,
                'price_volatility': price_volatility,
                'demand_trend': demand_trend,
                'supply_level': supply_level,
                'predicted_price_7d': Decimal(str(round(predicted_7d, 2))),
                'predicted_price_30d': Decimal(str(round(predicted_30d, 2))),
                'market_sentiment': market_sentiment,
                'best_buy_time': "Early morning" if supply_level == 'HIGH' else "Evening",
                'optimal_bid_range': {
                    'min': round(base_price * 0.95, 2),
                    'max': round(base_price * 1.15, 2),
                    'recommended': round(base_price * 1.02, 2)
                }
            }
        )
        
        # Update commodity with AI insights
        commodity.demand_score = 0.8 if demand_trend == 'INCREASING' else (0.4 if demand_trend == 'DECREASING' else 0.6)
        commodity.supply_score = 0.8 if supply_level == 'HIGH' else (0.4 if supply_level == 'LOW' else 0.6)
        commodity.volatility_index = price_volatility
        commodity.price_trend = demand_trend
        commodity.save()
        
        print(f"AI: Updated analytics for {commodity.name} - Sentiment: {market_sentiment}, Trend: {demand_trend}")
    
    return "Market analytics generation complete"


@shared_task
def generate_ai_recommendations():
    """Generate AI recommendations for all active users"""
    print("AI: Generating personalized recommendations...")
    
    buyers = User.objects.filter(profile__user_type='buyer')
    
    for buyer in buyers:
        # Get user's bidding history and preferences
        user_bids = Bid.objects.filter(bidder=buyer)
        user_profile = buyer.profile
        
        # Find suitable listings
        live_listings = SupplyListing.objects.filter(status='LIVE')
        
        for listing in live_listings:
            # Skip if user already has recommendation for this listing
            if AIRecommendation.objects.filter(user=buyer, listing=listing).exists():
                continue
            
            # Calculate recommendation score
            recommendation_score = calculate_recommendation_score(buyer, listing)
            
            if recommendation_score > 0.3:  # Only recommend if score > 30%
                recommendation_type = determine_recommendation_type(listing, buyer)
                reason = generate_recommendation_reason(listing, buyer, recommendation_type)
                
                AIRecommendation.objects.create(
                    user=buyer,
                    listing=listing,
                    recommendation_type=recommendation_type,
                    confidence_score=recommendation_score,
                    reason=reason,
                    suggested_bid=listing.ai_optimal_bid_range.get('recommended')
                )
                
                # Create notification for high-confidence recommendations
                if recommendation_score > 0.7:
                    create_notification.delay(
                        user_id=buyer.id,
                        notification_type='AI_INSIGHT',
                        title='🎯 AI Recommendation',
                        message=f'High-value opportunity: {listing.commodity.name}',
                        listing_id=listing.id
                    )
    
    return "AI recommendations generated"


def calculate_recommendation_score(user, listing):
    """Calculate AI recommendation score for a user-listing pair"""
    score = 0.0
    
    # User's historical success rate
    user_profile = user.profile
    score += user_profile.ai_success_rate * 0.3
    
    # Listing quality
    score += listing.quality_score * 0.25
    
    # Market conditions
    commodity = listing.commodity
    if commodity.demand_score > 0.7:
        score += 0.2
    
    # Price competitiveness
    if listing.ai_suggested_price and listing.commodity.market_price:
        price_ratio = float(listing.ai_suggested_price) / float(listing.commodity.market_price)
        if 0.95 <= price_ratio <= 1.05:  # Fair price
            score += 0.15
        elif price_ratio < 0.95:  # Good deal
            score += 0.2
    
    # Time urgency
    if listing.time_remaining_seconds < 3600:  # Less than 1 hour
        score += 0.1
    
    return min(1.0, score)


def determine_recommendation_type(listing, user):
    """Determine the type of recommendation"""
    if listing.time_remaining_seconds < 1800:  # Less than 30 minutes
        return 'SNIPE'
    elif listing.quality_score > 0.8 and listing.ai_suggested_price:
        if float(listing.ai_suggested_price) < float(listing.commodity.market_price or 0) * 0.95:
            return 'HIGH_VALUE'
        else:
            return 'BID_NOW'
    elif listing.interest_score > 0.7:
        return 'WATCH'
    else:
        return 'AVOID'


def generate_recommendation_reason(listing, user, recommendation_type):
    """Generate human-readable recommendation reason"""
    reasons = {
        'BID_NOW': f"High quality ({listing.quality_score:.1f}/1.0) at competitive price. Market demand is {listing.commodity.demand_score:.1f}/1.0",
        'WATCH': f"Good quality listing with moderate competition. Monitor for price changes.",
        'AVOID': f"Low quality score or high competition. Better opportunities available.",
        'SNIPE': f"Limited time remaining! Consider last-minute bid if price is right.",
        'HIGH_VALUE': f"Excellent quality at below-market price. Strong recommendation!"
    }
    return reasons.get(recommendation_type, "AI-generated recommendation based on market analysis")


@shared_task
def create_notification(user_id, notification_type, title, message, listing_id=None, bid_id=None):
    """Create notification for user"""
    try:
        user = User.objects.get(id=user_id)
        listing = SupplyListing.objects.get(id=listing_id) if listing_id else None
        bid = Bid.objects.get(id=bid_id) if bid_id else None
        
        Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            listing=listing,
            bid=bid
        )
        
        print(f"Notification created for {user.username}: {title}")
        return f"Notification sent to {user.username}"
        
    except User.DoesNotExist:
        return f"User {user_id} not found"
    except Exception as e:
        return f"Error creating notification: {str(e)}"


@shared_task
def analyze_bid_competitiveness(bid_id):
    """Analyze bid competitiveness using AI"""
    try:
        bid = Bid.objects.get(id=bid_id)
        listing = bid.listing
        
        # Calculate competitiveness factors
        time_factor = 1.0
        if listing.time_remaining_seconds < 3600:  # Less than 1 hour
            time_factor = 1.2
        
        quality_factor = 0.9 + (listing.quality_score * 0.2)  # 0.9-1.1
        market_factor = 0.95 + (listing.commodity.demand_score * 0.1)  # 0.95-1.05
        
        # Calculate AI confidence
        bid_amount = float(bid.amount)
        suggested_price = float(listing.ai_suggested_price or listing.starting_price)
        
        if suggested_price > 0:
            price_ratio = bid_amount / suggested_price
            if 0.95 <= price_ratio <= 1.05:
                confidence = 0.8 * time_factor * quality_factor * market_factor
            elif price_ratio > 1.05:
                confidence = 0.9 * time_factor * quality_factor * market_factor
            else:
                confidence = 0.4 * time_factor * quality_factor * market_factor
        else:
            confidence = 0.5
        
        confidence = min(1.0, confidence)
        
        # Determine strategy
        if bid_amount > suggested_price * 1.1:
            strategy = 'AGGRESSIVE'
        elif bid_amount < suggested_price * 0.95:
            strategy = 'CONSERVATIVE'
        elif listing.time_remaining_seconds < 300:  # Last 5 minutes
            strategy = 'SNIPE'
        else:
            strategy = 'OPTIMAL'
        
        # Update bid with AI analysis
        bid.ai_bid_confidence = confidence
        bid.ai_bid_strategy = strategy
        bid.ai_success_probability = confidence * (1.0 - listing.ai_fraud_risk)
        bid.save()
        
        print(f"AI: Analyzed bid {bid_id} - Confidence: {confidence:.2f}, Strategy: {strategy}")
        return f"Bid analysis complete for bid {bid_id}"
        
    except Bid.DoesNotExist:
        return f"Bid {bid_id} not found"


@shared_task
def send_auction_ending_alerts():
    """Send alerts for auctions ending soon"""
    print("AI: Checking for auctions ending soon...")
    
    # Find auctions ending in next 30 minutes
    soon_ending = SupplyListing.objects.filter(
        status='LIVE',
        auction_ends_at__lte=timezone.now() + timedelta(minutes=30),
        auction_ends_at__gt=timezone.now()
    )
    
    for listing in soon_ending:
        # Notify all bidders
        bidders = User.objects.filter(bids__listing=listing).distinct()
        
        for bidder in bidders:
            create_notification.delay(
                user_id=bidder.id,
                notification_type='AUCTION_ENDING',
                title='⏰ Auction Ending Soon!',
                message=f'Auction for {listing.commodity.name} ends in {listing.time_remaining_seconds//60} minutes',
                listing_id=listing.id
            )
        
        # Notify seller
        create_notification.delay(
            user_id=listing.seller.id,
            notification_type='AUCTION_ENDING',
            title='⏰ Your Auction Ending Soon!',
            message=f'Your {listing.commodity.name} auction ends in {listing.time_remaining_seconds//60} minutes',
            listing_id=listing.id
        )
    
    return f"Sent alerts for {soon_ending.count()} ending auctions"