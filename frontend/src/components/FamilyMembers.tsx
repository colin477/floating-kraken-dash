import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { ArrowLeft, Plus, Edit, Trash2, Users, Heart, ThumbsDown, AlertTriangle, Save, X } from 'lucide-react';
import { User, UserProfile, FamilyMember } from '@/types';
import { storage } from '@/lib/storage';
import { showSuccess, showError } from '@/utils/toast';
import { AutocompleteField } from '@/components/AutocompleteField';

interface FamilyMembersProps {
  user: User;
  profile: UserProfile;
  onBack: () => void;
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

export const FamilyMembers = ({ user, profile, onBack }: FamilyMembersProps) => {
  const [familyMembers, setFamilyMembers] = useState<FamilyMember[]>([]);
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingMember, setEditingMember] = useState<FamilyMember | null>(null);
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

  useEffect(() => {
    setFamilyMembers(profile.familyMembers);
  }, [profile.familyMembers]);

  const handleAddMember = async () => {
    console.log('🔍 [DEBUG] handleAddMember called');
    console.log('🔍 [DEBUG] Current newMember state:', newMember);
    console.log('🔍 [DEBUG] Current showAddForm state:', showAddForm);
    console.log('🔍 [DEBUG] Current editingMember state:', editingMember);

    if (!newMember.name.trim() || !newMember.age) {
      console.log('❌ [DEBUG] Validation failed - missing name or age');
      showError('Please enter name and age for the family member');
      return;
    }

    try {
      // Convert camelCase to snake_case for API
      const memberData = {
        name: newMember.name.trim(),
        age: parseInt(newMember.age),
        dietary_restrictions: newMember.dietaryRestrictions,
        allergies: newMember.allergies,
        loved_foods: newMember.lovedFoods,
        disliked_foods: newMember.dislikedFoods
      };

      console.log('🔍 [DEBUG] Prepared memberData for API:', memberData);

      // Call API to add family member
      console.log('🔍 [DEBUG] Calling profileApi.addFamilyMember...');
      const { profileApi } = await import('@/services/api');
      const updatedProfile = await profileApi.addFamilyMember(memberData);
      
      console.log('✅ [DEBUG] API call successful, received updatedProfile:', updatedProfile);
      console.log('🔍 [DEBUG] Updated family members:', updatedProfile.familyMembers);
      
      // Update local state with API response
      console.log('🔍 [DEBUG] Updating local state...');
      setFamilyMembers(updatedProfile.familyMembers);
      storage.setProfile(updatedProfile);

      // Reset form
      console.log('🔍 [DEBUG] Resetting form state...');
      setNewMember({
        name: '',
        age: '',
        dietaryRestrictions: [],
        allergies: [],
        lovedFoods: [],
        dislikedFoods: []
      });

      console.log('🔍 [DEBUG] Setting showAddForm to false...');
      setShowAddForm(false);
      console.log('🔍 [DEBUG] Setting editingMember to null...');
      setEditingMember(null);
      
      console.log('✅ [DEBUG] handleAddMember completed successfully');
      showSuccess(`Added ${memberData.name} to your family!`);
    } catch (error) {
      console.error('❌ [DEBUG] Error in handleAddMember:', error);
      console.error('❌ [DEBUG] Error details:', {
        message: error.message,
        stack: error.stack,
        name: error.name
      });
      showError(`Failed to add family member: ${error.message}`);
    }
  };

  const handleEditMember = (member: FamilyMember) => {
    console.log('🔍 [DEBUG] handleEditMember called with member:', member);
    
    setEditingMember(member);
    const editFormData = {
      name: member.name,
      age: member.age.toString(),
      dietaryRestrictions: [...member.dietaryRestrictions],
      allergies: [...member.allergies],
      lovedFoods: [...member.lovedFoods],
      dislikedFoods: [...member.dislikedFoods]
    };
    
    console.log('🔍 [DEBUG] Setting form data for editing:', editFormData);
    setNewMember(editFormData);
    
    console.log('🔍 [DEBUG] Setting showAddForm to true for editing');
    setShowAddForm(true);
  };

  const handleSaveEdit = async () => {
    console.log('🔍 [DEBUG] handleSaveEdit called');
    console.log('🔍 [DEBUG] Current newMember state:', newMember);
    console.log('🔍 [DEBUG] Current editingMember state:', editingMember);
    console.log('🔍 [DEBUG] Current showAddForm state:', showAddForm);

    if (!newMember.name.trim() || !newMember.age) {
      console.log('❌ [DEBUG] Validation failed - missing name or age');
      showError('Please enter name and age for the family member');
      return;
    }

    if (!editingMember) {
      console.log('❌ [DEBUG] No editingMember found, returning');
      return;
    }

    try {
      // Convert camelCase to snake_case for API
      const memberData = {
        name: newMember.name.trim(),
        age: parseInt(newMember.age),
        dietary_restrictions: newMember.dietaryRestrictions,
        allergies: newMember.allergies,
        loved_foods: newMember.lovedFoods,
        disliked_foods: newMember.dislikedFoods
      };

      console.log('🔍 [DEBUG] Prepared memberData for API:', memberData);
      console.log('🔍 [DEBUG] Updating member with ID:', editingMember.id);

      // Call API to update family member
      console.log('🔍 [DEBUG] Calling profileApi.updateFamilyMember...');
      const { profileApi } = await import('@/services/api');
      const updatedProfile = await profileApi.updateFamilyMember(editingMember.id, memberData);
      
      console.log('✅ [DEBUG] API call successful, received updatedProfile:', updatedProfile);
      console.log('🔍 [DEBUG] Updated family members:', updatedProfile.familyMembers);
      
      // Update local state with API response
      console.log('🔍 [DEBUG] Updating local state...');
      setFamilyMembers(updatedProfile.familyMembers);
      storage.setProfile(updatedProfile);

      // Reset form
      console.log('🔍 [DEBUG] Resetting form state...');
      setNewMember({
        name: '',
        age: '',
        dietaryRestrictions: [],
        allergies: [],
        lovedFoods: [],
        dislikedFoods: []
      });

      console.log('🔍 [DEBUG] Setting editingMember to null...');
      setEditingMember(null);
      console.log('🔍 [DEBUG] Setting showAddForm to false...');
      setShowAddForm(false);
      
      console.log('✅ [DEBUG] handleSaveEdit completed successfully');
      showSuccess(`Updated ${memberData.name}'s information!`);
    } catch (error) {
      console.error('❌ [DEBUG] Error in handleSaveEdit:', error);
      console.error('❌ [DEBUG] Error details:', {
        message: error.message,
        stack: error.stack,
        name: error.name
      });
      showError(`Failed to update family member: ${error.message}`);
    }
  };

  const handleRemoveMember = async (id: string) => {
    const memberToRemove = familyMembers.find(member => member.id === id);
    
    try {
      // Call API to remove family member
      const { profileApi } = await import('@/services/api');
      const updatedProfile = await profileApi.removeFamilyMember(id);
      
      // Update local state with API response
      setFamilyMembers(updatedProfile.familyMembers);
      storage.setProfile(updatedProfile);
      showSuccess(`Removed ${memberToRemove?.name} from your family`);
    } catch (error) {
      console.error('Error removing family member:', error);
      showError(`Failed to remove family member: ${error.message}`);
    }
  };

  const handleDietaryRestrictionToggle = (restriction: string) => {
    setNewMember(prev => ({
      ...prev,
      dietaryRestrictions: prev.dietaryRestrictions.includes(restriction)
        ? prev.dietaryRestrictions.filter(item => item !== restriction)
        : [...prev.dietaryRestrictions, restriction]
    }));
  };

  const handleCancelForm = () => {
    console.log('🔍 [DEBUG] handleCancelForm called');
    console.log('🔍 [DEBUG] Current states before cancel:', {
      showAddForm,
      editingMember,
      newMember
    });
    
    setNewMember({
      name: '',
      age: '',
      dietaryRestrictions: [],
      allergies: [],
      lovedFoods: [],
      dislikedFoods: []
    });
    setEditingMember(null);
    setShowAddForm(false);
    
    console.log('🔍 [DEBUG] Form cancelled and states reset');
  };

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
                <h1 className="text-xl font-semibold">Family Members</h1>
                <p className="text-sm text-gray-600">Manage your family's dietary preferences and restrictions</p>
              </div>
            </div>
            
            <Dialog open={showAddForm} onOpenChange={(open) => {
              console.log('🔍 [DEBUG] Dialog onOpenChange called with:', open);
              if (!open) {
                // Dialog is being closed
                console.log('🔍 [DEBUG] Dialog closing, resetting form state');
                handleCancelForm();
              } else {
                setShowAddForm(open);
              }
            }}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  Add Family Member
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-3xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle>
                    {editingMember ? 'Edit Family Member' : 'Add Family Member'}
                  </DialogTitle>
                  <DialogDescription>
                    {editingMember 
                      ? 'Update family member information and preferences'
                      : 'Add a new family member with their dietary preferences and restrictions'
                    }
                  </DialogDescription>
                </DialogHeader>
                
                <div className="space-y-6 py-4">
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
                            id={`dietary-${restriction}`}
                            checked={newMember.dietaryRestrictions.includes(restriction)}
                            onChange={() => handleDietaryRestrictionToggle(restriction)}
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
                </div>
                
                <div className="flex gap-3">
                  <Button 
                    onClick={editingMember ? handleSaveEdit : handleAddMember} 
                    className="flex-1"
                  >
                    <Save className="h-4 w-4 mr-2" />
                    {editingMember ? 'Save Changes' : 'Add Family Member'}
                  </Button>
                  <Button variant="outline" onClick={handleCancelForm} className="flex-1">
                    <X className="h-4 w-4 mr-2" />
                    Cancel
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Family Overview */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Users className="h-5 w-5 mr-2" />
              Family Overview
            </CardTitle>
            <CardDescription>
              Total family size: {familyMembers.length + 1} people (including you)
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">{familyMembers.length + 1}</div>
                <div className="text-sm text-blue-600">Total Members</div>
              </div>
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <div className="text-2xl font-bold text-green-600">
                  {familyMembers.filter(member => member.allergies.length > 0).length}
                </div>
                <div className="text-sm text-green-600">With Allergies</div>
              </div>
              <div className="text-center p-4 bg-purple-50 rounded-lg">
                <div className="text-2xl font-bold text-purple-600">
                  {familyMembers.filter(member => member.dietaryRestrictions.length > 0).length}
                </div>
                <div className="text-sm text-purple-600">With Dietary Restrictions</div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* You (Primary User) */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="w-10 h-10 bg-primary rounded-full flex items-center justify-center text-white font-medium mr-3">
                  {user.name.charAt(0).toUpperCase()}
                </div>
                <div>
                  <span className="text-lg">{user.name}</span>
                  <Badge variant="default" className="ml-2">You</Badge>
                </div>
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div>
                <div className="font-medium mb-2">Dietary Restrictions</div>
                <div className="flex flex-wrap gap-1">
                  {profile.dietaryRestrictions.length > 0 ? (
                    profile.dietaryRestrictions.map(restriction => (
                      <Badge key={restriction} variant="outline" className="text-xs">
                        {restriction}
                      </Badge>
                    ))
                  ) : (
                    <span className="text-gray-500">None</span>
                  )}
                </div>
              </div>
              
              <div>
                <div className="font-medium mb-2">Taste Preferences</div>
                <div className="flex flex-wrap gap-1">
                  {profile.tastePreferences.length > 0 ? (
                    profile.tastePreferences.slice(0, 3).map(preference => (
                      <Badge key={preference} variant="secondary" className="text-xs">
                        {preference}
                      </Badge>
                    ))
                  ) : (
                    <span className="text-gray-500">None</span>
                  )}
                  {profile.tastePreferences.length > 3 && (
                    <Badge variant="secondary" className="text-xs">
                      +{profile.tastePreferences.length - 3} more
                    </Badge>
                  )}
                </div>
              </div>
              
              <div>
                <div className="font-medium mb-2">Weekly Budget</div>
                <div className="text-green-600 font-semibold">${profile.weeklyBudget}</div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Family Members */}
        {familyMembers.length > 0 ? (
          <div className="space-y-6">
            <h2 className="text-lg font-semibold text-gray-900">Family Members</h2>
            {familyMembers.map(member => (
              <Card key={member.id}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className="w-10 h-10 bg-secondary rounded-full flex items-center justify-center text-secondary-foreground font-medium mr-3">
                        {member.name.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <span className="text-lg font-medium">{member.name}</span>
                        <span className="text-gray-600 ml-2">({member.age} years old)</span>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleEditMember(member)}
                      >
                        <Edit className="h-4 w-4 mr-1" />
                        Edit
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleRemoveMember(member.id)}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      >
                        <Trash2 className="h-4 w-4 mr-1" />
                        Remove
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-sm">
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
                    <div className="text-center py-4 text-gray-500">
                      No preferences or restrictions specified
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <Users className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No family members added yet</h3>
            <p className="text-gray-600 mb-4">
              Add family members to personalize meal planning for everyone's preferences and dietary needs.
            </p>
            <Button onClick={() => setShowAddForm(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Add Your First Family Member
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};