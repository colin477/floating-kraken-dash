import { useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, Camera, Upload, Loader2, Check, AlertCircle, TestTube } from 'lucide-react';
import { receiptApi, pantryApi } from '@/services/api';
import { storage } from '@/lib/storage';
import { PantryItem, ReceiptItem, PantryCategory, PantryUnit } from '@/types';
import { showSuccess, showError } from '@/utils/toast';
import { shouldUseMockData, shouldShowDemoIndicator } from '@/lib/demoMode';

interface ReceiptScanProps {
  onBack: () => void;
}

export const ReceiptScan = ({ onBack }: ReceiptScanProps) => {
  const cameraInputRef = useRef<HTMLInputElement>(null);
  const uploadInputRef = useRef<HTMLInputElement>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processedItems, setProcessedItems] = useState<ReceiptItem[]>([]);
  const [step, setStep] = useState<'upload' | 'processing' | 'review' | 'complete' | 'error'>('upload');
  const [error, setError] = useState<string | null>(null);

  // Demo receipt options
  const demoReceipts = [
    { name: 'Grocery Mart Receipt', file: 'demo-receipt-1.svg', description: 'Chicken, vegetables, rice, and dairy items' },
    { name: 'Fresh Foods Market Receipt', file: 'demo-receipt-2.svg', description: 'Turkey, pasta, cheese, and produce items' }
  ];

  const handleDemoReceiptSelect = async (demoReceipt: typeof demoReceipts[0]) => {
    if (!shouldUseMockData()) {
      showError('Demo mode is not enabled. Enable demo mode to use sample receipts.');
      return;
    }

    setStep('processing');
    setIsProcessing(true);
    setError(null);

    try {
      console.log('🧪 [Demo Mode] Processing demo receipt:', demoReceipt.name);
      
      // Create a mock file object for the demo receipt
      const mockFile = new File(['demo'], demoReceipt.file, { type: 'image/svg+xml' });
      const result = await receiptApi.uploadAndProcess(mockFile);
      console.log('🧪 [Demo Mode] Demo receipt processing result:', result);
      
      // Convert API response to ReceiptItem format
      const items: ReceiptItem[] = result.items?.map((item: any) => ({
        name: item.name,
        quantity: item.quantity || 1,
        price: item.price || 0,
        category: item.category || 'Other'
      })) || [];
      
      setProcessedItems(items);
      setStep('review');
      showSuccess(`Demo receipt processed! Found ${items.length} items.`);
    } catch (error) {
      console.error('Error processing demo receipt:', error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to process demo receipt';
      setError(errorMessage);
      setStep('error');
      showError(errorMessage);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
      showError('Please select an image file (JPG, PNG, HEIC)');
      return;
    }

    // Validate file size (10MB limit)
    if (file.size > 10 * 1024 * 1024) {
      showError('File size must be less than 10MB');
      return;
    }

    setStep('processing');
    setIsProcessing(true);
    setError(null);

    try {
      console.log('🧾 Uploading receipt file:', file.name);
      const result = await receiptApi.uploadAndProcess(file);
      console.log('🧾 Receipt processing result:', result);
      
      // Convert API response to ReceiptItem format
      const items: ReceiptItem[] = result.items?.map((item: any) => ({
        name: item.name,
        quantity: item.quantity || 1,
        price: item.price || 0,
        category: item.category || 'Other'
      })) || [];
      
      setProcessedItems(items);
      setStep('review');
    } catch (error) {
      console.error('Error processing receipt:', error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to process receipt';
      setError(errorMessage);
      setStep('error');
      showError(errorMessage);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleAddToPantry = async () => {
    setIsProcessing(true);
    
    try {
      // Map receipt items to pantry item creation requests
      const pantryItemPromises = processedItems.map(item => {
        // Map category string to PantryCategory enum
        const categoryMap: Record<string, PantryCategory> = {
          'produce': PantryCategory.PRODUCE,
          'dairy': PantryCategory.DAIRY,
          'meat': PantryCategory.MEAT,
          'seafood': PantryCategory.SEAFOOD,
          'grains': PantryCategory.GRAINS,
          'canned goods': PantryCategory.CANNED_GOODS,
          'frozen': PantryCategory.FROZEN,
          'beverages': PantryCategory.BEVERAGES,
          'snacks': PantryCategory.SNACKS,
          'condiments': PantryCategory.CONDIMENTS,
          'spices': PantryCategory.SPICES,
          'baking': PantryCategory.BAKING,
        };
        
        const category = categoryMap[item.category.toLowerCase()] || PantryCategory.OTHER;
        
        return pantryApi.createItem({
          name: item.name,
          category: category,
          quantity: item.quantity,
          unit: PantryUnit.PIECE, // Default unit
          purchase_date: new Date().toISOString().split('T')[0], // Today's date
          notes: `Added from receipt scan`
        });
      });

      // Wait for all items to be created
      await Promise.all(pantryItemPromises);
      
      setStep('complete');
      showSuccess(`Added ${processedItems.length} items to your pantry!`);
    } catch (error) {
      console.error('Error adding items to pantry:', error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to add items to pantry';
      showError(errorMessage);
    } finally {
      setIsProcessing(false);
    }
  };

  const renderUploadStep = () => (
    <div className="text-center space-y-6">
      <div className="mx-auto w-24 h-24 bg-green-100 rounded-full flex items-center justify-center">
        <Camera className="h-12 w-12 text-green-600" />
      </div>
      
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Scan Your Receipt</h2>
        <p className="text-gray-600">
          Take a photo or upload an image of your grocery receipt. Our AI will identify all items and add them to your virtual pantry.
        </p>
        {shouldShowDemoIndicator() && (
          <div className="mt-3 inline-flex items-center px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-800">
            <TestTube className="h-4 w-4 mr-1" />
            Demo Mode Active
          </div>
        )}
      </div>

      <div className="space-y-4">
        <input
          ref={cameraInputRef}
          type="file"
          accept="image/*"
          capture="environment"
          onChange={handleFileUpload}
          className="hidden"
        />
        <Button
          className="w-full"
          size="lg"
          onClick={() => cameraInputRef.current?.click()}
        >
          <Camera className="h-5 w-5 mr-2" />
          Take Photo
        </Button>

        <input
          ref={uploadInputRef}
          type="file"
          accept="image/*"
          onChange={handleFileUpload}
          className="hidden"
        />
        <Button
          variant="outline"
          className="w-full"
          size="lg"
          onClick={() => uploadInputRef.current?.click()}
        >
          <Upload className="h-5 w-5 mr-2" />
          Upload Image
        </Button>
      </div>

      {/* Demo Mode Section */}
      {shouldUseMockData() && (
        <div className="border-t pt-6">
          <div className="mb-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Try Demo Receipts</h3>
            <p className="text-sm text-gray-600">
              Test the receipt scanning feature with these sample receipts
            </p>
          </div>
          
          <div className="space-y-3">
            {demoReceipts.map((receipt, index) => (
              <div key={index} className="border rounded-lg p-4 text-left">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-900">{receipt.name}</h4>
                    <p className="text-sm text-gray-600 mt-1">{receipt.description}</p>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleDemoReceiptSelect(receipt)}
                    disabled={isProcessing}
                  >
                    <TestTube className="h-4 w-4 mr-1" />
                    Try This
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="text-sm text-gray-500">
        <p>Supported formats: JPG, PNG, HEIC</p>
        <p>For best results, ensure the receipt is well-lit and all text is visible</p>
      </div>
    </div>
  );

  const renderProcessingStep = () => (
    <div className="text-center space-y-6">
      <div className="mx-auto w-24 h-24 bg-blue-100 rounded-full flex items-center justify-center">
        <Loader2 className="h-12 w-12 text-blue-600 animate-spin" />
      </div>
      
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Processing Receipt</h2>
        <p className="text-gray-600">
          Our AI is analyzing your receipt and identifying all purchased items...
        </p>
      </div>

      <div className="space-y-2">
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div className="bg-blue-600 h-2 rounded-full animate-pulse" style={{ width: '60%' }} />
        </div>
        <p className="text-sm text-gray-500">This usually takes 10-30 seconds</p>
      </div>
    </div>
  );

  const renderReviewStep = () => (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Review Identified Items</h2>
        <p className="text-gray-600">
          We found {processedItems.length} items. Review and confirm to add them to your pantry.
        </p>
      </div>

      <div className="grid gap-3 max-h-96 overflow-y-auto">
        {processedItems.map((item, index) => (
          <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
            <div className="flex-1">
              <h4 className="font-medium">{item.name}</h4>
              <div className="flex items-center gap-2 mt-1">
                <Badge variant="outline" className="text-xs">
                  Qty: {item.quantity}
                </Badge>
                <Badge variant="outline" className="text-xs">
                  ${item.price.toFixed(2)}
                </Badge>
                <Badge variant="secondary" className="text-xs">
                  {item.category}
                </Badge>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="flex gap-3">
        <Button variant="outline" onClick={() => setStep('upload')} className="flex-1">
          Scan Another
        </Button>
        <Button onClick={handleAddToPantry} disabled={isProcessing} className="flex-1">
          {isProcessing ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Adding...
            </>
          ) : (
            'Add to Pantry'
          )}
        </Button>
      </div>
    </div>
  );

  const renderCompleteStep = () => (
    <div className="text-center space-y-6">
      <div className="mx-auto w-24 h-24 bg-green-100 rounded-full flex items-center justify-center">
        <Check className="h-12 w-12 text-green-600" />
      </div>
      
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Items Added Successfully!</h2>
        <p className="text-gray-600">
          Your pantry has been updated with {processedItems.length} new items. Ready to create some recipes?
        </p>
      </div>

      <div className="space-y-3">
        <Button onClick={onBack} className="w-full" size="lg">
          Back to Dashboard
        </Button>
        <Button variant="outline" onClick={() => setStep('upload')} className="w-full">
          Scan Another Receipt
        </Button>
      </div>
    </div>
  );

  const renderErrorStep = () => (
    <div className="text-center space-y-6">
      <div className="mx-auto w-24 h-24 bg-red-100 rounded-full flex items-center justify-center">
        <AlertCircle className="h-12 w-12 text-red-600" />
      </div>
      
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Upload Failed</h2>
        <p className="text-gray-600 mb-4">
          We couldn't process your receipt. Please try again.
        </p>
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-left">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}
      </div>

      <div className="space-y-3">
        <Button onClick={() => setStep('upload')} className="w-full" size="lg">
          Try Again
        </Button>
        <Button variant="outline" onClick={onBack} className="w-full">
          Back to Dashboard
        </Button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center py-4">
            <Button variant="ghost" onClick={onBack} className="mr-4">
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <div>
              <h1 className="text-xl font-semibold">Receipt Scanner</h1>
              <p className="text-sm text-gray-600">AI-powered grocery receipt processing</p>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Card>
          <CardContent className="p-8">
            {step === 'upload' && renderUploadStep()}
            {step === 'processing' && renderProcessingStep()}
            {step === 'review' && renderReviewStep()}
            {step === 'complete' && renderCompleteStep()}
            {step === 'error' && renderErrorStep()}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};