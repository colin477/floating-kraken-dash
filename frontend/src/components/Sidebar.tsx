import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { 
  Home, 
  Package, 
  ChefHat, 
  Calendar, 
  ShoppingCart, 
  RefreshCw, 
  Users, 
  User, 
  Camera, 
  Link, 
  Edit,
  ChevronDown,
  ChevronRight,
  X,
  Menu
} from 'lucide-react';
import { cn } from '@/lib/utils';

// TypeScript interfaces
interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  currentPage: string;
  onNavigate: (page: string) => void;
  user?: {
    name: string;
    email: string;
    subscription: 'free' | 'basic' | 'premium';
  };
}

interface NavigationItem {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  page: string;
  badge?: string;
}

interface QuickAction {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  page: string;
  description: string;
}

export const Sidebar = ({ isOpen, onToggle, currentPage, onNavigate, user }: SidebarProps) => {
  const [quickActionsExpanded, setQuickActionsExpanded] = useState(true);
  const [isMobile, setIsMobile] = useState(false);

  // Check screen size and update mobile state
  useEffect(() => {
    const checkScreenSize = () => {
      setIsMobile(window.innerWidth <= 767);
    };

    checkScreenSize();
    window.addEventListener('resize', checkScreenSize);
    return () => window.removeEventListener('resize', checkScreenSize);
  }, []);

  // Load sidebar state from localStorage
  useEffect(() => {
    const savedQuickActionsState = localStorage.getItem('sidebar-quick-actions-expanded');
    if (savedQuickActionsState !== null) {
      setQuickActionsExpanded(JSON.parse(savedQuickActionsState));
    }
  }, []);

  // Save quick actions state to localStorage
  const toggleQuickActions = () => {
    const newState = !quickActionsExpanded;
    setQuickActionsExpanded(newState);
    localStorage.setItem('sidebar-quick-actions-expanded', JSON.stringify(newState));
  };

  // Primary navigation items
  const primaryNavItems: NavigationItem[] = [
    { id: 'dashboard', label: 'Dashboard', icon: Home, page: 'dashboard' },
    { id: 'pantry', label: 'Pantry', icon: Package, page: 'pantry' },
    { id: 'recipes', label: 'Recipes', icon: ChefHat, page: 'recipes' },
    { id: 'meal-planner', label: 'Meal Planner', icon: Calendar, page: 'meal-planner' },
    { id: 'shopping-lists', label: 'Shopping Lists', icon: ShoppingCart, page: 'shopping-lists' },
    { id: 'leftovers', label: 'Leftovers', icon: RefreshCw, page: 'leftovers' },
  ];

  // Secondary navigation items
  const secondaryNavItems: NavigationItem[] = [
    { id: 'community', label: 'Community', icon: Users, page: 'community' },
    { id: 'family-members', label: 'Family', icon: Users, page: 'family-members' },
    { id: 'profile', label: 'Profile', icon: User, page: 'profile' },
  ];

  // Quick actions
  const quickActions: QuickAction[] = [
    { id: 'receipt-scan', label: 'Scan Receipt', icon: Camera, page: 'receipt-scan', description: 'Add groceries to pantry' },
    { id: 'meal-photo', label: 'Photo Analysis', icon: Camera, page: 'meal-photo', description: 'Get recipes from meals' },
    { id: 'add-from-link', label: 'Add from Link', icon: Link, page: 'add-from-link', description: 'Import recipe from URL' },
    { id: 'create-recipe', label: 'Create Recipe', icon: Edit, page: 'create-recipe', description: 'Write your own recipe' },
  ];

  const handleNavigation = (page: string) => {
    onNavigate(page);
    // Close sidebar on mobile after navigation
    if (isMobile && isOpen) {
      onToggle();
    }
  };

  const handleKeyDown = (event: React.KeyboardEvent, action: () => void) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      action();
    }
  };

  // Backdrop for mobile/tablet overlay
  const backdrop = (isMobile || (window.innerWidth >= 768 && window.innerWidth <= 1023)) && isOpen && (
    <div 
      className="fixed inset-0 bg-black/50 z-40 lg:hidden"
      onClick={onToggle}
      aria-hidden="true"
    />
  );

  return (
    <>
      {backdrop}
      
      {/* Sidebar */}
      <aside
        className={cn(
          "fixed top-0 left-0 z-50 h-full bg-sidebar border-r border-sidebar-border transition-transform duration-300 ease-in-out",
          // Desktop: always visible, fixed width
          "lg:translate-x-0 lg:w-[280px] lg:relative lg:z-auto",
          // Tablet: overlay with backdrop
          "md:w-[280px]",
          // Mobile: full width overlay
          "w-full sm:w-[280px]",
          // Transform based on isOpen state for mobile/tablet
          isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        )}
        role="navigation"
        aria-label="Main navigation"
      >
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-sidebar-border">
            <div className="flex items-center space-x-2">
              <ChefHat className="h-8 w-8 text-sidebar-primary" />
              <h1 className="text-xl font-bold text-sidebar-foreground">EZ Eatin'</h1>
            </div>
            {/* Close button for mobile/tablet */}
            <Button
              variant="ghost"
              size="sm"
              onClick={onToggle}
              className="lg:hidden"
              aria-label="Close sidebar"
            >
              <X className="h-5 w-5" />
            </Button>
          </div>

          {/* Navigation Content */}
          <div className="flex-1 overflow-y-auto">
            <div className="p-4 space-y-6">
              {/* Primary Navigation */}
              <nav role="navigation" aria-label="Primary navigation">
                <div className="space-y-1">
                  {primaryNavItems.map((item) => {
                    const Icon = item.icon;
                    const isActive = currentPage === item.page;
                    
                    return (
                      <Button
                        key={item.id}
                        variant={isActive ? "default" : "ghost"}
                        className={cn(
                          "w-full justify-start h-11 px-3",
                          isActive 
                            ? "bg-sidebar-primary text-sidebar-primary-foreground hover:bg-sidebar-primary/90" 
                            : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                        )}
                        onClick={() => handleNavigation(item.page)}
                        onKeyDown={(e) => handleKeyDown(e, () => handleNavigation(item.page))}
                        aria-current={isActive ? "page" : undefined}
                      >
                        <Icon className="h-5 w-5 mr-3" />
                        {item.label}
                        {item.badge && (
                          <span className="ml-auto bg-sidebar-primary text-sidebar-primary-foreground text-xs px-2 py-1 rounded-full">
                            {item.badge}
                          </span>
                        )}
                      </Button>
                    );
                  })}
                </div>
              </nav>

              <Separator className="bg-sidebar-border" />

              {/* Quick Actions */}
              <div>
                <Button
                  variant="ghost"
                  className="w-full justify-between h-9 px-3 text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                  onClick={toggleQuickActions}
                  onKeyDown={(e) => handleKeyDown(e, toggleQuickActions)}
                  aria-expanded={quickActionsExpanded}
                  aria-controls="quick-actions-content"
                >
                  <span className="font-medium">Quick Actions</span>
                  {quickActionsExpanded ? (
                    <ChevronDown className="h-4 w-4" />
                  ) : (
                    <ChevronRight className="h-4 w-4" />
                  )}
                </Button>
                
                {quickActionsExpanded && (
                  <div id="quick-actions-content" className="mt-2 space-y-1">
                    {quickActions.map((action) => {
                      const Icon = action.icon;
                      
                      return (
                        <Button
                          key={action.id}
                          variant="ghost"
                          className="w-full justify-start h-auto p-3 text-left text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                          onClick={() => handleNavigation(action.page)}
                          onKeyDown={(e) => handleKeyDown(e, () => handleNavigation(action.page))}
                        >
                          <Icon className="h-4 w-4 mr-3 mt-0.5 flex-shrink-0" />
                          <div className="flex-1 min-w-0">
                            <div className="font-medium">{action.label}</div>
                            <div className="text-xs text-sidebar-foreground/70 mt-0.5">
                              {action.description}
                            </div>
                          </div>
                        </Button>
                      );
                    })}
                  </div>
                )}
              </div>

              <Separator className="bg-sidebar-border" />

              {/* Secondary Navigation */}
              <nav role="navigation" aria-label="Secondary navigation">
                <div className="space-y-1">
                  {secondaryNavItems.map((item) => {
                    const Icon = item.icon;
                    const isActive = currentPage === item.page;
                    
                    return (
                      <Button
                        key={item.id}
                        variant="ghost"
                        className={cn(
                          "w-full justify-start h-10 px-3",
                          isActive 
                            ? "bg-sidebar-accent text-sidebar-accent-foreground" 
                            : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                        )}
                        onClick={() => handleNavigation(item.page)}
                        onKeyDown={(e) => handleKeyDown(e, () => handleNavigation(item.page))}
                        aria-current={isActive ? "page" : undefined}
                      >
                        <Icon className="h-4 w-4 mr-3" />
                        {item.label}
                      </Button>
                    );
                  })}
                </div>
              </nav>
            </div>
          </div>

          {/* User Profile Section */}
          {user && (
            <div className="border-t border-sidebar-border p-4">
              <Card className="bg-sidebar-accent/50 border-sidebar-border">
                <CardContent className="p-4">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-sidebar-primary rounded-full flex items-center justify-center">
                      <User className="h-5 w-5 text-sidebar-primary-foreground" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-sidebar-foreground truncate">
                        {user.name}
                      </p>
                      <p className="text-xs text-sidebar-foreground/70 truncate">
                        {user.email}
                      </p>
                      <div className="mt-1">
                        <span className={cn(
                          "inline-flex items-center px-2 py-1 rounded-full text-xs font-medium",
                          user.subscription === 'premium' 
                            ? "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200"
                            : user.subscription === 'basic'
                            ? "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
                            : "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200"
                        )}>
                          {user.subscription.charAt(0).toUpperCase() + user.subscription.slice(1)}
                        </span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </aside>
    </>
  );
};