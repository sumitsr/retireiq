
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

const Register: React.FC = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toast } = useToast();
  const navigate = useNavigate();
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Basic validation
    if (!name || !email || !password) {
      toast({
        title: 'Missing fields',
        description: 'Please fill out all required fields.',
        variant: 'destructive',
      });
      return;
    }
    
    if (password !== confirmPassword) {
      toast({
        title: 'Passwords do not match',
        description: 'Please ensure your passwords match.',
        variant: 'destructive',
      });
      return;
    }
    
    setIsSubmitting(true);
    
    try {
      await pythonBackendService.auth.register(email, password, name);
      toast({
        title: 'Account created',
        description: 'Your account has been created successfully.',
      });
      navigate('/chat');
    } catch (error) {
      console.error('Registration error:', error);
      toast({
        title: 'Registration failed',
        description: 'Could not create your account. Please try again.',
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
            <CardTitle className="text-lloyds-darkGreen">Create an account</CardTitle>
            <CardDescription>
              Join RetireIQ to get personalized retirement planning advice
            </CardDescription>
          </CardHeader>
          
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name">Full Name</Label>
                <Input 
                  id="name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Enter your full name"
                  required
                />
              </div>
              
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
                  placeholder="Create a password"
                  required
                  minLength={8}
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="confirmPassword">Confirm Password</Label>
                <Input 
                  id="confirmPassword"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Confirm your password"
                  required
                  minLength={8}
                />
              </div>
              
              <Button 
                type="submit" 
                className="lloyds-button-primary w-full"
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Creating account...' : 'Create Account'}
              </Button>
            </form>
          </CardContent>
          
          <CardFooter className="flex justify-center">
            <p className="text-sm text-gray-500">
              Already have an account?{' '}
              <Button 
                variant="link" 
                onClick={() => navigate('/login')}
                className="p-0 h-auto text-lloyds-darkBlue"
              >
                Log in
              </Button>
            </p>
          </CardFooter>
        </Card>
      </main>
      
      <Footer />
    </div>
  );
};

export default Register;
