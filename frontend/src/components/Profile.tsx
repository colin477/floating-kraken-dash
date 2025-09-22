import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { ArrowLeft, User, DollarSign, Users, MapPin, Plus, Save, Edit, Trash2, Heart, ThumbsDown, AlertTriangle, ChefHat, Store, Truck } from 'lucide-react';
import { User as UserType, UserProfile, FamilyMember } from '@/types';
import { storage } from '@/lib/storage';
import { showSuccess, showError } from '@/utils/toast';
import { AutocompleteField } from '@/components/AutocompleteField';

interface ProfileProps {
  user: UserType;
  profile: UserProfile;
  onBack: () => void;
  onLogout: () => void;
}

// Common options for autocomplete fields
const COMMON_ALLERGIES = [
  'Peanuts', 'Tree nuts', 'Shellfish', 'Fish', 'Milk', 'Eggs', 'Soy', 'Wheat', 'Gluten',
  'Sesame', 'Mustard', 'Celery', 'Lupin', 'Mollusks', 'Sulfites', 'Corn', 'Coconut',
  'Kiwi', 'Strawberries', 'Tomatoes', 'Chocolate', 'Food coloring', 'Preservatives'
];

const COMMON_LOVED_FOODS = [
  'Pizza', 'Pasta', 'Chicken nuggets', 'French fries', 'Ice cream', 'Chocolate', 'Cookies',
  'Burgers', 'Hot dogs', 'Mac and cheese', 'Grilled cheese', 'Pancakes', 'Waffles',
  'Tacos', 'Spaghetti', 'Meatballs', 'Fried chicken', 'Sandwiches', 'Cereal', 'Fruit',
  'Yogurt', 'Cheese', 'Bread', 'Rice', 'Noodles', 'Soup', 'Salad', 'Steak', 'Salmon',
  'Shrimp', 'Sushi', 'Chinese food', 'Mexican food', 'Italian food', 'Thai food'
];

const COMMON_DISLIKED_FOODS = [
  'Vegetables', 'Broccoli', 'Brussels sprouts', 'Spinach', 'Kale', 'Cauliflower',
  'Mushrooms', 'Onions', 'Garlic', 'Tomatoes', 'Peppers', 'Spicy food', 'Fish',
  'Seafood', 'Liver', 'Olives', 'Blue cheese', 'Cottage cheese', 'Tofu', 'Beans',
  'Lentils', 'Quinoa', 'Avocado', 'Coconut', 'Raisins', 'Nuts', 'Seeds', 'Pickles',
  'Sauerkraut', 'Anchovies', 'Caviar', 'Oysters', 'Exotic meats', 'Very sweet foods'
];

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

export const Profile = ({ user, profile, onBack, onLogout }: ProfileProps) => {
  const [isEditing, setIsEditing] = useState(false);
  const [showAddMember, setShowAddMember] = useState(false);
  const [editedProfile, setEditedProfile] = useState<UserProfile>(profile);
  const [localGrocers, setLocalGrocers] = useState<Grocer[]>([]);
  const [newMember, setNewMember] = useState({
    name: '',
    age: '',
    dietaryRestrictions: [] as string[],
    allergies: [] as string[],
    lovedFoods: [] as string[],
    dislikedFoods: [] as string[]
  });

  const availableDietaryRestrictions = [
    'Vegetarian', 'Vegan', 'Gluten-free', 'Dairy-free', 'Nut-free', 
    'Low-carb', 'Keto', 'Paleo', 'Mediterranean', 'Low-sodium'
  ];

  const availableTastePreferences = [
    'Sweet', 'Savory', 'Spicy', 'Mild', 'Sour', 'Bitter', 'Umami',
    'Comfort food', 'International cuisine', 'Fresh ingredients'
  ];

  const availableMealPreferences = [
    'Quick meals (under 30 min)', 'One-pot meals', 'Make-ahead meals',
    'Freezer-friendly', 'Leftover-friendly', 'Kid-friendly', 'Healthy options',
    'Budget-friendly', 'Gourmet cooking', 'Simple ingredients'
  ];

  const availableKitchenEquipment = [
    'Oven', 'Stovetop', 'Microwave', 'Slow cooker', 'Instant Pot', 'Air fryer',
    'Blender', 'Food processor', 'Stand mixer', 'Grill', 'Toaster oven'
  ];

  useEffect(() => {
    setEditedProfile(profile);
    // Update local grocers when zip code changes
    setLocalGrocers(getLocalGrocers(profile.zipCode));
  }, [profile]);

  // Update local grocers when zip code is edited
  useEffect(() => {
    setLocalGrocers(getLocalGrocers(editedProfile.zipCode));
  }, [editedProfile.zipCode]);

  const handleSave = () => {
    storage.setProfile(editedProfile);
    setIsEditing(false);
    showSuccess('Profile updated successfully!');
  };

  const handleCancel = () => {
    setEditedProfile(profile);
    setIsEditing(false);
  };

  const handleArrayToggle = (array: keyof UserProfile, item: string) => {
    setEditedProfile(prev => {
      const currentArray = prev[array] as string[];
      const newArray = currentArray.includes(item)
        ? currentArray.filter(i => i !== item)
        : [...currentArray, item];
      
      return {
        ...prev,
        [array]: newArray
      };
    });
  };

  const handleGrocerToggle = (grocerId: string) => {
    setEditedProfile(prev => {
      const currentGrocers = prev.preferredGrocers || [];
      const newGrocers = currentGrocers.includes(grocerId)
        ? currentGrocers.filter(id => id !== grocerId)
        : [...currentGrocers, grocerId];
      
      return {
        ...prev,
        preferredGrocers: newGrocers
      };
    });
  };

  const handleAddMember = () => {
    if (!newMember.name.trim() || !newMember.age) {
      showError('Please enter name and age for the family member');
      return;
    }

    const familyMember: FamilyMember = {
      id: Date.now().toString(),
      name: newMember.name.trim(),
      age: parseInt(newMember.age),
      dietaryRestrictions: newMember.dietaryRestrictions,
      allergies: newMember.allergies,
      lovedFoods: newMember.lovedFoods,
      dislikedFoods: newMember.dislikedFoods
    };

    const updatedProfile = {
      ...editedProfile,
      familyMembers: [...editedProfile.familyMembers, familyMember]
    };

    setEditedProfile(updatedProfile);
    storage.setProfile(updatedProfile);

    // Reset form
    setNewMember({
      name: '',
      age: '',
      dietaryRestrictions: [],
      allergies: [],
      lovedFoods: [],
      dislikedFoods: []
    });

    setShowAddMember(false);
    showSuccess(`Added ${familyMember.name} to your family!`);
  };

  const handleRemoveMember = (id: string) => {
    const memberToRemove = editedProfile.familyMembers.find(member => member.id === id);
    const updatedProfile = {
      ...editedProfile,
      familyMembers: editedProfile.familyMembers.filter(member => member.id !== id)
    };

    setEditedProfile(updatedProfile);
    storage.setProfile(updatedProfile);
    showSuccess(`Removed ${memberToRemove?.name} from your family`);
  };

  const handleDietaryRestrictionToggle = (restriction: string) => {
    setNewMember(prev => ({
      ...prev,
      dietaryRestrictions: prev.dietaryRestrictions.includes(restriction)
        ? prev.dietaryRestrictions.filter(item => item !== restriction)
        : [...prev.dietaryRestrictions, restriction]
    }));
  };

  const selectedGrocers = editedProfile.preferredGrocers || [];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-4">
            <div className="flex items-center">
              <Button variant="ghost" onClick={onBack} className="mr-4">
                <ArrowLeft className="h-4 w-4" />
              </Button>
              <div>
                <h1 className="text-xl font-semibold">Profile Settings</h1>
                <p className="text-sm text-gray-600">Manage your account and preferences</p>
              </div>
            </div>
            
            <div className="flex gap-2">
              {isEditing ? (
                <>
                  <Button variant="outline" onClick={handleCancel}>
                    Cancel
                  </Button>
                  <Button onClick={handleSave}>
                    <Save className="h-4 w-4 mr-2" />
                    Save Changes
                  </Button>
                </>
              ) : (
                <Button onClick={() => setIsEditing(true)}>
                  <Edit className="h-4 w-4 mr-2" />
                  Edit Profile
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Account Information */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <User className="h-5 w-5 mr-2" />
              Account Information
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label>Name</Label>
                <div className="mt-1 text-sm text-gray-900">{user.name}</div>
              </div>
              <div>
                <Label>Email</Label>
                <div className="mt-1 text-sm text-gray-900">{user.email}</div>
              </div>
              <div>
                <Label>Subscription</Label>
                <Badge variant={user.subscription === 'premium' ? 'default' : 'secondary'} className="mt-1">
                  {user.subscription.charAt(0).toUpperCase() + user.subscription.slice(1)}
                </Badge>
              </div>
              <div>
                <Label>Member Since</Label>
                <div className="mt-1 text-sm text-gray-900">
                  {new Date(user.createdAt).toLocaleDateString()}
                </div>
              </div>
              <div>
                <Label htmlFor="zipcode">Zip Code</Label>
                {isEditing ? (
                  <Input
                    id="zipcode"
                    value={editedProfile.zipCode}
                    onChange={(e) => setEditedProfile(prev => ({ 
                      ...prev, 
                      zipCode: e.target.value 
                    }))}
                    placeholder="Enter your zip code"
                    className="mt-1"
                  />
                ) : (
                  <div className="mt-1 text-sm text-gray-900">
                    {editedProfile.zipCode || 'Not specified'}
                  </div>
                )}
              </div>
            </div>
            
            <div className="pt-4 border-t">
              <Button variant="destructive" onClick={onLogout}>
                Sign Out
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Dietary Preferences */}
        <Card>
          <CardHeader>
            <CardTitle>Dietary Preferences</CardTitle>
            <CardDescription>
              Your dietary restrictions and food preferences
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <Label className="text-base font-medium">Dietary Restrictions</Label>
              <div className="mt-3 grid grid-cols-2 md:grid-cols-3 gap-3">
                {availableDietaryRestrictions.map(restriction => (
                  <div key={restriction} className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id={`dietary-${restriction}`}
                      checked={editedProfile.dietaryRestrictions.includes(restriction)}
                      onChange={() => handleArrayToggle('dietaryRestrictions', restriction)}
                      disabled={!isEditing}
                      className="rounded border-gray-300"
                    />
                    <Label htmlFor={`dietary-${restriction}`} className="text-sm">
                      {restriction}
                    </Label>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <Label className="text-base font-medium">Taste Preferences</Label>
              <div className="mt-3 grid grid-cols-2 md:grid-cols-3 gap-3">
                {availableTastePreferences.map(preference => (
                  <div key={preference} className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id={`taste-${preference}`}
                      checked={editedProfile.tastePreferences.includes(preference)}
                      onChange={() => handleArrayToggle('tastePreferences', preference)}
                      disabled={!isEditing}
                      className="rounded border-gray-300"
                    />
                    <Label htmlFor={`taste-${preference}`} className="text-sm">
                      {preference}
                    </Label>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <Label className="text-base font-medium">Meal Preferences</Label>
              <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-3">
                {availableMealPreferences.map(preference => (
                  <div key={preference} className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id={`meal-${preference}`}
                      checked={editedProfile.mealPreferences.includes(preference)}
                      onChange={() => handleArrayToggle('mealPreferences', preference)}
                      disabled={!isEditing}
                      className="rounded border-gray-300"
                    />
                    <Label htmlFor={`meal-${preference}`} className="text-sm">
                      {preference}
                    </Label>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Budget */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <DollarSign className="h-5 w-5 mr-2" />
              Budget
            </CardTitle>
            <CardDescription>
              Your weekly grocery budget
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="max-w-sm">
              <Label htmlFor="budget">Weekly Budget ($)</Label>
              <Input
                id="budget"
                type="number"
                min="0"
                step="10"
                value={editedProfile.weeklyBudget}
                onChange={(e) => setEditedProfile(prev => ({ 
                  ...prev, 
                  weeklyBudget: parseInt(e.target.value) || 0 
                }))}
                disabled={!isEditing}
                className="mt-1"
              />
            </div>
          </CardContent>
        </Card>

        {/* Kitchen Equipment */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <ChefHat className="h-5 w-5 mr-2" />
              Kitchen Equipment
            </CardTitle>
            <CardDescription>
              Select the kitchen appliances and tools you have available
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {availableKitchenEquipment.map(equipment => (
                <div key={equipment} className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id={`equipment-${equipment}`}
                    checked={editedProfile.kitchenEquipment.includes(equipment)}
                    onChange={() => handleArrayToggle('kitchenEquipment', equipment)}
                    disabled={!isEditing}
                    className="rounded border-gray-300"
                  />
                  <Label htmlFor={`equipment-${equipment}`} className="text-sm">
                    {equipment}
                  </Label>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Family Members */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <div className="flex items-center">
                <Users className="h-5 w-5 mr-2" />
                Family Members ({editedProfile.familyMembers.length})
              </div>
              {isEditing && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowAddMember(!showAddMember)}
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Add Member
                </Button>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Add Family Member Form */}
            {showAddMember && (
              <Card className="border-2 border-dashed border-gray-300">
                <CardContent className="p-6">
                  <h5 className="font-medium mb-4 flex items-center">
                    <Plus className="h-4 w-4 mr-2" />
                    Add Family Member
                  </h5>
                  
                  <div className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="member-name">Name *</Label>
                        <Input
                          id="member-name"
                          value={newMember.name}
                          onChange={(e) => setNewMember(prev => ({ ...prev, name: e.target.value }))}
                          placeholder="Enter name"
                        />
                      </div>
                      <div>
                        <Label htmlFor="member-age">Age *</Label>
                        <Input
                          id="member-age"
                          type="number"
                          min="0"
                          max="120"
                          value={newMember.age}
                          onChange={(e) => setNewMember(prev => ({ ...prev, age: e.target.value }))}
                          placeholder="Enter age"
                        />
                      </div>
                    </div>

                    <div>
                      <Label className="text-base font-medium mb-3 block">Dietary Restrictions</Label>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                        {availableDietaryRestrictions.map(restriction => (
                          <div key={restriction} className="flex items-center space-x-2">
                            <input
                              type="checkbox"
                              id={`new-dietary-${restriction}`}
                              checked={newMember.dietaryRestrictions.includes(restriction)}
                              onChange={() => handleDietaryRestrictionToggle(restriction)}
                              className="rounded border-gray-300"
                            />
                            <Label htmlFor={`new-dietary-${restriction}`} className="text-sm">
                              {restriction}
                            </Label>
                          </div>
                        ))}
                      </div>
                    </div>
                    
                    <div>
                      <Label className="text-base font-medium mb-3 block">Allergies</Label>
                      <AutocompleteField
                        label="Allergies"
                        placeholder="Search for allergies or add custom ones..."
                        options={COMMON_ALLERGIES}
                        selectedItems={newMember.allergies}
                        onSelectionChange={(items) => setNewMember(prev => ({ ...prev, allergies: items }))}
                      />
                    </div>
                    
                    <div>
                      <Label className="text-base font-medium mb-3 block">Foods/Meals They Love</Label>
                      <AutocompleteField
                        label="Loved Foods"
                        placeholder="Search for favorite foods or add custom ones..."
                        options={COMMON_LOVED_FOODS}
                        selectedItems={newMember.lovedFoods}
                        onSelectionChange={(items) => setNewMember(prev => ({ ...prev, lovedFoods: items }))}
                      />
                    </div>
                    
                    <div>
                      <Label className="text-base font-medium mb-3 block">Foods/Meals They Don't Like</Label>
                      <AutocompleteField
                        label="Disliked Foods"
                        placeholder="Search for disliked foods or add custom ones..."
                        options={COMMON_DISLIKED_FOODS}
                        selectedItems={newMember.dislikedFoods}
                        onSelectionChange={(items) => setNewMember(prev => ({ ...prev, dislikedFoods: items }))}
                      />
                    </div>
                    
                    <div className="flex gap-3 pt-4">
                      <Button onClick={handleAddMember} className="flex-1">
                        <Save className="h-4 w-4 mr-2" />
                        Add Family Member
                      </Button>
                      <Button 
                        variant="outline" 
                        onClick={() => {
                          setShowAddMember(false);
                          setNewMember({
                            name: '',
                            age: '',
                            dietaryRestrictions: [],
                            allergies: [],
                            lovedFoods: [],
                            dislikedFoods: []
                          });
                        }}
                        className="flex-1"
                      >
                        Cancel
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Existing Family Members */}
            {editedProfile.familyMembers.length > 0 ? (
              <div className="space-y-3">
                {editedProfile.familyMembers.map(member => (
                  <Card key={member.id} className="border-l-4 border-l-blue-500">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center">
                          <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 font-medium mr-3">
                            {member.name.charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <span className="font-medium">{member.name}</span>
                            <span className="text-gray-600 ml-2">({member.age} years old)</span>
                          </div>
                        </div>
                        {isEditing && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleRemoveMember(member.id)}
                            className="text-red-600 hover:text-red-700 hover:bg-red-50"
                          >
                            <Trash2 className="h-4 w-4 mr-1" />
                            Remove
                          </Button>
                        )}
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                        {member.allergies.length > 0 && (
                          <div>
                            <div className="flex items-center text-red-600 font-medium mb-2">
                              <AlertTriangle className="h-4 w-4 mr-1" />
                              Allergies
                            </div>
                            <div className="flex flex-wrap gap-1">
                              {member.allergies.map(allergy => (
                                <Badge key={allergy} variant="destructive" className="text-xs">
                                  {allergy}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}
                        
                        {member.lovedFoods.length > 0 && (
                          <div>
                            <div className="flex items-center text-green-600 font-medium mb-2">
                              <Heart className="h-4 w-4 mr-1" />
                              Loves
                            </div>
                            <div className="flex flex-wrap gap-1">
                              {member.lovedFoods.map(food => (
                                <Badge key={food} variant="secondary" className="text-xs bg-green-100 text-green-700">
                                  {food}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}
                        
                        {member.dislikedFoods.length > 0 && (
                          <div>
                            <div className="flex items-center text-orange-600 font-medium mb-2">
                              <ThumbsDown className="h-4 w-4 mr-1" />
                              Dislikes
                            </div>
                            <div className="flex flex-wrap gap-1">
                              {member.dislikedFoods.map(food => (
                                <Badge key={food} variant="outline" className="text-xs border-orange-200 text-orange-700">
                                  {food}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}

                        {member.dietaryRestrictions.length > 0 && (
                          <div>
                            <div className="font-medium mb-2">Dietary Restrictions</div>
                            <div className="flex flex-wrap gap-1">
                              {member.dietaryRestrictions.map(restriction => (
                                <Badge key={restriction} variant="outline" className="text-xs">
                                  {restriction}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>

                      {member.allergies.length === 0 && member.lovedFoods.length === 0 && 
                       member.dislikedFoods.length === 0 && member.dietaryRestrictions.length === 0 && (
                        <div className="text-center py-2 text-gray-500 text-sm">
                          No preferences or restrictions specified
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <Users className="h-8 w-8 mx-auto mb-2 text-gray-300" />
                <p>No family members added yet</p>
                {isEditing && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowAddMember(true)}
                    className="mt-2"
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Add Your First Family Member
                  </Button>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* My Grocers */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Store className="h-5 w-5 mr-2" />
              My Grocers
            </CardTitle>
            <CardDescription>
              Select your preferred grocery stores and delivery services
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Local Grocers */}
            {localGrocers.length > 0 && (
              <div>
                <div className="flex items-center mb-4">
                  <MapPin className="h-4 w-4 mr-2 text-blue-600" />
                  <Label className="text-base font-medium">Local Stores Near You</Label>
                  {editedProfile.zipCode && (
                    <Badge variant="outline" className="ml-2 text-xs">
                      {editedProfile.zipCode}
                    </Badge>
                  )}
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {localGrocers.map(grocer => (
                    <div key={grocer.id} className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50">
                      <div className="flex items-center space-x-3">
                        <input
                          type="checkbox"
                          id={`grocer-${grocer.id}`}
                          checked={selectedGrocers.includes(grocer.id)}
                          onChange={() => handleGrocerToggle(grocer.id)}
                          disabled={!isEditing}
                          className="rounded border-gray-300"
                        />
                        <div>
                          <Label htmlFor={`grocer-${grocer.id}`} className="text-sm font-medium cursor-pointer">
                            {grocer.name}
                          </Label>
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
                  ))}
                </div>
              </div>
            )}

            {/* No zip code message */}
            {!editedProfile.zipCode && (
              <div className="text-center py-6 bg-blue-50 rounded-lg border-2 border-dashed border-blue-200">
                <MapPin className="h-8 w-8 text-blue-400 mx-auto mb-2" />
                <p className="text-sm text-blue-600 font-medium">Add your zip code to see local stores</p>
                <p className="text-xs text-blue-500 mt-1">Update your zip code in Account Information above</p>
              </div>
            )}

            {/* Delivery Services */}
            <div>
              <div className="flex items-center mb-4">
                <Truck className="h-4 w-4 mr-2 text-green-600" />
                <Label className="text-base font-medium">Delivery Services</Label>
                <Badge variant="outline" className="ml-2 text-xs">
                  Available Nationwide
                </Badge>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {DELIVERY_GROCERS.map(grocer => (
                  <div key={grocer.id} className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50">
                    <div className="flex items-center space-x-3">
                      <input
                        type="checkbox"
                        id={`grocer-${grocer.id}`}
                        checked={selectedGrocers.includes(grocer.id)}
                        onChange={() => handleGrocerToggle(grocer.id)}
                        disabled={!isEditing}
                        className="rounded border-gray-300"
                      />
                      <div>
                        <Label htmlFor={`grocer-${grocer.id}`} className="text-sm font-medium cursor-pointer">
                          {grocer.name}
                        </Label>
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
                ))}
              </div>
            </div>

            {/* Selected grocers summary */}
            {selectedGrocers.length > 0 && (
              <div className="pt-4 border-t">
                <Label className="text-sm font-medium text-gray-700">
                  Selected: {selectedGrocers.length} grocer{selectedGrocers.length !== 1 ? 's' : ''}
                </Label>
                <div className="flex flex-wrap gap-2 mt-2">
                  {selectedGrocers.map(grocerId => {
                    const grocer = [...localGrocers, ...DELIVERY_GROCERS].find(g => g.id === grocerId);
                    return grocer ? (
                      <Badge key={grocerId} variant="default" className="text-xs">
                        {grocer.name}
                      </Badge>
                    ) : null;
                  })}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};