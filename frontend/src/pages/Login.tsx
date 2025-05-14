
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { pythonBackendService } from '@/services/pythonBackendService';
import Navbar from '@/components/Navbar';
import Footer from '@/components/Footer';
import { useToast } from '@/hooks/use-toast';

const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toast } = useToast();
  const navigate = useNavigate();
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Basic validation
    if (!email || !password) {
      toast({
        title: 'Missing fields',
        description: 'Please enter both email and password.',
        variant: 'destructive',
      });
      return;
    }
    
    setIsSubmitting(true);
    
    try {
      await pythonBackendService.auth.login(email, password);
      toast({
        title: 'Login successful',
        description: 'Welcome back to RetireIQ!',
      });
      navigate('/chat');
    } catch (error) {
      console.error('Login error:', error);
      toast({
        title: 'Login failed',
        description: 'Invalid email or password. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setIsSubmitting(false);
    }
  };
  
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      
      <main className="flex-1 flex items-center justify-center py-10">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle className="text-lloyds-darkGreen">Log in</CardTitle>
            <CardDescription>
              Access your RetireIQ account for personalized retirement advice
            </CardDescription>
          </CardHeader>
          
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input 
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Enter your email"
                  required
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input 
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  required
                />
              </div>
              
              <Button 
                type="submit" 
                className="lloyds-button-primary w-full"
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Logging in...' : 'Log in'}
              </Button>
            </form>
          </CardContent>
          
          <CardFooter className="flex flex-col space-y-4">
            <p className="text-sm text-gray-500">
              Don't have an account?{' '}
              <Button 
                variant="link" 
                onClick={() => navigate('/register')}
                className="p-0 h-auto text-lloyds-darkBlue"
              >
                Sign up
              </Button>
            </p>
            
            <Button 
              variant="link"
              className="text-sm text-lloyds-darkBlue"
            >
              Forgot password?
            </Button>
          </CardFooter>
        </Card>
      </main>
      
      <Footer />
    </div>
  );
};

export default Login;
