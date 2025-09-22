import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, Camera, Upload, Loader2, Check } from 'lucide-react';
import { simulateReceiptProcessing } from '@/lib/mockData';
import { storage } from '@/lib/storage';
import { PantryItem, ReceiptItem } from '@/types';
import { showSuccess } from '@/utils/toast';

interface ReceiptScanProps {
  onBack: () => void;
}

export const ReceiptScan = ({ onBack }: ReceiptScanProps) => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [processedItems, setProcessedItems] = useState<ReceiptItem[]>([]);
  const [step, setStep] = useState<'upload' | 'processing' | 'review' | 'complete'>('upload');

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setStep('processing');
    setIsProcessing(true);

    try {
      // Simulate AI processing
      const items = await simulateReceiptProcessing(URL.createObjectURL(file));
      setProcessedItems(items);
      setStep('review');
    } catch (error) {
      console.error('Error processing receipt:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleAddToPantry = () => {
    const pantryItems: PantryItem[] = processedItems.map(item => ({
      id: Date.now().toString() + Math.random(),
      name: item.name,
      quantity: item.quantity,
      unit: 'pieces', // Default unit
      source: 'receipt',
      addedAt: new Date().toISOString()
    }));

    const existingItems = storage.getPantryItems();
    storage.setPantryItems([...existingItems, ...pantryItems]);
    
    setStep('complete');
    showSuccess(`Added ${pantryItems.length} items to your pantry!`);
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
      </div>

      <div className="space-y-4">
        <label className="block">
          <input
            type="file"
            accept="image/*"
            capture="environment"
            onChange={handleFileUpload}
            className="hidden"
          />
          <Button className="w-full" size="lg">
            <Camera className="h-5 w-5 mr-2" />
            Take Photo
          </Button>
        </label>

        <label className="block">
          <input
            type="file"
            accept="image/*"
            onChange={handleFileUpload}
            className="hidden"
          />
          <Button variant="outline" className="w-full" size="lg">
            <Upload className="h-5 w-5 mr-2" />
            Upload Image
          </Button>
        </label>
      </div>

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
        <Button onClick={handleAddToPantry} className="flex-1">
          Add to Pantry
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
          </CardContent>
        </Card>
      </div>
    </div>
  );
};