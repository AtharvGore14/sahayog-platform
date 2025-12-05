"""
Advanced AI Waste Analysis Module
Real image analysis for accurate waste classification
"""

import cv2
import numpy as np
from PIL import Image
import os
from datetime import datetime
import random

class WasteAnalyzer:
    def __init__(self):
        self.waste_patterns = {
            'ORGANIC_WASTE': {
                'colors': [(34, 139, 34), (107, 142, 35), (154, 205, 50), (124, 252, 0), (85, 107, 47), (139, 69, 19), (160, 82, 45), (210, 180, 140)],
                'texture_patterns': ['rough', 'irregular', 'natural'],
                'shapes': ['irregular', 'organic'],
                'typical_confidence': 0.85
            },
            'PLASTIC_WASTE': {
                'colors': [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255), (255, 165, 0), (255, 192, 203)],
                'texture_patterns': ['smooth', 'shiny', 'synthetic'],
                'shapes': ['rectangular', 'cylindrical', 'bottles'],
                'typical_confidence': 0.82
            },
            'PAPER_WASTE': {
                'colors': [(255, 255, 255), (245, 245, 220), (222, 184, 135), (210, 180, 140), (250, 235, 215), (255, 228, 196)],
                'texture_patterns': ['flat', 'textured', 'fibrous'],
                'shapes': ['rectangular', 'flat'],
                'typical_confidence': 0.78
            },
            'METAL_WASTE': {
                'colors': [(192, 192, 192), (169, 169, 169), (105, 105, 105), (128, 128, 128), (220, 220, 220), (211, 211, 211)],
                'texture_patterns': ['metallic', 'shiny', 'reflective'],
                'shapes': ['cylindrical', 'rectangular'],
                'typical_confidence': 0.80
            },
            'GLASS_WASTE': {
                'colors': [(173, 216, 230), (135, 206, 235), (0, 191, 255), (30, 144, 255), (176, 196, 222), (135, 206, 250)],
                'texture_patterns': ['transparent', 'smooth', 'translucent'],
                'shapes': ['cylindrical', 'bottles'],
                'typical_confidence': 0.75
            },
            'ELECTRONIC_WASTE': {
                'colors': [(0, 0, 0), (25, 25, 25), (64, 64, 64), (105, 105, 105), (128, 128, 128), (47, 79, 79)],
                'texture_patterns': ['smooth', 'metallic'],
                'shapes': ['rectangular', 'complex'],
                'typical_confidence': 0.88
            }
        }

    def analyze_image(self, image_path):
        """Analyze the uploaded image and classify waste type"""
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                return self._get_default_analysis()
            
            # Convert to RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Analyze image properties
            color_analysis = self._analyze_colors(image_rgb)
            texture_analysis = self._analyze_texture(image_rgb)
            shape_analysis = self._analyze_shapes(image_rgb)
            
            # Get filename hints for better classification
            filename_hint = self._get_filename_hint(image_path)
            
            # Classify based on analysis
            classification = self._classify_waste(color_analysis, texture_analysis, shape_analysis, filename_hint)
            
            return classification
            
        except Exception as e:
            print(f"Error analyzing image: {e}")
            return self._get_default_analysis()

    def _analyze_colors(self, image):
        """Analyze dominant colors in the image"""
        # Reshape image to be a list of pixels
        pixels = image.reshape(-1, 3)
        
        # Get dominant colors using k-means clustering
        from sklearn.cluster import KMeans
        kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
        kmeans.fit(pixels)
        
        # Get the dominant colors
        dominant_colors = kmeans.cluster_centers_.astype(int)
        
        return dominant_colors.tolist()

    def _analyze_texture(self, image):
        """Analyze texture patterns in the image"""
        # Convert to grayscale for texture analysis
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        
        # Calculate texture features using Local Binary Patterns
        try:
            from skimage.feature import local_binary_pattern
            from skimage import measure
            
            # Local Binary Pattern for texture
            radius = 3
            n_points = 8 * radius
            lbp = local_binary_pattern(gray, n_points, radius, method='uniform')
            
            # Calculate texture statistics
            texture_variance = np.var(lbp)
            texture_mean = np.mean(lbp)
            
            # Determine texture type based on statistics
            if texture_variance < 50:
                return 'smooth'
            elif texture_variance < 150:
                return 'textured'
            else:
                return 'rough'
                
        except ImportError:
            # Fallback texture analysis
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size
            
            if edge_density < 0.1:
                return 'smooth'
            elif edge_density < 0.3:
                return 'textured'
            else:
                return 'rough'

    def _analyze_shapes(self, image):
        """Analyze shapes and contours in the image"""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        
        # Apply edge detection
        edges = cv2.Canny(gray, 50, 150)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return 'irregular'
        
        # Analyze the largest contour
        largest_contour = max(contours, key=cv2.contourArea)
        
        # Calculate shape features
        area = cv2.contourArea(largest_contour)
        perimeter = cv2.arcLength(largest_contour, True)
        
        if perimeter == 0:
            return 'irregular'
        
        # Calculate circularity
        circularity = 4 * np.pi * area / (perimeter * perimeter)
        
        # Calculate aspect ratio
        x, y, w, h = cv2.boundingRect(largest_contour)
        aspect_ratio = w / h if h > 0 else 1
        
        # Classify shape
        if circularity > 0.7:
            return 'cylindrical'
        elif 0.8 <= aspect_ratio <= 1.2:
            return 'rectangular'
        else:
            return 'irregular'

    def _get_filename_hint(self, image_path):
        """Extract hints from filename for better classification"""
        filename = os.path.basename(image_path).lower()
        
        # Check for keywords in filename
        if any(word in filename for word in ['organic', 'food', 'vegetable', 'fruit', 'plant', 'leaf', 'green']):
            return 'ORGANIC_WASTE'
        elif any(word in filename for word in ['plastic', 'bottle', 'container', 'bag', 'synthetic']):
            return 'PLASTIC_WASTE'
        elif any(word in filename for word in ['paper', 'cardboard', 'document', 'white']):
            return 'PAPER_WASTE'
        elif any(word in filename for word in ['metal', 'aluminum', 'can', 'steel', 'iron']):
            return 'METAL_WASTE'
        elif any(word in filename for word in ['glass', 'bottle', 'transparent', 'clear']):
            return 'GLASS_WASTE'
        elif any(word in filename for word in ['electronic', 'phone', 'computer', 'device', 'tech']):
            return 'ELECTRONIC_WASTE'
        
        return None

    def _classify_waste(self, colors, texture, shape, filename_hint=None):
        """Classify waste based on analysis results"""
        scores = {}
        
        for waste_type, patterns in self.waste_patterns.items():
            score = 0
            
            # Color matching (improved logic)
            color_score = self._match_colors(colors, patterns['colors'])
            score += color_score * 0.5  # Increased weight for color
            
            # Texture matching (improved logic)
            texture_score = self._match_texture(texture, patterns['texture_patterns'])
            score += texture_score * 0.3
            
            # Shape matching (improved logic)
            shape_score = self._match_shape(shape, patterns['shapes'])
            score += shape_score * 0.2
            
            # Apply bias against electronic waste unless very specific conditions
            if waste_type == 'ELECTRONIC_WASTE':
                # Electronic waste needs very specific characteristics
                if texture not in ['smooth', 'metallic'] or shape not in ['rectangular', 'complex']:
                    score *= 0.3  # Heavily reduce score
                # Need dark colors for electronic waste
                dark_colors = sum(1 for color in colors if sum(color) < 200)
                if dark_colors < len(colors) * 0.6:  # Less than 60% dark colors
                    score *= 0.2  # Further reduce score
            
            # Boost organic waste if natural characteristics
            if waste_type == 'ORGANIC_WASTE':
                if texture == 'rough' or shape == 'irregular':
                    score *= 1.5  # Boost score
                # Boost if green/brown colors
                natural_colors = sum(1 for color in colors 
                                   if (color[1] > color[0] and color[1] > color[2]) or  # Green dominant
                                      (color[0] > 100 and color[1] > 80 and color[2] < 100))  # Brown tones
                if natural_colors > 0:
                    score *= 1.3
            
            # Boost plastic waste if bright colors and smooth texture
            if waste_type == 'PLASTIC_WASTE':
                if texture == 'smooth' and any(sum(color) > 400 for color in colors):
                    score *= 1.4
            
            # Apply filename hint boost
            if filename_hint == waste_type:
                score *= 1.5  # Boost if filename suggests this type
                print(f"Filename hint boost applied for {waste_type}")
            
            scores[waste_type] = score
        
        # Debug: print scores for troubleshooting
        print(f"Classification scores: {scores}")
        if filename_hint:
            print(f"Filename hint: {filename_hint}")
        
        # Get the best match
        best_match = max(scores, key=scores.get)
        raw_confidence = scores[best_match]
        
        # Normalize confidence to 0-1 range using sigmoid function
        # This ensures scores above 1.0 are properly scaled down
        import math
        confidence = 1 / (1 + math.exp(-(raw_confidence - 1.0)))  # Sigmoid normalization
        
        # If filename hint exists and confidence is low, consider using hint
        if filename_hint and confidence < 0.4:
            hint_score = scores.get(filename_hint, 0)
            if hint_score > 0.2:  # If hint type has reasonable score
                best_match = filename_hint
                # Normalize hint score too
                hint_confidence = 1 / (1 + math.exp(-(hint_score - 1.0)))
                confidence = min(hint_confidence * 1.2, 0.8)  # Boost but cap at 0.8
                print(f"Using filename hint: {filename_hint} with confidence {confidence}")
        
        # Ensure confidence is within valid range (0-1)
        confidence = max(0.0, min(1.0, confidence))
        
        # Ensure minimum confidence threshold
        if confidence < 0.3:
            best_match = 'UNKNOWN_WASTE'
            confidence = 0.3
        
        # Get detailed analysis for the best match
        return self._get_detailed_analysis(best_match, confidence, colors, texture, shape)

    def _match_colors(self, image_colors, pattern_colors):
        """Match image colors with waste type color patterns"""
        if not image_colors or not pattern_colors:
            return 0.0
            
        matches = 0
        total_score = 0
        
        for img_color in image_colors:
            best_match_score = 0
            for pattern_color in pattern_colors:
                # Calculate color distance
                distance = np.sqrt(sum((a - b) ** 2 for a, b in zip(img_color, pattern_color)))
                # Convert distance to similarity score (closer = higher score)
                similarity = max(0, 1 - distance / 300)  # 300 is max reasonable distance
                best_match_score = max(best_match_score, similarity)
            
            total_score += best_match_score
            if best_match_score > 0.3:  # Threshold for good match
                matches += 1
        
        # Return average similarity score
        return total_score / len(image_colors) if image_colors else 0.0

    def _match_texture(self, image_texture, pattern_textures):
        """Match image texture with waste type texture patterns"""
        if image_texture in pattern_textures:
            return 1.0
        elif any(t in image_texture for t in pattern_textures):
            return 0.7
        else:
            return 0.3

    def _match_shape(self, image_shape, pattern_shapes):
        """Match image shape with waste type shape patterns"""
        if image_shape in pattern_shapes:
            return 1.0
        else:
            return 0.5

    def _get_detailed_analysis(self, waste_type, confidence, colors, texture, shape):
        """Get detailed analysis results for the classified waste type"""
        
        analysis_templates = {
            'ORGANIC_WASTE': {
                'sub_category': 'Food Waste',
                'recyclability': 'COMPOSTABLE',
                'environmental_impact': 'LOW',
                'disposal_method': 'COMPOSTING',
                'processing_time': '2-4 weeks',
                'carbon_footprint': '0.1 kg CO2',
                'monetary_value': '₹0.50 per kg',
                'composition': {
                    'organic_matter': 85,
                    'moisture': 70,
                    'contaminants': 5,
                    'nutrients': 15
                },
                'audit_score': int(85 + confidence * 15),
                'segregation_quality': 'EXCELLENT' if confidence > 0.8 else 'GOOD',
                'contamination_level': 'LOW',
                'recommendations': [
                    'Perfect for home composting - high nutrient value',
                    'Add to green waste bin for municipal composting',
                    'Can be used as organic fertilizer after processing',
                    'Biodegradable in 2-4 weeks under proper conditions',
                    'Consider vermicomposting for faster breakdown'
                ],
                'environmental_benefits': [
                    'Reduces methane emissions from landfills',
                    'Creates nutrient-rich soil amendment',
                    'Supports circular economy principles',
                    'Zero waste to landfill potential'
                ],
                'processing_facilities': [
                    'Local composting facility - 5km away',
                    'Municipal green waste center',
                    'Community garden composting program'
                ]
            },
            'PLASTIC_WASTE': {
                'sub_category': 'PET Bottles',
                'recyclability': 'HIGHLY_RECYCLABLE',
                'environmental_impact': 'HIGH',
                'disposal_method': 'RECYCLING_PLANT',
                'processing_time': '2-6 months',
                'carbon_footprint': '2.5 kg CO2',
                'monetary_value': '₹35 per kg',
                'composition': {
                    'PET_polymer': 95,
                    'additives': 3,
                    'contaminants': 2,
                    'labels': 1
                },
                'audit_score': int(70 + confidence * 20),
                'segregation_quality': 'GOOD' if confidence > 0.7 else 'FAIR',
                'contamination_level': 'MEDIUM',
                'recommendations': [
                    'Remove labels and caps before recycling',
                    'Rinse thoroughly to remove contaminants',
                    'Send to certified plastic recycling facility',
                    'Check recycling number (PET #1) for confirmation',
                    'Consider upcycling for creative reuse projects'
                ],
                'environmental_benefits': [
                    'Reduces virgin plastic production',
                    'Prevents ocean pollution',
                    'Saves energy in manufacturing',
                    'Reduces carbon footprint by 75%'
                ],
                'processing_facilities': [
                    'Regional plastic recycling plant - 15km away',
                    'PET bottle collection center',
                    'Industrial recycling facility'
                ]
            },
            'PAPER_WASTE': {
                'sub_category': 'Office Paper',
                'recyclability': 'HIGHLY_RECYCLABLE',
                'environmental_impact': 'LOW',
                'disposal_method': 'PAPER_RECYCLING',
                'processing_time': '2-4 weeks',
                'carbon_footprint': '0.8 kg CO2',
                'monetary_value': '₹12 per kg',
                'composition': {
                    'cellulose': 90,
                    'ink': 5,
                    'contaminants': 3,
                    'coatings': 2
                },
                'audit_score': int(80 + confidence * 15),
                'segregation_quality': 'GOOD' if confidence > 0.7 else 'FAIR',
                'contamination_level': 'LOW',
                'recommendations': [
                    'Remove any plastic or metal clips',
                    'Keep dry and clean before recycling',
                    'Send to paper recycling center',
                    'Can be recycled 5-7 times maximum',
                    'Consider shredding for security if needed'
                ],
                'environmental_benefits': [
                    'Saves trees and forest resources',
                    'Reduces water usage in paper production',
                    'Decreases energy consumption by 40%',
                    'Supports sustainable forestry practices'
                ],
                'processing_facilities': [
                    'Local paper recycling mill - 8km away',
                    'Municipal paper collection center',
                    'Office supply store take-back program'
                ]
            },
            'METAL_WASTE': {
                'sub_category': 'Aluminum Cans',
                'recyclability': 'HIGHLY_RECYCLABLE',
                'environmental_impact': 'MEDIUM',
                'disposal_method': 'METAL_RECYCLING',
                'processing_time': '1-2 months',
                'carbon_footprint': '1.2 kg CO2',
                'monetary_value': '₹85 per kg',
                'composition': {
                    'aluminum_alloy': 95,
                    'paint_coating': 3,
                    'contaminants': 2,
                    'labels': 1
                },
                'audit_score': int(85 + confidence * 15),
                'segregation_quality': 'EXCELLENT' if confidence > 0.8 else 'GOOD',
                'contamination_level': 'LOW',
                'recommendations': [
                    'Clean and remove any liquid residue',
                    'Separate from other metal types',
                    'Take to metal recycling facility',
                    'High economic value - worth collecting',
                    'Can be recycled infinitely without quality loss'
                ],
                'environmental_benefits': [
                    'Saves 95% energy compared to new aluminum',
                    'Reduces mining environmental impact',
                    'Prevents landfill accumulation',
                    'Supports circular economy model'
                ],
                'processing_facilities': [
                    'Regional aluminum recycling plant - 12km away',
                    'Metal scrap yard with aluminum focus',
                    'Beverage company collection program'
                ]
            },
            'GLASS_WASTE': {
                'sub_category': 'Glass Bottles',
                'recyclability': 'HIGHLY_RECYCLABLE',
                'environmental_impact': 'LOW',
                'disposal_method': 'GLASS_RECYCLING',
                'processing_time': '1-2 months',
                'carbon_footprint': '0.5 kg CO2',
                'monetary_value': '₹8 per kg',
                'composition': {
                    'silica': 75,
                    'soda_ash': 15,
                    'lime': 10,
                    'contaminants': 2
                },
                'audit_score': int(80 + confidence * 15),
                'segregation_quality': 'GOOD' if confidence > 0.7 else 'FAIR',
                'contamination_level': 'LOW',
                'recommendations': [
                    'Remove caps and labels before recycling',
                    'Keep separate from other glass colors',
                    'Send to glass recycling facility',
                    'Can be recycled infinitely',
                    'Avoid broken glass in recycling'
                ],
                'environmental_benefits': [
                    'Reduces energy consumption by 30%',
                    'Saves raw materials',
                    'Reduces landfill waste',
                    'Supports circular economy'
                ],
                'processing_facilities': [
                    'Local glass recycling plant - 10km away',
                    'Glass collection center',
                    'Municipal glass recycling program'
                ]
            },
            'ELECTRONIC_WASTE': {
                'sub_category': 'Electronic Device',
                'recyclability': 'PARTIALLY_RECYCLABLE',
                'environmental_impact': 'VERY_HIGH',
                'disposal_method': 'E_WASTE_FACILITY',
                'processing_time': '6-12 months',
                'carbon_footprint': '18.5 kg CO2',
                'monetary_value': '₹200-800 per item',
                'composition': {
                    'precious_metals': 15,
                    'base_metals': 25,
                    'plastics': 30,
                    'glass': 20,
                    'hazardous_materials': 10
                },
                'audit_score': int(75 + confidence * 20),
                'segregation_quality': 'EXCELLENT' if confidence > 0.8 else 'GOOD',
                'contamination_level': 'LOW',
                'recommendations': [
                    'Remove all personal data before disposal',
                    'Take to certified e-waste facility only',
                    'Consider donating if still functional',
                    'Never dispose in regular trash - illegal',
                    'Check for trade-in or buyback programs'
                ],
                'environmental_benefits': [
                    'Prevents toxic material leaching',
                    'Recovers valuable metals and materials',
                    'Reduces mining demand for rare earth elements',
                    'Complies with environmental regulations'
                ],
                'processing_facilities': [
                    'Certified e-waste processing facility - 25km away',
                    'Electronics recycling center',
                    'Electronics manufacturer take-back program'
                ]
            }
        }
        
        # Get the template for the waste type
        analysis = analysis_templates.get(waste_type, analysis_templates['ORGANIC_WASTE']).copy()
        
        # Add analysis metadata
        analysis['primary_type'] = waste_type
        analysis['confidence'] = confidence
        analysis['analysis_timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        analysis['image_analysis'] = {
            'dominant_colors': colors,
            'texture_type': texture,
            'shape_type': shape,
            'analysis_method': 'AI_Computer_Vision'
        }
        
        return analysis

    def _get_default_analysis(self):
        """Fallback analysis when image processing fails"""
        return {
            'primary_type': 'UNKNOWN_WASTE',
            'confidence': 0.3,
            'sub_category': 'Mixed Waste',
            'recyclability': 'UNKNOWN',
            'environmental_impact': 'MEDIUM',
            'disposal_method': 'GENERAL_DISPOSAL',
            'processing_time': 'Unknown',
            'carbon_footprint': 'Unknown',
            'monetary_value': 'Unknown',
            'composition': {
                'mixed_materials': 100
            },
            'audit_score': 30,
            'segregation_quality': 'POOR',
            'contamination_level': 'HIGH',
            'recommendations': [
                'Manual inspection required',
                'Separate into different waste streams',
                'Consult waste management professional',
                'Check local recycling guidelines'
            ],
            'environmental_benefits': [
                'Proper sorting reduces environmental impact',
                'Prevents contamination of recycling streams'
            ],
            'processing_facilities': [
                'Local waste management facility',
                'Mixed waste processing center'
            ],
            'analysis_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'image_analysis': {
                'analysis_method': 'FALLBACK_DEFAULT',
                'error': 'Image processing failed'
            }
        }

# Create global analyzer instance
waste_analyzer = WasteAnalyzer()
