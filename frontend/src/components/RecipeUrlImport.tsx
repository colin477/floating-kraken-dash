import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Globe,
  Link,
  CheckCircle,
  AlertCircle,
  Clock,
  Users,
  ChefHat,
  Tag,
  ExternalLink,
  Loader2,
  Info,
  X
} from 'lucide-react';
import { recipeImportApi } from '@/services/api';

// Simple Alert component since it's not available
const Alert: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = '' }) => (
  <div className={`border border-gray-200 rounded-lg p-4 ${className}`}>
    {children}
  </div>
);

const AlertDescription: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div className="text-sm text-gray-600">{children}</div>
);

// Simple Switch component since it's not available
const Switch: React.FC<{
  id?: string;
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
}> = ({ id, checked, onCheckedChange }) => (
  <button
    id={id}
    type="button"
    role="switch"
    aria-checked={checked}
    onClick={() => onCheckedChange(!checked)}
    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
      checked ? 'bg-blue-600' : 'bg-gray-200'
    }`}
  >
    <span
      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
        checked ? 'translate-x-6' : 'translate-x-1'
      }`}
    />
  </button>
);

interface RecipeImportPreview {
  title: string;
  description?: string;
  ingredients_count: number;
  instructions_count: number;
  prep_time?: number;
  cook_time?: number;
  servings: number;
  difficulty: string;
  meal_types: string[];
  dietary_restrictions: string[];
  tags: string[];
  photo_url?: string;
  source_domain: string;
  scraping_method: string;
  confidence_score: number;
}

interface RecipeImportResponse {
  success: boolean;
  status: string;
  recipe?: any;
  preview?: RecipeImportPreview;
  source_url: string;
  processing_time_ms: number;
  data_quality_score: number;
  completeness_score: number;
  error_message?: string;
  validation_issues?: string[];
  warnings?: string[];
  is_duplicate?: boolean;
  existing_recipe_id?: string;
  metadata?: any;
}

interface RecipeUrlValidationResponse {
  is_valid: boolean;
  is_supported: boolean;
  domain: string;
  is_accessible: boolean;
  validation_issues: string[];
  warnings: string[];
  page_title?: string;
  has_recipe_data?: boolean;
  estimated_confidence?: number;
  response_time_ms: number;
}

interface RecipeUrlImportProps {
  onImportSuccess?: (recipe: any) => void;
  onClose?: () => void;
  className?: string;
}

export const RecipeUrlImport: React.FC<RecipeUrlImportProps> = ({
  onImportSuccess,
  onClose,
  className = ''
}) => {
  const [url, setUrl] = useState('');
  const [customTags, setCustomTags] = useState('');
  const [overrideDuplicate, setOverrideDuplicate] = useState(false);
  const [isValidating, setIsValidating] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const [validationResult, setValidationResult] = useState<RecipeUrlValidationResponse | null>(null);
  const [importResult, setImportResult] = useState<RecipeImportResponse | null>(null);
  const [supportedDomains, setSupportedDomains] = useState<string[]>([]);
  const [showPreview, setShowPreview] = useState(false);

  // Load supported domains on component mount
  useEffect(() => {
    const loadSupportedDomains = async () => {
      try {
        const response = await recipeImportApi.getSupportedDomains();
        setSupportedDomains(response.domains || []);
      } catch (error) {
        console.error('Failed to load supported domains:', error);
      }
    };

    loadSupportedDomains();
  }, []);

  const validateUrl = async () => {
    if (!url.trim()) {
      return;
    }

    setIsValidating(true);
    setValidationResult(null);
    setImportResult(null);

    try {
      const result = await recipeImportApi.validateUrl(url.trim());
      setValidationResult(result);
    } catch (error) {
      console.error('URL validation failed:', error);
      setValidationResult({
        is_valid: false,
        is_supported: false,
        domain: '',
        is_accessible: false,
        validation_issues: [error instanceof Error ? error.message : 'Validation failed'],
        warnings: [],
        response_time_ms: 0
      });
    } finally {
      setIsValidating(false);
    }
  };

  const importRecipe = async () => {
    if (!url.trim()) {
      return;
    }

    setIsImporting(true);
    setImportResult(null);

    try {
      const tags = customTags
        .split(',')
        .map(tag => tag.trim())
        .filter(tag => tag.length > 0);

      const result = await recipeImportApi.importFromUrl({
        url: url.trim(),
        override_duplicate: overrideDuplicate,
        custom_tags: tags.length > 0 ? tags : undefined
      });

      setImportResult(result);

      if (result.success && result.recipe && onImportSuccess) {
        onImportSuccess(result.recipe);
      }
    } catch (error) {
      console.error('Recipe import failed:', error);
      setImportResult({
        success: false,
        status: 'failed',
        source_url: url,
        processing_time_ms: 0,
        data_quality_score: 0,
        completeness_score: 0,
        error_message: error instanceof Error ? error.message : 'Import failed'
      });
    } finally {
      setIsImporting(false);
    }
  };

  const handleUrlChange = (value: string) => {
    setUrl(value);
    setValidationResult(null);
    setImportResult(null);
    setShowPreview(false);
  };

  const handlePreviewToggle = () => {
    if (!showPreview && !validationResult) {
      validateUrl();
    }
    setShowPreview(!showPreview);
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty.toLowerCase()) {
      case 'easy': return 'bg-green-100 text-green-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'hard': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success': return 'text-green-600';
      case 'failed': return 'text-red-600';
      case 'duplicate': return 'text-yellow-600';
      case 'validation_error': return 'text-orange-600';
      default: return 'text-gray-600';
    }
  };

  const isUrlValid = url.trim().length > 0 && (url.startsWith('http://') || url.startsWith('https://'));

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Link className="h-5 w-5 text-blue-600" />
          <h2 className="text-xl font-semibold">Import Recipe from URL</h2>
        </div>
        {onClose && (
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        )}
      </div>

      {/* URL Input Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Globe className="h-4 w-4" />
            <span>Recipe URL</span>
          </CardTitle>
          <CardDescription>
            Enter the URL of a recipe from a supported website to import it into your collection.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="recipe-url">Recipe URL</Label>
            <div className="flex space-x-2">
              <Input
                id="recipe-url"
                type="url"
                placeholder="https://www.allrecipes.com/recipe/..."
                value={url}
                onChange={(e) => handleUrlChange(e.target.value)}
                className="flex-1"
              />
              <Button
                variant="outline"
                onClick={validateUrl}
                disabled={!isUrlValid || isValidating}
              >
                {isValidating ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <CheckCircle className="h-4 w-4" />
                )}
                Validate
              </Button>
            </div>
          </div>

          {/* Supported Domains */}
          {supportedDomains.length > 0 && (
            <div className="space-y-2">
              <Label className="text-sm font-medium">Supported Websites</Label>
              <div className="flex flex-wrap gap-1">
                {supportedDomains.slice(0, 8).map((domain) => (
                  <Badge key={domain} variant="secondary" className="text-xs">
                    {domain}
                  </Badge>
                ))}
                {supportedDomains.length > 8 && (
                  <Badge variant="secondary" className="text-xs">
                    +{supportedDomains.length - 8} more
                  </Badge>
                )}
              </div>
            </div>
          )}

          {/* Custom Tags */}
          <div className="space-y-2">
            <Label htmlFor="custom-tags">Custom Tags (optional)</Label>
            <Input
              id="custom-tags"
              placeholder="family-favorite, quick-meal, comfort-food"
              value={customTags}
              onChange={(e) => setCustomTags(e.target.value)}
            />
            <p className="text-xs text-gray-500">
              Separate multiple tags with commas
            </p>
          </div>

          {/* Override Duplicate */}
          <div className="flex items-center space-x-2">
            <Switch
              id="override-duplicate"
              checked={overrideDuplicate}
              onCheckedChange={setOverrideDuplicate}
            />
            <Label htmlFor="override-duplicate" className="text-sm">
              Import even if recipe already exists
            </Label>
          </div>
        </CardContent>
      </Card>

      {/* Validation Results */}
      {validationResult && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              {validationResult.is_valid ? (
                <CheckCircle className="h-4 w-4 text-green-600" />
              ) : (
                <AlertCircle className="h-4 w-4 text-red-600" />
              )}
              <span>URL Validation</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <p className="text-sm font-medium">Domain</p>
                <p className="text-sm text-gray-600">{validationResult.domain}</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm font-medium">Supported</p>
                <Badge variant={validationResult.is_supported ? "default" : "secondary"}>
                  {validationResult.is_supported ? "Yes" : "Limited"}
                </Badge>
              </div>
              <div className="space-y-1">
                <p className="text-sm font-medium">Accessible</p>
                <Badge variant={validationResult.is_accessible ? "default" : "destructive"}>
                  {validationResult.is_accessible ? "Yes" : "No"}
                </Badge>
              </div>
              {validationResult.estimated_confidence && (
                <div className="space-y-1">
                  <p className="text-sm font-medium">Confidence</p>
                  <Badge variant="outline">
                    {Math.round(validationResult.estimated_confidence * 100)}%
                  </Badge>
                </div>
              )}
            </div>

            {validationResult.page_title && (
              <div className="space-y-1">
                <p className="text-sm font-medium">Page Title</p>
                <p className="text-sm text-gray-600">{validationResult.page_title}</p>
              </div>
            )}

            {validationResult.validation_issues.length > 0 && (
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  <div className="space-y-1">
                    <p className="font-medium">Issues found:</p>
                    <ul className="list-disc list-inside space-y-1">
                      {validationResult.validation_issues.map((issue, index) => (
                        <li key={index} className="text-sm">{issue}</li>
                      ))}
                    </ul>
                  </div>
                </AlertDescription>
              </Alert>
            )}

            {validationResult.warnings.length > 0 && (
              <Alert>
                <Info className="h-4 w-4" />
                <AlertDescription>
                  <div className="space-y-1">
                    <p className="font-medium">Warnings:</p>
                    <ul className="list-disc list-inside space-y-1">
                      {validationResult.warnings.map((warning, index) => (
                        <li key={index} className="text-sm">{warning}</li>
                      ))}
                    </ul>
                  </div>
                </AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>
      )}

      {/* Import Results */}
      {importResult && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              {importResult.success ? (
                <CheckCircle className="h-4 w-4 text-green-600" />
              ) : (
                <AlertCircle className="h-4 w-4 text-red-600" />
              )}
              <span>Import Results</span>
              <Badge className={getStatusColor(importResult.status)}>
                {importResult.status.replace('_', ' ').toUpperCase()}
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {importResult.success && importResult.preview && (
              <div className="space-y-4">
                {/* Recipe Preview */}
                <div className="space-y-3">
                  <h3 className="font-semibold text-lg">{importResult.preview.title}</h3>
                  
                  {importResult.preview.description && (
                    <p className="text-gray-600 text-sm">{importResult.preview.description}</p>
                  )}

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="flex items-center space-x-2">
                      <ChefHat className="h-4 w-4 text-gray-500" />
                      <span className="text-sm">{importResult.preview.ingredients_count} ingredients</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Users className="h-4 w-4 text-gray-500" />
                      <span className="text-sm">{importResult.preview.servings} servings</span>
                    </div>
                    {importResult.preview.prep_time && (
                      <div className="flex items-center space-x-2">
                        <Clock className="h-4 w-4 text-gray-500" />
                        <span className="text-sm">{importResult.preview.prep_time}min prep</span>
                      </div>
                    )}
                    {importResult.preview.cook_time && (
                      <div className="flex items-center space-x-2">
                        <Clock className="h-4 w-4 text-gray-500" />
                        <span className="text-sm">{importResult.preview.cook_time}min cook</span>
                      </div>
                    )}
                  </div>

                  <div className="flex flex-wrap gap-2">
                    <Badge className={getDifficultyColor(importResult.preview.difficulty)}>
                      {importResult.preview.difficulty}
                    </Badge>
                    {importResult.preview.meal_types.map((type) => (
                      <Badge key={type} variant="outline">{type}</Badge>
                    ))}
                    {importResult.preview.dietary_restrictions.map((restriction) => (
                      <Badge key={restriction} variant="secondary">{restriction}</Badge>
                    ))}
                  </div>

                  {importResult.preview.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {importResult.preview.tags.map((tag) => (
                        <Badge key={tag} variant="outline" className="text-xs">
                          <Tag className="h-3 w-3 mr-1" />
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>

                <Separator />

                {/* Quality Metrics */}
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center">
                    <p className="text-2xl font-bold text-green-600">
                      {Math.round(importResult.data_quality_score * 100)}%
                    </p>
                    <p className="text-xs text-gray-500">Data Quality</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-blue-600">
                      {Math.round(importResult.completeness_score * 100)}%
                    </p>
                    <p className="text-xs text-gray-500">Completeness</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-purple-600">
                      {Math.round(importResult.processing_time_ms)}ms
                    </p>
                    <p className="text-xs text-gray-500">Processing Time</p>
                  </div>
                </div>
              </div>
            )}

            {!importResult.success && (
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  <div className="space-y-2">
                    <p className="font-medium">Import Failed</p>
                    <p>{importResult.error_message}</p>
                    
                    {importResult.validation_issues && importResult.validation_issues.length > 0 && (
                      <div>
                        <p className="font-medium mt-2">Issues:</p>
                        <ul className="list-disc list-inside space-y-1">
                          {importResult.validation_issues.map((issue, index) => (
                            <li key={index} className="text-sm">{issue}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </AlertDescription>
              </Alert>
            )}

            {importResult.is_duplicate && (
              <Alert>
                <Info className="h-4 w-4" />
                <AlertDescription>
                  This recipe already exists in your collection. Enable "Import even if recipe already exists" to import it anyway.
                </AlertDescription>
              </Alert>
            )}

            {importResult.warnings && importResult.warnings.length > 0 && (
              <Alert>
                <Info className="h-4 w-4" />
                <AlertDescription>
                  <div className="space-y-1">
                    <p className="font-medium">Warnings:</p>
                    <ul className="list-disc list-inside space-y-1">
                      {importResult.warnings.map((warning, index) => (
                        <li key={index} className="text-sm">{warning}</li>
                      ))}
                    </ul>
                  </div>
                </AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>
      )}

      {/* Action Buttons */}
      <div className="flex justify-end space-x-2">
        {onClose && (
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
        )}
        <Button
          onClick={importRecipe}
          disabled={!isUrlValid || isImporting || (validationResult && !validationResult.is_accessible)}
        >
          {isImporting ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
              Importing...
            </>
          ) : (
            <>
              <ExternalLink className="h-4 w-4 mr-2" />
              Import Recipe
            </>
          )}
        </Button>
      </div>
    </div>
  );
};

export default RecipeUrlImport;