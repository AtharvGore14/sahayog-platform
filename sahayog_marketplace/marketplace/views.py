from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.db.models import Q
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from datetime import timedelta
from .models import (
    SupplyListing, Bid, UserProfile, Commodity,
    MarketAnalytics, AIRecommendation, Notification
)
from .serializers import (
    ListingSerializer, BidSerializer, UserSerializer, UserProfileSerializer, 
    CommoditySerializer, MarketAnalyticsSerializer, AIRecommendationSerializer,
    NotificationSerializer
)
from .permissions import IsBuyer, IsSeller

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Health check endpoint for subprocess proxy"""
    return Response({'status': 'ok', 'service': 'marketplace'}, status=status.HTTP_200_OK)

class UserCreateView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def custom_token_auth(request):
    """Custom token authentication endpoint that accepts JSON"""
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response(
            {'error': 'Username and password are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user = authenticate(username=username, password=password)
    if not user:
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not user.is_active:
        return Response(
            {'error': 'User account is disabled'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    token, created = Token.objects.get_or_create(user=user)
    return Response({'token': token.key})

class UserProfileView(generics.RetrieveAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        try:
            return self.request.user.profile
        except UserProfile.DoesNotExist:
            # Create a default profile if one doesn't exist, e.g., for superuser
            return UserProfile.objects.create(user=self.request.user, user_type='buyer')

class ListingListView(generics.ListAPIView):
    """
    List all active listings (buyer view).
    - Automatically marks expired listings as EXPIRED
    - Only shows recent listings (created today or within last 7 days)
    - Filters out EXPIRED and SOLD listings
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ListingSerializer
    
    def get_serializer_context(self):
        """Pass request context to serializer for building absolute URLs"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def get_queryset(self):
        # First, automatically mark expired listings as EXPIRED
        expired_listings = SupplyListing.objects.filter(
            status='LIVE',
            auction_ends_at__lt=timezone.now()
        )
        expired_count = expired_listings.update(status='EXPIRED')
        if expired_count > 0:
            print(f"Automatically expired {expired_count} listing(s)")
        
        # Calculate date threshold for recent listings (today or within last 7 days)
        recent_threshold = timezone.now() - timedelta(days=7)
        
        # Check if user wants to see their own listings (seller view)
        # Frontend can pass ?seller=<username> or we check if user is seller
        seller_filter = self.request.query_params.get('seller', None)
        is_seller_view = False
        
        if seller_filter is not None:
            is_seller_view = True
        else:
            # Safely check if user is a seller
            # Use try/except to handle case where profile doesn't exist yet
            try:
                # Try to get profile - Django will raise RelatedObjectDoesNotExist if it doesn't exist
                profile = self.request.user.profile
                if profile.user_type == 'seller':
                    is_seller_view = True
            except (AttributeError, UserProfile.DoesNotExist, Exception):
                # If profile doesn't exist or any error, default to buyer view
                # This is safe - user can still sign in and use the system
                is_seller_view = False
        
        # Build queryset - always exclude EXPIRED listings
        if is_seller_view:
            # Sellers can see their LIVE and SOLD listings (recent only)
            seller_username = seller_filter or self.request.user.username
            queryset = SupplyListing.objects.filter(
                seller__username__iexact=seller_username,
                status__in=['LIVE', 'SOLD'],
                created_at__gte=recent_threshold
            ).order_by('-created_at')
        else:
            # Buyers see only LIVE listings (recent only)
            queryset = SupplyListing.objects.filter(
                status='LIVE',
                created_at__gte=recent_threshold
            ).order_by('-created_at')
        
        return queryset

class ListingCreateView(generics.CreateAPIView):
    queryset = SupplyListing.objects.all()
    serializer_class = ListingSerializer
    permission_classes = [permissions.IsAuthenticated, IsSeller]
    parser_classes = (MultiPartParser, FormParser)
    
    def get_serializer_context(self):
        """Pass request context to serializer for building absolute URLs"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        # Ensure starting_price is populated even if omitted or parsed as null
        data = dict(serializer.validated_data)
        starting_price = data.get('starting_price')
        if starting_price in (None, ""):
            commodity = data.get('commodity')
            default_price = getattr(commodity, 'market_price', None) or 0
            serializer.save(seller=self.request.user, status='LIVE', starting_price=default_price)
        else:
            serializer.save(seller=self.request.user, status='LIVE')

class ListingDetailView(generics.RetrieveAPIView):
    queryset = SupplyListing.objects.all()
    serializer_class = ListingSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_context(self):
        """Pass request context to serializer for building absolute URLs"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

class ListingUpdateView(generics.UpdateAPIView):
    queryset = SupplyListing.objects.all()
    serializer_class = ListingSerializer
    permission_classes = [permissions.IsAuthenticated, IsSeller]
    parser_classes = (MultiPartParser, FormParser)

    def perform_update(self, serializer):
        # Ensure only the seller can update their listing
        instance = self.get_object()
        if instance.seller != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only update your own listings.")
        serializer.save()

class BidCreateView(generics.CreateAPIView):
    serializer_class = BidSerializer
    permission_classes = [permissions.IsAuthenticated, IsBuyer]

    def perform_create(self, serializer):
        serializer.save(bidder=self.request.user)

class CommodityListCreateView(generics.ListCreateAPIView):
    queryset = Commodity.objects.all().order_by('name')
    serializer_class = CommoditySerializer
    permission_classes = [permissions.IsAuthenticated]


# 🧠 AI-POWERED VIEWS

class MarketAnalyticsView(generics.ListAPIView):
    """Get AI-powered market analytics"""
    serializer_class = MarketAnalyticsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return MarketAnalytics.objects.all().order_by('-date')[:30]


class AIRecommendationsView(generics.ListAPIView):
    """Get AI recommendations for the current user"""
    serializer_class = AIRecommendationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return AIRecommendation.objects.filter(
            user=self.request.user
        ).order_by('-confidence_score')[:10]


class NotificationsView(generics.ListAPIView):
    """Get user notifications"""
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(
            user=self.request.user
        ).order_by('-created_at')[:20]


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    try:
        notification = Notification.objects.get(
            id=notification_id,
            user=request.user
        )
        notification.is_read = True
        notification.save()
        return Response({'status': 'success'})
    except Notification.DoesNotExist:
        return Response(
            {'error': 'Notification not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def ai_bid_suggestions(request, listing_id):
    """Get AI-powered bid suggestions for a listing"""
    try:
        listing = SupplyListing.objects.get(id=listing_id, status='LIVE')
        
        # Get AI optimal bid range
        bid_range = listing.ai_optimal_bid_range
        
        # Get user's bidding history for similar items
        user_bids = Bid.objects.filter(
            bidder=request.user,
            listing__commodity=listing.commodity
        ).order_by('-timestamp')[:5]
        
        # Calculate personalized suggestions
        suggestions = {
            'optimal_range': bid_range,
            'market_conditions': {
                'demand_score': float(listing.commodity.demand_score),
                'supply_score': float(listing.commodity.supply_score),
                'volatility': float(listing.commodity.volatility_index),
                'trend': listing.commodity.price_trend
            },
            'listing_analysis': {
                'quality_score': float(listing.quality_score),
                'competitiveness': float(listing.ai_competitiveness_score),
                'urgency_factor': float(listing.urgency_factor),
                'time_remaining_hours': listing.time_remaining_seconds / 3600
            },
            'user_history': {
                'average_bid_amount': float(sum(bid.amount for bid in user_bids) / len(user_bids)) if user_bids else 0,
                'success_rate': float(request.user.profile.ai_success_rate),
                'preferred_strategy': request.user.profile.preferred_bid_strategy
            }
        }
        
        return Response(suggestions)
        
    except SupplyListing.DoesNotExist:
        return Response(
            {'error': 'Listing not found or not live'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def ai_market_insights(request):
    """Get comprehensive AI market insights"""
    insights = {
        'top_opportunities': [],
        'market_trends': [],
        'price_alerts': [],
        'recommendations': []
    }
    
    # Get top opportunities (high quality, good price)
    top_listings = SupplyListing.objects.filter(
        status='LIVE',
        quality_score__gt=0.7
    ).order_by('-ai_competitiveness_score')[:5]
    
    for listing in top_listings:
        if listing.ai_suggested_price and listing.commodity.market_price:
            price_ratio = float(listing.ai_suggested_price) / float(listing.commodity.market_price)
            if price_ratio < 0.95:  # Good deal
                insights['top_opportunities'].append({
                    'listing_id': listing.id,
                    'commodity': listing.commodity.name,
                    'quality_score': float(listing.quality_score),
                    'price_advantage': round((1 - price_ratio) * 100, 1),
                    'time_remaining': listing.time_remaining_seconds
                })
    
    # Get market trends
    commodities = Commodity.objects.all()
    for commodity in commodities:
        insights['market_trends'].append({
            'commodity': commodity.name,
            'trend': commodity.price_trend,
            'demand_score': float(commodity.demand_score),
            'supply_score': float(commodity.supply_score),
            'volatility': float(commodity.volatility_index),
            'ai_suggested_price': float(commodity.ai_suggested_price)
        })
    
    # Get user's AI recommendations
    user_recommendations = AIRecommendation.objects.filter(
        user=request.user,
        confidence_score__gt=0.7
    ).order_by('-confidence_score')[:5]
    
    for rec in user_recommendations:
        insights['recommendations'].append({
            'listing_id': rec.listing.id,
            'commodity': rec.listing.commodity.name,
            'recommendation_type': rec.recommendation_type,
            'confidence': float(rec.confidence_score),
            'reason': rec.reason,
            'suggested_bid': float(rec.suggested_bid) if rec.suggested_bid else None
        })
    
    return Response(insights)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def trigger_ai_analysis(request, listing_id):
    """Manually trigger AI analysis for a listing"""
    try:
        listing = SupplyListing.objects.get(id=listing_id)
        
        # Check if user owns the listing or is admin
        if listing.seller != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Trigger AI analysis tasks
        from .tasks import analyze_listing_quality, generate_ai_recommendations
        
        if listing.image:
            analyze_listing_quality.delay(listing_id)
        
        generate_ai_recommendations.delay()
        
        return Response({
            'status': 'success',
            'message': 'AI analysis triggered successfully'
        })
        
    except SupplyListing.DoesNotExist:
        return Response(
            {'error': 'Listing not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def ai_competitor_analysis(request, listing_id):
    """Get AI-powered competitor analysis for a listing"""
    try:
        listing = SupplyListing.objects.get(id=listing_id, status='LIVE')
        
        # Find similar listings
        similar_listings = SupplyListing.objects.filter(
            commodity=listing.commodity,
            status='LIVE'
        ).exclude(id=listing_id)
        
        competitor_analysis = {
            'listing_id': listing_id,
            'commodity': listing.commodity.name,
            'competitors': [],
            'competitive_position': {
                'price_rank': 0,
                'quality_rank': 0,
                'overall_rank': 0
            }
        }
        
        # Analyze competitors
        all_listings = list(similar_listings) + [listing]
        
        # Sort by price and quality
        price_sorted = sorted(all_listings, key=lambda x: float(x.ai_suggested_price or x.starting_price))
        quality_sorted = sorted(all_listings, key=lambda x: x.quality_score, reverse=True)
        
        for comp_listing in similar_listings[:5]:  # Top 5 competitors
            competitor_analysis['competitors'].append({
                'listing_id': comp_listing.id,
                'seller': comp_listing.seller.username,
                'quantity': float(comp_listing.quantity_kg),
                'price': float(comp_listing.ai_suggested_price or comp_listing.starting_price),
                'quality_score': float(comp_listing.quality_score),
                'time_remaining': comp_listing.time_remaining_seconds,
                'bid_count': comp_listing.bids.count()
            })
        
        # Calculate competitive position
        listing_price = float(listing.ai_suggested_price or listing.starting_price)
        listing_quality = float(listing.quality_score)
        
        price_rank = next(i for i, l in enumerate(price_sorted) if l.id == listing_id) + 1
        quality_rank = next(i for i, l in enumerate(quality_sorted) if l.id == listing_id) + 1
        
        competitor_analysis['competitive_position'] = {
            'price_rank': price_rank,
            'quality_rank': quality_rank,
            'overall_rank': (price_rank + quality_rank) / 2,
            'total_competitors': len(similar_listings)
        }
        
        return Response(competitor_analysis)
        
    except SupplyListing.DoesNotExist:
        return Response(
            {'error': 'Listing not found'},
            status=status.HTTP_404_NOT_FOUND
        )