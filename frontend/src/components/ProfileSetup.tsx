import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { UserProfile } from '@/types';
import { storage } from '@/lib/storage';
import { showSuccess } from '@/utils/toast';
import { Clock, Utensils, Crown, MapPin, Truck } from 'lucide-react';

interface ProfileSetupProps {
  userId: string;
  level: 'basic' | 'medium' | 'full';
  onComplete: () => void;
}

interface QuickAnswers {
  timePreference?: string;
  flavorAdventure?: string;
  mainIngredient?: string;
  familySize?: string;
  dietaryRestrictions?: string;
  eatingStyle?: string;
  weeklyBudget?: string;
  mealPace?: string;
  // Full setup questions
  foodMood?: string[];
  cookingStyle?: string;
  dietaryGoals?: string;
  cookingTime?: string;
  leftoversPreference?: string;
  pickyEaters?: string;
  mealsPerWeek?: string;
  shoppingStyle?: string;
  localDeals?: string;
  cookingChallenge?: string;
  kitchenGadgets?: string[];
  preferredGrocers?: string[];
}

// Grocer data structures
interface Grocer {
  id: string;
  name: string;
  type: 'local' | 'delivery';
  distance?: string;
  services?: string[];
}

// National delivery services (available everywhere)
const DELIVERY_GROCERS: Grocer[] = [
  { id: 'amazon-fresh', name: 'Amazon Fresh', type: 'delivery', services: ['Delivery', 'Same-day'] },
  { id: 'walmart-delivery', name: 'Walmart Grocery', type: 'delivery', services: ['Delivery', 'Pickup'] },
  { id: 'costco-delivery', name: 'Costco Same-Day', type: 'delivery', services: ['Delivery', 'Bulk orders'] },
  { id: 'target-shipt', name: 'Target (Shipt)', type: 'delivery', services: ['Delivery', 'Same-day'] },
  { id: 'instacart', name: 'Instacart', type: 'delivery', services: ['Multiple stores', 'Fast delivery'] },
  { id: 'kroger-delivery', name: 'Kroger Delivery', type: 'delivery', services: ['Delivery', 'Pickup'] },
  { id: 'safeway-delivery', name: 'Safeway Delivery', type: 'delivery', services: ['Delivery', 'DriveUp'] },
  { id: 'whole-foods', name: 'Whole Foods (Amazon)', type: 'delivery', services: ['Prime delivery', 'Pickup'] }
];

// Function to get local grocers based on zip code
const getLocalGrocers = (zipCode: string): Grocer[] => {
  if (!zipCode) return [];
  
  // Mock local grocers - in a real app, this would be an API call
  const localGrocers: Grocer[] = [
    { id: 'kroger-local', name: 'Kroger', type: 'local', distance: '0.8 mi', services: ['In-store', 'Pickup'] },
    { id: 'safeway-local', name: 'Safeway', type: 'local', distance: '1.2 mi', services: ['In-store', 'Pickup'] },
    { id: 'walmart-local', name: 'Walmart Supercenter', type: 'local', distance: '1.5 mi', services: ['In-store', 'Pickup'] },
    { id: 'target-local', name: 'Target', type: 'local', distance: '2.1 mi', services: ['In-store', 'Pickup'] },
    { id: 'whole-foods-local', name: 'Whole Foods Market', type: 'local', distance: '2.3 mi', services: ['In-store', 'Pickup'] },
    { id: 'costco-local', name: 'Costco Wholesale', type: 'local', distance: '3.2 mi', services: ['In-store', 'Bulk shopping'] },
    { id: 'trader-joes', name: 'Trader Joe\'s', type: 'local', distance: '2.8 mi', services: ['In-store only'] },
    { id: 'aldi-local', name: 'ALDI', type: 'local', distance: '1.9 mi', services: ['In-store', 'Curbside'] }
  ];
  
  return localGrocers;
};

const BASE_QUESTIONS = [
  {
    id: 'timePreference',
    title: 'Time Check',
    question: 'How fast do you want dinner on the table?',
    options: [
      { value: 'fast', label: '10–20 minutes, I\'m starving!', emoji: '⚡' },
      { value: 'medium', label: '30–40 minutes, I can stir a pot or two.', emoji: '🍳' },
      { value: 'slow', label: 'Take your time—slow and cozy works for me.', emoji: '🍲' }
    ]
  },
  {
    id: 'flavorAdventure',
    title: 'Flavor Adventure Level',
    question: 'Are you in the mood for comfort food or adventure?',
    options: [
      { value: 'classics', label: 'Stick to the classics I know and love.', emoji: '🏡' },
      { value: 'international', label: 'I\'ll try something new from around the world.', emoji: '🌍' },
      { value: 'surprise', label: 'Surprise me!', emoji: '🎲' }
    ]
  },
  {
    id: 'mainIngredient',
    title: 'Main Ingredient Vibe',
    question: 'What\'s the star of your plate tonight?',
    options: [
      { value: 'meat', label: 'Chicken or meat', emoji: '🍗' },
      { value: 'veggie', label: 'Veggie-based', emoji: '🥦' },
      { value: 'pasta', label: 'Pasta or grains', emoji: '🍝' },
      { value: 'no-preference', label: 'No clue—help me decide!', emoji: '❓' }
    ]
  },
  {
    id: 'familySize',
    title: 'Mouths to Feed',
    question: 'How many mouths are we feeding tonight?',
    options: [
      { value: 'solo', label: 'Just me', emoji: '🧍' },
      { value: 'couple', label: 'Two', emoji: '👩‍❤️‍👨' },
      { value: 'family', label: 'Family of 3–4', emoji: '👨‍👩‍👧' },
      { value: 'big-crew', label: 'Big crew (5+)', emoji: '👨‍👩‍👧‍👦👨‍👩‍👧' }
    ]
  }
];

const ADDITIONAL_QUESTIONS = [
  {
    id: 'dietaryRestrictions',
    title: 'Food Restrictions',
    question: 'Any foods we should never suggest?',
    options: [
      { value: 'allergies', label: 'Allergies', emoji: '🥜' },
      { value: 'dislikes', label: 'Dislikes (e.g., no red meat)', emoji: '🥩' },
      { value: 'everything', label: 'I eat everything', emoji: '✅' }
    ]
  },
  {
    id: 'eatingStyle',
    title: 'Eating Style',
    question: 'Do you follow a particular eating style?',
    options: [
      { value: 'balanced', label: 'Balanced / No preference', emoji: '🍽️' },
      { value: 'vegetarian', label: 'Vegetarian', emoji: '🥦' },
      { value: 'vegan', label: 'Vegan', emoji: '🌱' },
      { value: 'low-carb', label: 'Low-carb / Keto', emoji: '🥩' }
    ]
  },
  {
    id: 'weeklyBudget',
    title: 'Budget Sweet Spot',
    question: 'What\'s your weekly grocery budget sweet spot?',
    options: [
      { value: 'under-50', label: '<$50', emoji: '💵' },
      { value: '50-100', label: '$50–100', emoji: '💳' },
      { value: '100-150', label: '$100–150', emoji: '🛒' },
      { value: '150-plus', label: '$150+', emoji: '🥂' }
    ]
  },
  {
    id: 'mealPace',
    title: 'Meal Pace',
    question: 'Quick or cozy meals?',
    options: [
      { value: 'quick', label: 'Fast, easy, and done', emoji: '🏃' },
      { value: 'cozy', label: 'Slower meals are fine', emoji: '🕰️' }
    ]
  }
];

const FULL_QUESTIONS = [
  {
    id: 'foodMood',
    title: 'Food Mood',
    question: 'What\'s your food mood? (Pick up to 3)',
    multiSelect: true,
    maxSelections: 3,
    options: [
      { value: 'pasta-comfort', label: 'Pasta & comfort carbs', emoji: '🍝' },
      { value: 'fresh-healthy', label: 'Fresh + healthy', emoji: '🥗' },
      { value: 'classic-american', label: 'Classic American', emoji: '🍔' },
      { value: 'cozy-home', label: 'Cozy home cooking', emoji: '🥘' },
      { value: 'light-fancy', label: 'Light & fancy', emoji: '🍣' },
      { value: 'street-food', label: 'Street food vibes', emoji: '🌮' }
    ]
  },
  {
    id: 'cookingStyle',
    title: 'Cooking Style',
    question: 'What kind of cook are you?',
    options: [
      { value: 'shortcut', label: 'Shortcut chef (quick hacks, semi-homemade)', emoji: '⚡' },
      { value: 'recipe-follower', label: 'Recipe follower (step by step, please)', emoji: '🍳' },
      { value: 'freestyle', label: 'Freestyle cook (I wing it)', emoji: '🧑‍🍳' },
      { value: 'from-scratch', label: 'From-scratch master (I enjoy the process)', emoji: '👨‍🍳' }
    ]
  },
  {
    id: 'dietaryGoals',
    title: 'Dietary Goals',
    question: 'Any dietary goals we should support?',
    options: [
      { value: 'more-veggies', label: 'Eat more veggies', emoji: '🥦' },
      { value: 'weight-management', label: 'Weight management', emoji: '⚖️' },
      { value: 'high-protein', label: 'High-protein meals', emoji: '💪' },
      { value: 'budget-only', label: 'Stick to budget only', emoji: '💸' },
      { value: 'balanced', label: 'Balanced nutrition', emoji: '🍽️' },
      { value: 'no-goals', label: 'No goals, just feed me!', emoji: '🚫' }
    ]
  },
  {
    id: 'preferredGrocers',
    title: 'My Grocers',
    question: 'Where do you like to shop? (Select all that apply)',
    multiSelect: true,
    maxSelections: 10,
    isGrocerQuestion: true,
    options: [] // Will be populated dynamically
  },
  {
    id: 'cookingTime',
    title: 'Cooking Time',
    question: 'What\'s your ideal cooking time on a weeknight?',
    options: [
      { value: 'super-quick', label: '10–20 min (super quick)', emoji: '⚡' },
      { value: 'normal', label: '20–40 min (normal dinner)', emoji: '🍳' },
      { value: 'slow-cozy', label: '40+ min (slow & cozy cooking)', emoji: '🍲' }
    ]
  },
  {
    id: 'leftoversPreference',
    title: 'Leftovers',
    question: 'Do you like leftovers or fresh every time?',
    options: [
      { value: 'love-leftovers', label: 'Love leftovers (next-day meals rock!)', emoji: '✅' },
      { value: 'fresh-only', label: 'No thanks, I want fresh every time', emoji: '🚫' },
      { value: 'mix-it-up', label: 'Mix it up (some fresh, some reheats)', emoji: '♻️' }
    ]
  },
  {
    id: 'pickyEaters',
    title: 'Picky Eaters',
    question: 'Any picky eaters at the table?',
    options: [
      { value: 'no-picky', label: 'Just me, no picky eaters here', emoji: '🧍' },
      { value: 'picky-kids', label: 'Yes, kids with specific tastes', emoji: '👶' },
      { value: 'picky-partner', label: 'Partner with picky habits', emoji: '👩‍❤️‍👨' },
      { value: 'multiple-picky', label: 'Multiple picky eaters in the family', emoji: '👨‍👩‍👧‍👦' },
      { value: 'all-adventurous', label: 'We\'re all adventurous eaters', emoji: '🎲' }
    ]
  },
  {
    id: 'weeklyBudget',
    title: 'Budget Sweet Spot',
    question: 'What\'s your weekly grocery budget sweet spot?',
    options: [
      { value: 'under-50', label: '<$50', emoji: '💵' },
      { value: '50-100', label: '$50–100', emoji: '💳' },
      { value: '100-150', label: '$100–150', emoji: '🛒' },
      { value: '150-plus', label: '$150+', emoji: '🥂' }
    ]
  },
  {
    id: 'mealsPerWeek',
    title: 'Meal Frequency',
    question: 'How many meals do you usually prepare per week?',
    options: [
      { value: '1-2', label: '1–2 (occasional cooking)', emoji: '🍳' },
      { value: '3-5', label: '3–5 (a few times a week)', emoji: '🥗' },
      { value: '6-8', label: '6–8 (almost every day)', emoji: '🍲' },
      { value: '9-plus', label: '9+ (I cook all the time!)', emoji: '👨‍👩‍👧' }
    ]
  },
  {
    id: 'shoppingStyle',
    title: 'Shopping Style',
    question: 'How do you usually shop for groceries?',
    options: [
      { value: 'big-trip', label: 'In-store, one big trip', emoji: '🛒' },
      { value: 'delivery', label: 'Grocery delivery / pickup', emoji: '📦' },
      { value: 'multiple-small', label: 'Multiple small trips during the week', emoji: '🌀' },
      { value: 'no-system', label: 'No system—I shop when I feel like it', emoji: '🎲' }
    ]
  },
  {
    id: 'localDeals',
    title: 'Local Deals',
    question: 'Do you want us to find local grocery deals for you?',
    options: [
      { value: 'yes-save', label: 'Yes, help me save money', emoji: '✅' },
      { value: 'maybe', label: 'Maybe, I\'ll check it out', emoji: '🤔' },
      { value: 'no-favorite', label: 'No, I stick to my favorite store', emoji: '🚫' }
    ]
  },
  {
    id: 'cookingChallenge',
    title: 'Cooking Challenge',
    question: 'What\'s your biggest cooking challenge?',
    options: [
      { value: 'no-time', label: 'Not enough time', emoji: '⏱️' },
      { value: 'no-ideas', label: 'Running out of ideas', emoji: '💡' },
      { value: 'budget', label: 'Staying on budget', emoji: '💸' },
      { value: 'food-waste', label: 'Too many leftovers / food waste', emoji: '🧹' }
    ]
  },
  {
    id: 'kitchenGadgets',
    title: 'Kitchen Toolbox',
    question: 'What gadgets are in your kitchen toolbox?',
    multiSelect: true,
    maxSelections: 8,
    options: [
      { value: 'stove-oven', label: 'Stove & oven (the basics)', emoji: '🔥' },
      { value: 'slow-cooker', label: 'Slow cooker / Crockpot', emoji: '🍳' },
      { value: 'instant-pot', label: 'Instant Pot / Pressure cooker', emoji: '🍲' },
      { value: 'air-fryer', label: 'Air fryer', emoji: '🍟' },
      { value: 'toaster-oven', label: 'Toaster oven', emoji: '🍞' },
      { value: 'microwave', label: 'Microwave', emoji: '🍕' },
      { value: 'blender', label: 'Blender or food processor', emoji: '🥤' },
      { value: 'just-basics', label: 'None of the fancy stuff—just me & a pan', emoji: '🧑‍🍳' }
    ]
  }
];

export const ProfileSetup = ({ userId, level, onComplete }: ProfileSetupProps) => {
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<Partial<QuickAnswers>>({});
  const [selectedMultiple, setSelectedMultiple] = useState<string[]>([]);
  const [userZipCode, setUserZipCode] = useState('');

  const getQuestionsForLevel = () => {
    switch (level) {
      case 'basic':
        return BASE_QUESTIONS;
      case 'medium':
        return [...BASE_QUESTIONS, ...ADDITIONAL_QUESTIONS];
      case 'full':
        return FULL_QUESTIONS;
      default:
        return BASE_QUESTIONS;
    }
  };

  const questions = getQuestionsForLevel();

  const getSetupConfig = () => {
    switch (level) {
      case 'basic':
        return {
          title: 'Free Tier Setup',
          subtitle: 'Quick 4 questions to get you started with basic AI meal suggestions',
          icon: Utensils,
          color: 'text-green-600',
          planName: 'Free Plan'
        };
      case 'medium':
        return {
          title: 'Basic Plan Setup',
          subtitle: '8 questions to unlock meal planning and grocery savings',
          icon: Clock,
          color: 'text-blue-600',
          planName: 'Basic Plan ($5-7/mo)'
        };
      case 'full':
        return {
          title: 'Premium Plan Setup',
          subtitle: '12 questions for maximum personalization and family features',
          icon: Crown,
          color: 'text-purple-600',
          planName: 'Premium Plan ($9-12/mo)'
        };
      default:
        return {
          title: 'Profile Setup',
          subtitle: 'Let\'s get you started',
          icon: Utensils,
          color: 'text-green-600',
          planName: 'Free Plan'
        };
    }
  };

  const config = getSetupConfig();
  const Icon = config.icon;
  const question = questions[currentQuestion];

  // Get grocer options for the grocer question
  const getGrocerOptions = () => {
    const localGrocers = getLocalGrocers(userZipCode);
    const allGrocers = [...localGrocers, ...DELIVERY_GROCERS];
    
    return allGrocers.map(grocer => ({
      value: grocer.id,
      label: grocer.name,
      emoji: grocer.type === 'local' ? '🏪' : '🚚',
      distance: grocer.distance,
      services: grocer.services,
      type: grocer.type
    }));
  };

  // Update grocer options if this is the grocer question
  if (question?.isGrocerQuestion) {
    question.options = getGrocerOptions();
  }

  const handleAnswer = (value: string) => {
    if (question.multiSelect) {
      handleMultiSelectAnswer(value);
    } else {
      const newAnswers = {
        ...answers,
        [question.id]: value
      };
      setAnswers(newAnswers);
      setSelectedMultiple([]);

      // Move to next question or complete setup
      if (currentQuestion < questions.length - 1) {
        setCurrentQuestion(currentQuestion + 1);
      } else {
        completeSetup(newAnswers as QuickAnswers);
      }
    }
  };

  const handleMultiSelectAnswer = (value: string) => {
    const newSelected = selectedMultiple.includes(value)
      ? selectedMultiple.filter(item => item !== value)
      : [...selectedMultiple, value];
    
    setSelectedMultiple(newSelected);
  };

  const handleMultiSelectContinue = () => {
    const newAnswers = {
      ...answers,
      [question.id]: selectedMultiple
    };
    setAnswers(newAnswers);
    setSelectedMultiple([]);

    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
    } else {
      completeSetup(newAnswers as QuickAnswers);
    }
  };

  const completeSetup = (finalAnswers: QuickAnswers) => {
    // Convert answers to profile data
    const profile: UserProfile = {
      userId,
      dietaryRestrictions: getDietaryRestrictions(finalAnswers),
      allergies: getAllergies(finalAnswers),
      tastePreferences: getTastePreferences(finalAnswers),
      mealPreferences: getMealPreferences(finalAnswers),
      kitchenEquipment: getKitchenEquipment(finalAnswers),
      weeklyBudget: getWeeklyBudget(finalAnswers),
      zipCode: userZipCode,
      familyMembers: getFamilyMembers(finalAnswers),
      preferredGrocers: finalAnswers.preferredGrocers || []
    };

    storage.setProfile(profile);
    showSuccess('Profile setup complete! Let\'s start meal planning.');
    onComplete();
  };

  // Helper functions to convert answers to profile data
  const getDietaryRestrictions = (answers: QuickAnswers): string[] => {
    const restrictions: string[] = [];
    
    // From dietary goals
    if (answers.dietaryGoals === 'more-veggies') {
      restrictions.push('Vegetable-focused');
    } else if (answers.dietaryGoals === 'high-protein') {
      restrictions.push('High-protein');
    }
    
    // From eating style (medium questions)
    if (answers.eatingStyle === 'vegetarian') {
      restrictions.push('Vegetarian');
    } else if (answers.eatingStyle === 'vegan') {
      restrictions.push('Vegan');
    } else if (answers.eatingStyle === 'low-carb') {
      restrictions.push('Low-carb', 'Keto');
    }
    
    return [...new Set(restrictions)];
  };

  const getAllergies = (answers: QuickAnswers): string[] => {
    const allergies: string[] = [];
    
    if (answers.dietaryRestrictions === 'allergies') {
      allergies.push('Common allergies');
    }
    
    return allergies;
  };

  const getTastePreferences = (answers: QuickAnswers): string[] => {
    const preferences: string[] = [];
    
    // From food mood (full setup)
    if (answers.foodMood && Array.isArray(answers.foodMood)) {
      answers.foodMood.forEach(mood => {
        switch (mood) {
          case 'pasta-comfort': preferences.push('Pasta', 'Comfort Food'); break;
          case 'fresh-healthy': preferences.push('Fresh', 'Healthy'); break;
          case 'classic-american': preferences.push('American', 'Classic'); break;
          case 'cozy-home': preferences.push('Home Cooking', 'Comfort Food'); break;
          case 'light-fancy': preferences.push('Light', 'Elegant'); break;
          case 'street-food': preferences.push('Street Food', 'Casual'); break;
        }
      });
    }
    
    // From flavor adventure (basic/medium)
    if (answers.flavorAdventure) {
      switch (answers.flavorAdventure) {
        case 'classics': preferences.push('American', 'Comfort Food'); break;
        case 'international': preferences.push('International', 'Variety'); break;
        case 'surprise': preferences.push('Adventurous', 'Variety'); break;
      }
    }
    
    return [...new Set(preferences)];
  };

  const getMealPreferences = (answers: QuickAnswers): string[] => {
    const preferences: string[] = [];
    
    // From cooking time
    if (answers.cookingTime) {
      switch (answers.cookingTime) {
        case 'super-quick': preferences.push('Quick meals (under 20 min)'); break;
        case 'normal': preferences.push('Standard cooking time'); break;
        case 'slow-cozy': preferences.push('Slow cooking', 'Comfort meals'); break;
      }
    }
    
    // From cooking style
    if (answers.cookingStyle) {
      switch (answers.cookingStyle) {
        case 'shortcut': preferences.push('Quick hacks', 'Semi-homemade'); break;
        case 'recipe-follower': preferences.push('Step-by-step recipes'); break;
        case 'freestyle': preferences.push('Flexible recipes'); break;
        case 'from-scratch': preferences.push('From-scratch cooking'); break;
      }
    }
    
    // From leftovers preference
    if (answers.leftoversPreference) {
      switch (answers.leftoversPreference) {
        case 'love-leftovers': preferences.push('Batch cooking', 'Meal prep'); break;
        case 'fresh-only': preferences.push('Fresh meals only'); break;
        case 'mix-it-up': preferences.push('Variety'); break;
      }
    }
    
    // From picky eaters
    if (answers.pickyEaters) {
      switch (answers.pickyEaters) {
        case 'picky-kids': preferences.push('Kid-friendly'); break;
        case 'picky-partner': preferences.push('Simple flavors'); break;
        case 'multiple-picky': preferences.push('Family-friendly', 'Simple'); break;
        case 'all-adventurous': preferences.push('Adventurous', 'International'); break;
      }
    }
    
    return [...new Set(preferences)];
  };

  const getKitchenEquipment = (answers: QuickAnswers): string[] => {
    const equipment: string[] = [];
    
    if (answers.kitchenGadgets && Array.isArray(answers.kitchenGadgets)) {
      answers.kitchenGadgets.forEach(gadget => {
        switch (gadget) {
          case 'stove-oven': equipment.push('Stove & oven'); break;
          case 'slow-cooker': equipment.push('Slow cooker'); break;
          case 'instant-pot': equipment.push('Instant Pot'); break;
          case 'air-fryer': equipment.push('Air fryer'); break;
          case 'toaster-oven': equipment.push('Toaster oven'); break;
          case 'microwave': equipment.push('Microwave'); break;
          case 'blender': equipment.push('Blender'); break;
          case 'just-basics': equipment.push('Basic cookware only'); break;
        }
      });
    }
    
    return equipment;
  };

  const getWeeklyBudget = (answers: QuickAnswers): number => {
    if (answers.weeklyBudget) {
      switch (answers.weeklyBudget) {
        case 'under-50': return 40;
        case '50-100': return 75;
        case '100-150': return 125;
        case '150-plus': return 200;
      }
    }
    
    // Fallback
    return 100;
  };

  const getFamilyMembers = (answers: QuickAnswers) => {
    return [];
  };

  const goBack = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(currentQuestion - 1);
      setSelectedMultiple([]);
    }
  };

  const canContinueMultiSelect = () => {
    return selectedMultiple.length > 0 && selectedMultiple.length <= (question.maxSelections || 3);
  };

  // Special rendering for grocer question
  const renderGrocerQuestion = () => {
    const localGrocers = getLocalGrocers(userZipCode);
    const hasZipCode = userZipCode.trim().length > 0;

    return (
      <div className="space-y-6">
        {/* Zip Code Input */}
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            {question.title}
          </h2>
          <p className="text-lg text-gray-600 mb-4">
            First, what's your zip code? This helps us find local stores near you.
          </p>
          <div className="max-w-xs mx-auto">
            <input
              type="text"
              value={userZipCode}
              onChange={(e) => setUserZipCode(e.target.value)}
              placeholder="Enter zip code"
              className="w-full px-4 py-2 border border-gray-300 rounded-md text-center text-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
              maxLength={5}
            />
          </div>
        </div>

        {/* Grocer Selection */}
        {hasZipCode && (
          <div className="space-y-6">
            <div className="text-center">
              <p className="text-lg text-gray-600">
                {question.question}
              </p>
              {question.multiSelect && (
                <p className="text-sm text-gray-500 mt-2">
                  Selected: {selectedMultiple.length} / {question.maxSelections || 10}
                </p>
              )}
            </div>

            {/* Local Grocers */}
            {localGrocers.length > 0 && (
              <div>
                <div className="flex items-center justify-center mb-4">
                  <MapPin className="h-4 w-4 mr-2 text-blue-600" />
                  <h3 className="text-lg font-medium">Local Stores Near You</h3>
                  <Badge variant="outline" className="ml-2 text-xs">
                    {userZipCode}
                  </Badge>
                </div>
                <div className="grid gap-3">
                  {localGrocers.map(grocer => {
                    const option = question.options.find(opt => opt.value === grocer.id);
                    if (!option) return null;
                    
                    return (
                      <Button
                        key={grocer.id}
                        variant={selectedMultiple.includes(grocer.id) ? "default" : "outline"}
                        className="w-full p-4 h-auto text-left justify-start hover:bg-gray-50 hover:border-gray-300 transition-all"
                        onClick={() => handleAnswer(grocer.id)}
                        disabled={!selectedMultiple.includes(grocer.id) && selectedMultiple.length >= (question.maxSelections || 10)}
                      >
                        <div className="flex items-center justify-between w-full">
                          <div className="flex items-center space-x-3">
                            <span className="text-xl">🏪</span>
                            <div>
                              <div className="font-medium">{grocer.name}</div>
                              <div className="flex items-center gap-2 mt-1">
                                <span className="text-xs text-gray-500">{grocer.distance}</span>
                                <div className="flex gap-1">
                                  {grocer.services?.map(service => (
                                    <Badge key={service} variant="secondary" className="text-xs">
                                      {service}
                                    </Badge>
                                  ))}
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      </Button>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Delivery Services */}
            <div>
              <div className="flex items-center justify-center mb-4">
                <Truck className="h-4 w-4 mr-2 text-green-600" />
                <h3 className="text-lg font-medium">Delivery Services</h3>
                <Badge variant="outline" className="ml-2 text-xs">
                  Available Nationwide
                </Badge>
              </div>
              <div className="grid gap-3">
                {DELIVERY_GROCERS.map(grocer => {
                  const option = question.options.find(opt => opt.value === grocer.id);
                  if (!option) return null;
                  
                  return (
                    <Button
                      key={grocer.id}
                      variant={selectedMultiple.includes(grocer.id) ? "default" : "outline"}
                      className="w-full p-4 h-auto text-left justify-start hover:bg-gray-50 hover:border-gray-300 transition-all"
                      onClick={() => handleAnswer(grocer.id)}
                      disabled={!selectedMultiple.includes(grocer.id) && selectedMultiple.length >= (question.maxSelections || 10)}
                    >
                      <div className="flex items-center justify-between w-full">
                        <div className="flex items-center space-x-3">
                          <span className="text-xl">🚚</span>
                          <div>
                            <div className="font-medium">{grocer.name}</div>
                            <div className="flex gap-1 mt-1">
                              {grocer.services?.map(service => (
                                <Badge key={service} variant="secondary" className="text-xs">
                                  {service}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>
                    </Button>
                  );
                })}
              </div>
            </div>

            {/* Multi-select selections display */}
            {selectedMultiple.length > 0 && (
              <div className="text-center">
                <div className="flex flex-wrap gap-2 justify-center mb-4">
                  {selectedMultiple.map(selection => {
                    const grocer = [...localGrocers, ...DELIVERY_GROCERS].find(g => g.id === selection);
                    return grocer ? (
                      <Badge key={selection} variant="secondary" className="text-sm">
                        {grocer.type === 'local' ? '🏪' : '🚚'} {grocer.name}
                      </Badge>
                    ) : null;
                  })}
                </div>
                <Button 
                  onClick={handleMultiSelectContinue}
                  disabled={!canContinueMultiSelect()}
                  size="lg"
                >
                  Continue
                </Button>
              </div>
            )}
          </div>
        )}

        {/* No zip code message */}
        {!hasZipCode && (
          <div className="text-center py-8 text-gray-500">
            <p>Enter your zip code above to see local grocery stores and delivery options</p>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-50 to-blue-50 p-4">
      <Card className="w-full max-w-2xl">
        <CardHeader>
          <div className="flex items-center justify-center mb-4">
            <div className="p-3 bg-white rounded-full shadow-sm">
              <Icon className={`h-8 w-8 ${config.color}`} />
            </div>
          </div>
          <CardTitle className="text-center">{config.title}</CardTitle>
          <CardDescription className="text-center">
            {config.subtitle}
            <span className="block mt-2">
              <Badge variant="outline" className={config.color}>
                {config.planName}
              </Badge>
            </span>
            <span className="block mt-1">
              Question {currentQuestion + 1} of {questions.length}
            </span>
          </CardDescription>
          
          {/* Progress bar */}
          <div className="w-full bg-gray-200 rounded-full h-2 mt-4">
            <div 
              className={`h-2 rounded-full transition-all duration-300 ${
                level === 'basic' ? 'bg-green-600' : 
                level === 'medium' ? 'bg-blue-600' : 'bg-purple-600'
              }`}
              style={{ width: `${((currentQuestion + 1) / questions.length) * 100}%` }}
            />
          </div>
        </CardHeader>
        
        <CardContent className="space-y-8">
          {/* Special rendering for grocer question */}
          {question?.isGrocerQuestion ? renderGrocerQuestion() : (
            <>
              {/* Question */}
              <div className="text-center">
                <h2 className="text-2xl font-bold text-gray-900 mb-2">
                  {question.title}
                </h2>
                <p className="text-lg text-gray-600">
                  {question.question}
                </p>
                {question.multiSelect && (
                  <p className="text-sm text-gray-500 mt-2">
                    Selected: {selectedMultiple.length} / {question.maxSelections || 3}
                  </p>
                )}
              </div>

              {/* Multi-select selections display */}
              {question.multiSelect && selectedMultiple.length > 0 && (
                <div className="flex flex-wrap gap-2 justify-center">
                  {selectedMultiple.map(selection => {
                    const option = question.options.find(opt => opt.value === selection);
                    return (
                      <Badge key={selection} variant="secondary" className="text-sm">
                        {option?.emoji} {option?.label}
                      </Badge>
                    );
                  })}
                </div>
              )}

              {/* Answer Options */}
              <div className="space-y-4">
                {question.options.map((option) => (
                  <Button
                    key={option.value}
                    variant={question.multiSelect && selectedMultiple.includes(option.value) ? "default" : "outline"}
                    className="w-full p-6 h-auto text-left justify-start hover:bg-gray-50 hover:border-gray-300 transition-all"
                    onClick={() => handleAnswer(option.value)}
                    disabled={question.multiSelect && !selectedMultiple.includes(option.value) && selectedMultiple.length >= (question.maxSelections || 3)}
                  >
                    <div className="flex items-center space-x-4">
                      <span className="text-2xl">{option.emoji}</span>
                      <span className="text-lg">{option.label}</span>
                    </div>
                  </Button>
                ))}
              </div>

              {/* Multi-select continue button */}
              {question.multiSelect && (
                <div className="text-center">
                  <Button 
                    onClick={handleMultiSelectContinue}
                    disabled={!canContinueMultiSelect()}
                    size="lg"
                  >
                    Continue
                  </Button>
                </div>
              )}
            </>
          )}

          {/* Navigation */}
          <div className="flex justify-between pt-4">
            <Button
              variant="ghost"
              onClick={goBack}
              disabled={currentQuestion === 0}
              className="text-gray-500"
            >
              ← Previous
            </Button>
            
            <div className="text-sm text-gray-500 flex items-center">
              {currentQuestion + 1} / {questions.length}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};