"""
OCR service for receipt text extraction using Google Vision API
"""

import logging
import os
import re
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, date
from io import BytesIO
import requests
from PIL import Image

try:
    from google.cloud import vision
    GOOGLE_VISION_AVAILABLE = True
except ImportError:
    GOOGLE_VISION_AVAILABLE = False
    vision = None

from app.models.receipts import ReceiptItem, ReceiptItemCategory

# Configure logging
logger = logging.getLogger(__name__)

class OCRService:
    """OCR service for processing receipt images"""
    
    def __init__(self):
        self.client = None
        self.enabled = os.getenv('OCR_ENABLED', 'false').lower() == 'true'
        self.fallback_enabled = os.getenv('OCR_FALLBACK_ENABLED', 'true').lower() == 'true'
        
        if self.enabled and GOOGLE_VISION_AVAILABLE:
            try:
                # Initialize Google Vision client
                self.client = vision.ImageAnnotatorClient()
                logger.info("Google Vision API client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Google Vision API client: {e}")
                if not self.fallback_enabled:
                    raise
    
    async def extract_text_from_image(self, image_url: str) -> Optional[str]:
        """
        Extract text from receipt image using OCR
        
        Args:
            image_url: URL of the receipt image
            
        Returns:
            Extracted text if successful, None otherwise
        """
        if not self.enabled:
            logger.warning("OCR is disabled, skipping text extraction")
            return None
        
        if not self.client:
            logger.error("OCR client not initialized")
            return None
        
        try:
            # Download image
            image_data = await self._download_image(image_url)
            if not image_data:
                return None
            
            # Process with Google Vision API
            image = vision.Image(content=image_data)
            response = self.client.text_detection(image=image)
            
            if response.error.message:
                logger.error(f"Google Vision API error: {response.error.message}")
                return None
            
            # Extract full text
            texts = response.text_annotations
            if texts:
                extracted_text = texts[0].description
                logger.info(f"Successfully extracted {len(extracted_text)} characters of text")
                return extracted_text
            else:
                logger.warning("No text detected in image")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            return None
    
    async def _download_image(self, image_url: str) -> Optional[bytes]:
        """
        Download image from URL or read from local file
        
        Args:
            image_url: URL or local path of the image
            
        Returns:
            Image data as bytes if successful, None otherwise
        """
        try:
            # Check if it's a local file path
            if not image_url.startswith('http'):
                # Local file path
                import os
                if os.path.exists(image_url):
                    with open(image_url, 'rb') as f:
                        image_data = f.read()
                    
                    # Validate it's an image
                    try:
                        img = Image.open(BytesIO(image_data))
                        img.verify()
                        return image_data
                    except Exception as e:
                        logger.error(f"Invalid image format for local file {image_url}: {e}")
                        return None
                else:
                    logger.error(f"Local file not found: {image_url}")
                    return None
            else:
                # URL - download the image
                # For S3 URLs, we might need to generate presigned URLs
                from app.utils.cloud_storage import cloud_storage_service
                
                # Generate presigned URL if it's an S3 URL
                if '.s3.' in image_url:
                    presigned_url = await cloud_storage_service.generate_presigned_url(image_url)
                    if presigned_url:
                        image_url = presigned_url
                
                response = requests.get(image_url, timeout=30)
                response.raise_for_status()
                
                # Validate it's an image
                try:
                    img = Image.open(BytesIO(response.content))
                    img.verify()
                    return response.content
                except Exception as e:
                    logger.error(f"Invalid image format for URL {image_url}: {e}")
                    return None
                
        except Exception as e:
            logger.error(f"Error downloading/reading image from {image_url}: {e}")
            return None
    
    def parse_receipt_text(self, text: str) -> Dict[str, Any]:
        """
        Parse extracted text to identify receipt components
        
        Args:
            text: Raw extracted text from OCR
            
        Returns:
            Dictionary containing parsed receipt data
        """
        if not text:
            return {}
        
        try:
            # Clean and normalize text
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            # Extract store information
            store_info = self._extract_store_info(lines)
            
            # Extract date
            receipt_date = self._extract_date(lines)
            
            # Extract items
            items = self._extract_items(lines)
            
            # Extract totals
            totals = self._extract_totals(lines)
            
            return {
                'store_name': store_info.get('name'),
                'store_address': store_info.get('address'),
                'receipt_date': receipt_date,
                'items': items,
                'subtotal': totals.get('subtotal'),
                'tax': totals.get('tax'),
                'total': totals.get('total'),
                'raw_text': text
            }
            
        except Exception as e:
            logger.error(f"Error parsing receipt text: {e}")
            return {'raw_text': text}
    
    def _extract_store_info(self, lines: List[str]) -> Dict[str, str]:
        """Extract store name and address from receipt lines"""
        store_info = {'name': None, 'address': None}
        
        # Store name is usually in the first few lines
        for i, line in enumerate(lines[:5]):
            # Skip lines that look like addresses or phone numbers
            if re.search(r'\d{3}-\d{3}-\d{4}|\d{10}', line):  # Phone number
                continue
            if re.search(r'\d+\s+\w+\s+(st|street|ave|avenue|rd|road|blvd|boulevard)', line, re.IGNORECASE):
                store_info['address'] = line
                continue
            
            # Store name is likely a line with mostly letters
            if len(line) > 3 and not re.search(r'^\d+$', line):
                if not store_info['name']:
                    store_info['name'] = line
                    break
        
        return store_info
    
    def _extract_date(self, lines: List[str]) -> Optional[date]:
        """Extract receipt date from lines"""
        date_patterns = [
            r'(\d{1,2})/(\d{1,2})/(\d{2,4})',  # MM/DD/YYYY or MM/DD/YY
            r'(\d{1,2})-(\d{1,2})-(\d{2,4})',  # MM-DD-YYYY or MM-DD-YY
            r'(\d{2,4})/(\d{1,2})/(\d{1,2})',  # YYYY/MM/DD
            r'(\d{2,4})-(\d{1,2})-(\d{1,2})',  # YYYY-MM-DD
        ]
        
        for line in lines:
            for pattern in date_patterns:
                match = re.search(pattern, line)
                if match:
                    try:
                        groups = match.groups()
                        if len(groups[2]) == 2:  # 2-digit year
                            year = 2000 + int(groups[2]) if int(groups[2]) < 50 else 1900 + int(groups[2])
                        else:
                            year = int(groups[2])
                        
                        # Try different date formats
                        if pattern.startswith(r'(\d{2,4})'):  # YYYY first
                            month, day = int(groups[1]), int(groups[2])
                        else:  # MM/DD format
                            month, day = int(groups[0]), int(groups[1])
                        
                        return date(year, month, day)
                    except (ValueError, IndexError):
                        continue
        
        return None
    
    def _extract_items(self, lines: List[str]) -> List[ReceiptItem]:
        """Extract items from receipt lines"""
        items = []
        
        # Patterns for item lines
        item_patterns = [
            # Item name followed by price: "BANANAS 1.99"
            r'^(.+?)\s+(\d+\.?\d*)\s*$',
            # Quantity, item, price: "2 MILK 3.49"
            r'^(\d+\.?\d*)\s+(.+?)\s+(\d+\.?\d*)\s*$',
            # Item with @ price: "BANANAS @ 0.68 1.70"
            r'^(.+?)\s+@\s+(\d+\.?\d*)\s+(\d+\.?\d*)\s*$',
        ]
        
        for line in lines:
            # Skip lines that are clearly not items
            if self._is_non_item_line(line):
                continue
            
            for pattern in item_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    try:
                        item = self._parse_item_match(match, pattern)
                        if item:
                            items.append(item)
                            break
                    except Exception as e:
                        logger.debug(f"Error parsing item line '{line}': {e}")
                        continue
        
        return items
    
    def _is_non_item_line(self, line: str) -> bool:
        """Check if line is not an item (store info, totals, etc.)"""
        non_item_keywords = [
            'total', 'subtotal', 'tax', 'change', 'cash', 'credit', 'debit',
            'thank you', 'receipt', 'store', 'phone', 'address', 'manager',
            'cashier', 'register', 'transaction', 'balance', 'tender'
        ]
        
        line_lower = line.lower()
        return any(keyword in line_lower for keyword in non_item_keywords)
    
    def _parse_item_match(self, match, pattern: str) -> Optional[ReceiptItem]:
        """Parse regex match into ReceiptItem"""
        groups = match.groups()
        
        try:
            if pattern.endswith(r'(\d+\.?\d*)\s*$') and len(groups) == 2:
                # Simple item name + price
                name = groups[0].strip()
                price = float(groups[1])
                return ReceiptItem(
                    name=name,
                    quantity=1.0,
                    unit_price=price,
                    total_price=price,
                    category=self._categorize_item(name)
                )
            
            elif len(groups) == 3:
                if '@' in pattern:
                    # Item @ unit_price total_price
                    name = groups[0].strip()
                    unit_price = float(groups[1])
                    total_price = float(groups[2])
                    quantity = total_price / unit_price if unit_price > 0 else 1.0
                else:
                    # quantity item price
                    quantity = float(groups[0])
                    name = groups[1].strip()
                    total_price = float(groups[2])
                    unit_price = total_price / quantity if quantity > 0 else total_price
                
                return ReceiptItem(
                    name=name,
                    quantity=quantity,
                    unit_price=unit_price,
                    total_price=total_price,
                    category=self._categorize_item(name)
                )
        
        except (ValueError, ZeroDivisionError) as e:
            logger.debug(f"Error parsing item match: {e}")
            return None
        
        return None
    
    def _extract_totals(self, lines: List[str]) -> Dict[str, float]:
        """Extract subtotal, tax, and total from receipt lines"""
        totals = {}
        
        total_patterns = {
            'subtotal': r'subtotal\s*:?\s*\$?(\d+\.?\d*)',
            'tax': r'tax\s*:?\s*\$?(\d+\.?\d*)',
            'total': r'total\s*:?\s*\$?(\d+\.?\d*)',
        }
        
        for line in lines:
            line_lower = line.lower()
            for key, pattern in total_patterns.items():
                if key not in totals:
                    match = re.search(pattern, line_lower)
                    if match:
                        try:
                            totals[key] = float(match.group(1))
                        except ValueError:
                            continue
        
        return totals
    
    def _categorize_item(self, item_name: str) -> ReceiptItemCategory:
        """Categorize item based on name"""
        name_lower = item_name.lower()
        
        # Category keywords mapping
        category_keywords = {
            ReceiptItemCategory.PRODUCE: [
                'banana', 'apple', 'orange', 'grape', 'berry', 'lettuce', 'tomato',
                'onion', 'potato', 'carrot', 'celery', 'spinach', 'broccoli',
                'cucumber', 'pepper', 'avocado', 'lemon', 'lime', 'organic'
            ],
            ReceiptItemCategory.DAIRY: [
                'milk', 'cheese', 'yogurt', 'butter', 'cream', 'egg', 'dairy'
            ],
            ReceiptItemCategory.MEAT: [
                'beef', 'chicken', 'pork', 'turkey', 'ham', 'bacon', 'sausage',
                'ground', 'steak', 'roast', 'chop'
            ],
            ReceiptItemCategory.SEAFOOD: [
                'fish', 'salmon', 'tuna', 'shrimp', 'crab', 'lobster', 'seafood'
            ],
            ReceiptItemCategory.GRAINS: [
                'bread', 'rice', 'pasta', 'cereal', 'oats', 'flour', 'grain',
                'wheat', 'bagel', 'tortilla'
            ],
            ReceiptItemCategory.BEVERAGES: [
                'water', 'juice', 'soda', 'coffee', 'tea', 'beer', 'wine',
                'drink', 'beverage', 'cola'
            ],
            ReceiptItemCategory.FROZEN: [
                'frozen', 'ice cream', 'popsicle', 'frozen pizza'
            ],
            ReceiptItemCategory.CANNED_GOODS: [
                'canned', 'can', 'soup', 'beans', 'corn', 'peas', 'sauce'
            ],
            ReceiptItemCategory.SNACKS: [
                'chips', 'crackers', 'cookies', 'candy', 'chocolate', 'nuts',
                'snack', 'popcorn'
            ],
            ReceiptItemCategory.CONDIMENTS: [
                'ketchup', 'mustard', 'mayo', 'dressing', 'sauce', 'oil',
                'vinegar', 'salt', 'pepper'
            ],
            ReceiptItemCategory.SPICES: [
                'spice', 'herb', 'seasoning', 'garlic', 'ginger', 'basil',
                'oregano', 'thyme'
            ],
            ReceiptItemCategory.BAKING: [
                'sugar', 'flour', 'baking', 'vanilla', 'chocolate chip',
                'yeast', 'powder'
            ]
        }
        
        # Check each category
        for category, keywords in category_keywords.items():
            if any(keyword in name_lower for keyword in keywords):
                return category
        
        return ReceiptItemCategory.OTHER


# Global OCR service instance
ocr_service = OCRService()