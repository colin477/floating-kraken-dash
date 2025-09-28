# OCR Integration Guide

## Overview

This document describes the OCR (Optical Character Recognition) integration for receipt processing in the EZ Eatin' application. The system uses Google Vision API for text extraction from receipt images and includes intelligent text parsing and item categorization.

## Features

### ✅ Implemented Features

1. **Google Vision API Integration**
   - Text extraction from receipt images
   - Configurable OCR service with environment variables
   - Graceful fallback when OCR is unavailable

2. **Intelligent Text Parsing**
   - Store name detection
   - Receipt date extraction (multiple date formats)
   - Item extraction with quantity, price, and categorization
   - Subtotal, tax, and total amount detection

3. **Smart Item Categorization**
   - Automatic categorization into 13 categories:
     - Produce, Dairy, Meat, Seafood, Grains
     - Canned Goods, Frozen, Beverages, Snacks
     - Condiments, Spices, Baking, Other

4. **Error Handling & Fallback**
   - Fallback to mock data when OCR fails
   - Comprehensive error logging
   - Confidence scoring for processing results

5. **Multiple Receipt Formats Support**
   - Standard item + price format
   - Quantity + item + price format
   - Item @ unit_price total_price format

## Configuration

### Environment Variables

Add these variables to your `.env` file:

```bash
# OCR Configuration (Google Vision API)
GOOGLE_CLOUD_PROJECT_ID=your-google-cloud-project-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account-key.json
OCR_ENABLED=true
OCR_FALLBACK_ENABLED=true
```

### Google Cloud Setup

1. **Create a Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one

2. **Enable Vision API**
   - Navigate to APIs & Services > Library
   - Search for "Cloud Vision API"
   - Click "Enable"

3. **Create Service Account**
   - Go to IAM & Admin > Service Accounts
   - Click "Create Service Account"
   - Give it a name (e.g., "receipt-ocr-service")
   - Grant "Cloud Vision API User" role
   - Create and download JSON key file

4. **Set Environment Variables**
   - Set `GOOGLE_CLOUD_PROJECT_ID` to your project ID
   - Set `GOOGLE_APPLICATION_CREDENTIALS` to path of JSON key file
   - Set `OCR_ENABLED=true` to enable OCR processing

## Dependencies

The following packages have been added to `requirements.txt`:

```
google-cloud-vision==3.4.5
pillow==10.1.0
requests==2.31.0
```

Install with:
```bash
cd backend
pip install -r requirements.txt
```

## Usage

### API Endpoint

The OCR integration works through the existing receipt processing endpoint:

```
POST /api/v1/receipts/{receipt_id}/process
```

### Processing Flow

1. **Receipt Upload**: User uploads receipt image via `/receipts/upload`
2. **OCR Processing**: Call `/receipts/{receipt_id}/process` to extract text
3. **Text Analysis**: System parses extracted text for items and metadata
4. **Item Categorization**: Items are automatically categorized
5. **Database Update**: Receipt is updated with extracted items

### Example Response

```json
{
  "receipt_id": "507f1f77bcf86cd799439011",
  "processing_status": "completed",
  "extracted_items": [
    {
      "name": "Organic Bananas",
      "quantity": 2.5,
      "unit_price": 0.68,
      "total_price": 1.70,
      "category": "produce"
    },
    {
      "name": "Whole Milk",
      "quantity": 1.0,
      "unit_price": 3.49,
      "total_price": 3.49,
      "category": "dairy"
    }
  ],
  "confidence_score": 0.85,
  "processing_notes": "OCR processing completed. Extracted 6 items. Store: Walmart Supercenter. Date: 2023-12-15."
}
```

## File Structure

```
backend/
├── app/
│   ├── utils/
│   │   └── ocr_service.py          # Main OCR service implementation
│   ├── crud/
│   │   └── receipts.py             # Updated with OCR integration
│   └── models/
│       └── receipts.py             # Receipt models and enums
├── requirements.txt                # Updated with OCR dependencies
└── .env.example                    # Updated with OCR configuration
```

## Key Components

### OCRService Class (`app/utils/ocr_service.py`)

- **`extract_text_from_image()`**: Extracts text using Google Vision API
- **`parse_receipt_text()`**: Parses extracted text into structured data
- **`_categorize_item()`**: Categorizes items based on name keywords
- **`_extract_items()`**: Extracts individual items from receipt text
- **`_extract_totals()`**: Extracts subtotal, tax, and total amounts

### Updated Receipt Processing (`app/crud/receipts.py`)

- **`process_receipt_image()`**: Main processing function with OCR integration
- **`_process_receipt_fallback()`**: Fallback processing when OCR fails
- **`_calculate_confidence_score()`**: Calculates processing confidence

## Testing

### Run Text Parsing Tests

```bash
python test_text_parsing.py
```

### Run Full OCR Integration Tests

```bash
python test_ocr_integration.py
```

### Test Results

The system successfully:
- ✅ Extracts store names (e.g., "WALMART SUPERCENTER", "TARGET")
- ✅ Parses receipt dates in multiple formats
- ✅ Identifies individual items with prices
- ✅ Categorizes items automatically
- ✅ Handles different receipt formats
- ✅ Provides fallback when OCR is unavailable

## Supported Receipt Formats

### Format 1: Simple Item + Price
```
BANANAS                 1.68
MILK WHOLE GAL          3.49
BREAD WHITE             2.99
```

### Format 2: Quantity + Item + Price
```
2 APPLES                3.98
1 CHICKEN BREAST       11.98
```

### Format 3: Item @ Unit Price Total
```
APPLES @ 1.99          3.98
CHICKEN BREAST @ 5.99  11.98
```

## Item Categories

The system automatically categorizes items into:

| Category | Keywords |
|----------|----------|
| **Produce** | banana, apple, orange, lettuce, tomato, organic |
| **Dairy** | milk, cheese, yogurt, butter, cream, egg |
| **Meat** | beef, chicken, pork, turkey, ham, bacon |
| **Seafood** | fish, salmon, tuna, shrimp, crab |
| **Grains** | bread, rice, pasta, cereal, oats, flour |
| **Beverages** | water, juice, soda, coffee, tea, cola |
| **Frozen** | frozen, ice cream, popsicle |
| **Canned Goods** | canned, soup, beans, corn |
| **Snacks** | chips, crackers, cookies, candy |
| **Condiments** | ketchup, mustard, mayo, oil, vinegar |
| **Spices** | spice, herb, seasoning, garlic |
| **Baking** | sugar, flour, baking, vanilla |

## Error Handling

### OCR Failures
- System logs detailed error messages
- Automatically falls back to mock data if `OCR_FALLBACK_ENABLED=true`
- Returns low confidence score for fallback processing

### Image Processing Errors
- Validates image format before processing
- Handles network timeouts for image downloads
- Provides meaningful error messages in processing notes

### Text Parsing Issues
- Handles malformed receipt text gracefully
- Skips invalid item lines
- Continues processing even if some items fail to parse

## Performance Considerations

- **Image Size**: Larger images take longer to process
- **API Limits**: Google Vision API has rate limits and quotas
- **Network**: Image download speed affects processing time
- **Fallback**: Fallback processing is much faster than OCR

## Security

- Service account credentials should be kept secure
- Image URLs should be validated before processing
- Consider implementing rate limiting for OCR requests

## Future Enhancements

### Potential Improvements
1. **Enhanced Parsing**: Better handling of discounts, coupons, and promotions
2. **Multi-language Support**: Support for receipts in different languages
3. **Receipt Validation**: Cross-validation of extracted totals
4. **Batch Processing**: Process multiple receipts simultaneously
5. **Custom Categories**: User-defined item categories
6. **OCR Alternatives**: Support for other OCR services (AWS Textract, Azure)

### Known Limitations
1. Address lines may be parsed as items (needs filtering improvement)
2. Complex receipt layouts may not parse perfectly
3. Handwritten receipts are not supported
4. Some store-specific formats may need custom handling

## Troubleshooting

### Common Issues

**OCR Not Working**
- Check Google Cloud credentials
- Verify Vision API is enabled
- Ensure `OCR_ENABLED=true` in environment

**Poor Item Extraction**
- Check receipt image quality
- Verify receipt format is supported
- Review parsing logs for specific issues

**Categorization Issues**
- Items default to "other" category if no keywords match
- Add custom keywords to `_categorize_item()` method

### Debugging

Enable detailed logging by setting `LOG_LEVEL=DEBUG` in your environment file.

## Conclusion

The OCR integration provides a robust foundation for receipt processing with intelligent text extraction, parsing, and categorization. The system is designed to handle various receipt formats while providing graceful fallbacks and comprehensive error handling.