import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import { User, UserProfile } from '@/types';
import { storage } from '@/lib/storage';
import { showSuccess, showError } from '@/utils/toast';
import { useAuth } from '@/hooks/useAuth';
import { useGoogleLogin } from '@react-oauth/google';

interface AuthFormProps {
  onAuthSuccess: (user: User, isNewUser: boolean) => void;
}

export const AuthForm = ({ onAuthSuccess }: AuthFormProps) => {
  const { login, register } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  // Test comment for Fast Refresh verification - HMR Test Update
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: '',
    confirmPassword: ''
  });

  // Check URL parameters to determine default tab
  const urlParams = new URLSearchParams(window.location.search);
  const defaultTab = urlParams.get('tab') === 'signup' ? 'signup' : 'login';

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  const createDefaultProfile = (userId: string): UserProfile => {
    return {
      userId,
      dietaryRestrictions: [],
      allergies: [],
      tastePreferences: [],
      mealPreferences: [],
      kitchenEquipment: [],
      weeklyBudget: 100,
      familyMembers: []
    };
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setSuccess(null);

    try {
      console.log('[AuthForm] Starting login process...');
      await login(formData.email, formData.password);
      
      console.log('[AuthForm] Login successful, setting up profile...');
      // Create default profile if needed
      let existingProfile = storage.getProfile();
      if (!existingProfile) {
        const storedUser = storage.getUser();
        if (storedUser) {
          existingProfile = createDefaultProfile(storedUser.id);
          storage.setProfile(existingProfile);
        }
      }
      
      setSuccess('Welcome back to EZ Eatin\'!');
      const user = storage.getUser();
      if (user) {
        onAuthSuccess(user, false); // false = existing user
      }
    } catch (error) {
      console.error('[AuthForm] 🚨 LOGIN ERROR CAUGHT:');
      console.error('[AuthForm] Error type:', error?.constructor?.name);
      console.error('[AuthForm] Error message:', error?.message);
      console.error('[AuthForm] Full error object:', error);
      
      const errorMessage = error instanceof Error ? error.message : 'Login failed';
      console.error('[AuthForm] Displaying error message to user:', errorMessage);
      
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setIsLoading(true);

    try {
      console.log('[AuthForm] Starting registration process...');
      const newUser = await register(formData.email, formData.password, formData.name);
      
      console.log('[AuthForm] Registration successful, showing success message');
      setSuccess('Welcome to EZ Eatin\'! Choose your plan to get started.');
      
      if (newUser) {
        onAuthSuccess(newUser, true); // true = new user (show plan selection)
      }
    } catch (error) {
      console.error('[AuthForm] 🚨 REGISTRATION ERROR CAUGHT:');
      console.error('[AuthForm] Error type:', error?.constructor?.name);
      console.error('[AuthForm] Error message:', (error as Error)?.message);
      console.error('[AuthForm] Full error object:', error);
      
      const errorMessage = error instanceof Error ? error.message : 'Registration failed. Please try again.';
      console.error('[AuthForm] Displaying error message to user:', errorMessage);
      
      setError(errorMessage);
      setSuccess(null);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleSignIn = useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      setIsGoogleLoading(true);
      setError(null);
      
      try {
        // Get user info from Google using the access token
        const userInfoResponse = await fetch('https://www.googleapis.com/oauth2/v2/userinfo', {
          headers: {
            Authorization: `Bearer ${tokenResponse.access_token}`,
          },
        });
        
        if (!userInfoResponse.ok) {
          throw new Error('Failed to get user information from Google');
        }
        
        const googleUserInfo = await userInfoResponse.json();
        
        // Get Google ID token for backend verification
        const tokenInfoResponse = await fetch(`https://oauth2.googleapis.com/tokeninfo?access_token=${tokenResponse.access_token}`);
        
        if (!tokenInfoResponse.ok) {
          throw new Error('Failed to verify Google token');
        }
        
        // For production, you would get the ID token from the Google OAuth flow
        // For now, we'll use the access token to get user info and create a mock ID token
        // In a real implementation, you'd get the ID token directly from Google
        
        // Send to backend for verification and user creation/login
        const backendResponse = await fetch('/api/v1/auth/google/verify', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            // In production, this would be the actual ID token from Google
            // For now, we'll simulate with user info
            id_token: tokenResponse.access_token, // This should be the ID token in production
          }),
        });
        
        if (!backendResponse.ok) {
          const errorData = await backendResponse.json();
          throw new Error(errorData.detail || 'Google OAuth verification failed');
        }
        
        const authData = await backendResponse.json();
        
        // Create user object from backend response
        const user: User = {
          id: authData.user.id,
          email: authData.user.email,
          name: authData.user.full_name,
          createdAt: authData.user.created_at,
          subscription: 'free',
          monthlyUsage: {
            receiptScans: 0,
            mealPlans: 0,
            communityPosts: 0
          }
        };
        
        // Store user and token
        storage.setUser(user);
        storage.setToken(authData.access_token);
        
        // Create default profile if needed
        let existingProfile = storage.getProfile();
        if (!existingProfile) {
          existingProfile = createDefaultProfile(user.id);
          storage.setProfile(existingProfile);
        }
        
        // Determine if this is a new user (you could get this from backend response)
        const isNewUser = new Date(user.createdAt).getTime() > (Date.now() - 60000); // Created within last minute
        
        setSuccess(isNewUser ? 'Welcome to EZ Eatin\'! Choose your plan to get started.' : 'Welcome back to EZ Eatin\'!');
        onAuthSuccess(user, isNewUser);
        
      } catch (error) {
        console.error('Google OAuth error:', error);
        const errorMessage = error instanceof Error ? error.message : 'Google sign-in failed. Please try again.';
        setError(errorMessage);
        showError(errorMessage);
      } finally {
        setIsGoogleLoading(false);
      }
    },
    onError: (error) => {
      console.error('Google OAuth error:', error);
      setError('Google sign-in failed. Please try again.');
      showError('Google sign-in failed. Please try again.');
      setIsGoogleLoading(false);
    },
  });

  const GoogleIcon = () => (
    <svg className="w-5 h-5" viewBox="0 0 24 24">
      <path
        fill="#4285F4"
        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
      />
      <path
        fill="#34A853"
        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
      />
      <path
        fill="#FBBC05"
        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
      />
      <path
        fill="#EA4335"
        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
      />
    </svg>
  );

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-50 to-blue-50 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl font-bold text-green-600">EZ Eatin'</CardTitle>
          <CardDescription>
            AI-powered meal planning for busy families
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* Error/Success Messages */}
          {error && (
            <div className="mb-4 p-3 rounded-md bg-red-50 border border-red-200">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-red-800">{error}</p>
                </div>
              </div>
            </div>
          )}
          
          {success && (
            <div className="mb-4 p-3 rounded-md bg-green-50 border border-green-200">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-green-800">{success}</p>
                </div>
              </div>
            </div>
          )}

          <Tabs defaultValue={defaultTab} className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="login">Login</TabsTrigger>
              <TabsTrigger value="signup">Sign Up</TabsTrigger>
            </TabsList>
            
            <TabsContent value="login">
              <div className="space-y-4">
                {/* Google Sign In Button */}
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={handleGoogleSignIn}
                  disabled={isGoogleLoading}
                >
                  {isGoogleLoading ? (
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-gray-600 mr-2"></div>
                  ) : (
                    <GoogleIcon />
                  )}
                  <span className="ml-2">
                    {isGoogleLoading ? 'Signing in...' : 'Continue with Google'}
                  </span>
                </Button>

                <div className="relative">
                  <div className="absolute inset-0 flex items-center">
                    <Separator className="w-full" />
                  </div>
                  <div className="relative flex justify-center text-xs uppercase">
                    <span className="bg-white px-2 text-gray-500">Or continue with email</span>
                  </div>
                </div>

                <form onSubmit={handleLogin} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="email">Email</Label>
                    <Input
                      id="email"
                      name="email"
                      type="email"
                      placeholder="your@email.com"
                      value={formData.email}
                      onChange={handleInputChange}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="password">Password</Label>
                    <Input
                      id="password"
                      name="password"
                      type="password"
                      placeholder="••••••••"
                      value={formData.password}
                      onChange={handleInputChange}
                      required
                    />
                  </div>
                  <Button type="submit" className="w-full" disabled={isLoading}>
                    {isLoading ? 'Signing in...' : 'Sign In'}
                  </Button>
                </form>
                
                <div className="text-center text-sm text-gray-500">
                  <p>Existing users go directly to dashboard</p>
                </div>
              </div>
            </TabsContent>
            
            <TabsContent value="signup">
              <div className="space-y-4">
                {/* Google Sign Up Button */}
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={handleGoogleSignIn}
                  disabled={isGoogleLoading}
                >
                  {isGoogleLoading ? (
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-gray-600 mr-2"></div>
                  ) : (
                    <GoogleIcon />
                  )}
                  <span className="ml-2">
                    {isGoogleLoading ? 'Creating account...' : 'Sign up with Google'}
                  </span>
                </Button>

                <div className="relative">
                  <div className="absolute inset-0 flex items-center">
                    <Separator className="w-full" />
                  </div>
                  <div className="relative flex justify-center text-xs uppercase">
                    <span className="bg-white px-2 text-gray-500">Or create account with email</span>
                  </div>
                </div>

                <form onSubmit={handleSignup} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="name">Full Name</Label>
                    <Input
                      id="name"
                      name="name"
                      type="text"
                      placeholder="Your Name"
                      value={formData.name}
                      onChange={handleInputChange}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="signup-email">Email</Label>
                    <Input
                      id="signup-email"
                      name="email"
                      type="email"
                      placeholder="your@email.com"
                      value={formData.email}
                      onChange={handleInputChange}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="signup-password">Password</Label>
                    <Input
                      id="signup-password"
                      name="password"
                      type="password"
                      placeholder="••••••••"
                      value={formData.password}
                      onChange={handleInputChange}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="confirmPassword">Confirm Password</Label>
                    <Input
                      id="confirmPassword"
                      name="confirmPassword"
                      type="password"
                      placeholder="••••••••"
                      value={formData.confirmPassword}
                      onChange={handleInputChange}
                      required
                    />
                  </div>
                  <Button type="submit" className="w-full" disabled={isLoading}>
                    {isLoading ? 'Creating account...' : 'Start Free'}
                  </Button>
                  <p className="text-xs text-gray-500 text-center">
                    New users will choose a plan after signup
                  </p>
                </form>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
};