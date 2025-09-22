import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Utensils, Clock, Crown, Check } from 'lucide-react';

interface TableSettingChoiceProps {
  onChoice: (level: 'basic' | 'medium' | 'full') => void;
}

export const TableSettingChoice = ({ onChoice }: TableSettingChoiceProps) => {
  const [selectedLevel, setSelectedLevel] = useState<'basic' | 'medium' | 'full' | null>(null);

  const options = [
    {
      id: 'basic' as const,
      title: 'Just give me a plate, I\'m hungry now!',
      subtitle: 'Free Tier',
      price: 'Free',
      description: 'Get started quickly and see the magic of AI meal planning.',
      icon: Utensils,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
      borderColor: 'border-green-200',
      features: [
        'Basic sign-up (2 minutes)',
        '5 receipt scans per month',
        'Basic pantry management',
        '1 shopping list per week',
        'Browse community recipes',
        'Basic leftover suggestions'
      ],
      limitations: [
        'No meal planning',
        'No store deals',
        'Can\'t post in community'
      ]
    },
    {
      id: 'medium' as const,
      title: 'I\'ll set a few utensils, makes the meal easier.',
      subtitle: 'Basic Plan',
      price: '$5-7/mo',
      description: 'Unlock real savings with full meal planning and grocery optimization.',
      icon: Clock,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
      borderColor: 'border-blue-200',
      popular: true,
      features: [
        'Everything in Free, plus:',
        'Unlimited receipt scanning',
        'Weekly meal planning',
        'Budget tracking',
        'Local store deals (1-2 stores)',
        'Export to grocery delivery',
        'Post in community'
      ],
      savings: 'Save 20-30% on groceries'
    },
    {
      id: 'full' as const,
      title: 'I\'m hosting a full dinner party. Let\'s do this right.',
      subtitle: 'Premium Plan',
      price: '$9-12/mo',
      description: 'Maximum personalization and convenience for serious meal planners.',
      icon: Crown,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
      borderColor: 'border-purple-200',
      features: [
        'Everything in Basic, plus:',
        'Advanced diet customization',
        'Family member profiles',
        'Multi-store deal comparison',
        'Real-time deal notifications',
        'Advanced leftover management',
        'Photo meal reverse-engineering',
        'Priority support'
      ],
      savings: 'Maximum savings & convenience'
    }
  ];

  const handleOptionClick = (optionId: 'basic' | 'medium' | 'full') => {
    setSelectedLevel(optionId);
    // Immediately proceed to next step when option is clicked
    onChoice(optionId);
  };

  const handleContinue = () => {
    if (selectedLevel) {
      onChoice(selectedLevel);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-50 to-blue-50 p-4">
      <Card className="w-full max-w-6xl">
        <CardHeader className="text-center">
          <CardTitle className="text-3xl font-bold text-gray-900 mb-2">
            Choose Your EZ Eatin' Plan
          </CardTitle>
          <CardDescription className="text-lg">
            Start with any plan and upgrade anytime. All plans include our core AI meal planning features.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-8">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
            {options.map((option) => {
              const Icon = option.icon;
              const isSelected = selectedLevel === option.id;
              
              return (
                <Card
                  key={option.id}
                  className={`cursor-pointer transition-all duration-200 hover:shadow-lg relative ${
                    isSelected 
                      ? `ring-2 ring-offset-2 ${option.color.replace('text-', 'ring-')} ${option.bgColor}` 
                      : 'hover:shadow-md'
                  } ${option.popular ? 'ring-2 ring-blue-500 ring-offset-2' : ''}`}
                  onClick={() => handleOptionClick(option.id)}
                >
                  {option.popular && (
                    <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                      <Badge className="bg-blue-500 text-white px-3 py-1">
                        Most Popular
                      </Badge>
                    </div>
                  )}
                  
                  <CardHeader className="text-center pb-4">
                    <div className={`mx-auto w-16 h-16 ${option.bgColor} rounded-full flex items-center justify-center mb-4`}>
                      <Icon className={`h-8 w-8 ${option.color}`} />
                    </div>
                    
                    <div className="mb-4">
                      <div className={`text-2xl font-bold ${option.color} mb-1`}>
                        {option.price}
                      </div>
                      <Badge variant="outline" className={`${option.color} border-current`}>
                        {option.subtitle}
                      </Badge>
                    </div>
                    
                    <CardTitle className="text-lg font-semibold mb-2 min-h-[3rem] flex items-center justify-center">
                      {option.title}
                    </CardTitle>
                    
                    <CardDescription className="text-sm">
                      {option.description}
                    </CardDescription>
                    
                    {option.savings && (
                      <div className={`text-sm font-medium ${option.color} mt-2`}>
                        💰 {option.savings}
                      </div>
                    )}
                  </CardHeader>
                  
                  <CardContent className="pt-0">
                    <div className="space-y-3 mb-6">
                      {option.features.map((feature, index) => (
                        <div key={index} className="flex items-start text-sm">
                          <Check className={`w-4 h-4 ${option.color} mr-2 mt-0.5 flex-shrink-0`} />
                          <span className={feature.startsWith('Everything') ? 'font-medium' : ''}>
                            {feature}
                          </span>
                        </div>
                      ))}
                    </div>
                    
                    {option.limitations && (
                      <div className="border-t pt-4">
                        <div className="text-xs text-gray-500 mb-2">Limitations:</div>
                        {option.limitations.map((limitation, index) => (
                          <div key={index} className="flex items-center text-xs text-gray-500">
                            <div className="w-2 h-2 bg-gray-300 rounded-full mr-2" />
                            {limitation}
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              );
            })}
          </div>

          {/* Optional continue button for users who want to review their choice */}
          {selectedLevel && (
            <div className="text-center">
              <p className="text-sm text-gray-600 mb-4">
                You selected: <span className="font-medium">{options.find(o => o.id === selectedLevel)?.subtitle}</span>
              </p>
              <Button 
                onClick={handleContinue}
                size="lg"
                className="px-8"
              >
                Continue to Setup
              </Button>
            </div>
          )}
          
          <div className="text-center mt-8 text-sm text-gray-500">
            <p>✨ All plans include AI-powered recipe suggestions and basic meal planning</p>
            <p>🔄 Upgrade or downgrade anytime • 💳 Cancel anytime</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};