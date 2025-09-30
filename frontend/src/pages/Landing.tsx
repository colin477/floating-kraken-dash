import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

const Landing = () => {
  const navigate = useNavigate();
  
  const handleStartTrial = () => {
    // Navigate to auth page with signup tab active
    navigate('/auth?tab=signup');
  };

  return (
    <div className="bg-background min-h-screen font-sans text-foreground">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 min-h-screen flex flex-col justify-center">
        <main className="bg-card rounded-lg p-6 shadow-lg text-center mb-8">
          <header className="mb-8">
            <h1 className="text-4xl font-bold text-foreground mb-4 leading-tight">
              Stop Stressing About Dinner. Start Saving Money.
            </h1>
            <p className="text-xl text-muted-foreground mb-10 leading-relaxed max-w-2xl mx-auto">
              Turn your grocery receipts into personalized meal plans in 5 minutes. Save 20-30% on groceries with AI-powered local deal optimization.
            </p>
          </header>

          <section className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12" aria-label="Key Benefits">
            <Card className="text-left hover:shadow-lg transition-all duration-200 hover:scale-[1.02] border-l-4 border-l-primary">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg font-semibold text-foreground flex items-center gap-2">
                  <span className="text-2xl" aria-hidden="true">📸</span>
                  <strong>Snap & Plan</strong>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-muted-foreground text-sm">
                  Photo your receipt, get instant meal recommendations
                </CardDescription>
              </CardContent>
            </Card>

            <Card className="text-left hover:shadow-lg transition-all duration-200 hover:scale-[1.02] border-l-4 border-l-primary">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg font-semibold text-foreground flex items-center gap-2">
                  <span className="text-2xl" aria-hidden="true">💰</span>
                  <strong>Smart Savings</strong>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-muted-foreground text-sm">
                  Find the best local deals automatically
                </CardDescription>
              </CardContent>
            </Card>

            <Card className="text-left hover:shadow-lg transition-all duration-200 hover:scale-[1.02] border-l-4 border-l-primary">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg font-semibold text-foreground flex items-center gap-2">
                  <span className="text-2xl" aria-hidden="true">⏰</span>
                  <strong>5-Minute Planning</strong>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-muted-foreground text-sm">
                  Weekly meal plans in minutes, not hours
                </CardDescription>
              </CardContent>
            </Card>

            <Card className="text-left hover:shadow-lg transition-all duration-200 hover:scale-[1.02] border-l-4 border-l-primary">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg font-semibold text-foreground flex items-center gap-2">
                  <span className="text-2xl" aria-hidden="true">🍽️</span>
                  <strong>Zero Waste</strong>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-muted-foreground text-sm">
                  Creative leftover suggestions and batch cooking guides
                </CardDescription>
              </CardContent>
            </Card>
          </section>

          <section className="text-center">
            <Button
              onClick={handleStartTrial}
              size="lg"
              className="text-lg font-semibold px-10 py-3 rounded-full bg-primary text-primary-foreground hover:bg-primary/90 transition-all duration-200 shadow-lg hover:shadow-xl"
              role="button"
              aria-label="Start your free 7-day trial of EZ Eatin'"
            >
              Start Your Free 7-Day Trial
            </Button>
          </section>
        </main>
      </div>
    </div>
  );
};

export default Landing;