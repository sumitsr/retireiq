import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { CheckCircle } from 'lucide-react';
import Navbar from '@/components/Navbar';
import Footer from '@/components/Footer';

// Helper components moved here to avoid multiple exports
function Label({ htmlFor, children }: { htmlFor: string, children: React.ReactNode }) {
  return (
    <label htmlFor={htmlFor} className="block text-sm font-medium text-gray-700 mb-1">
      {children}
    </label>
  );
}

function Input({ id, type, placeholder }: { id: string, type: string, placeholder?: string }) {
  return (
    <input
      id={id}
      type={type}
      placeholder={placeholder}
      className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-lloyds-green focus:border-transparent"
    />
  );
}

const Index: React.FC = () => {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      
      <main className="flex-1">
        {/* Hero Section */}
        <section className="bg-gradient-to-r from-lloyds-darkBlue to-lloyds-darkGreen text-white py-20">
          <div className="lloyds-container">
            <div className="flex flex-col md:flex-row items-center">
              <div className="md:w-1/2 mb-10 md:mb-0">
                <h1 className="text-4xl md:text-5xl font-bold mb-6 leading-tight">
                  Plan your perfect retirement with RetireIQ
                </h1>
                <p className="text-xl mb-8 opacity-90">
                  Our intelligent assistant helps you make informed retirement planning decisions tailored to your unique circumstances.
                </p>
                <div className="flex flex-col sm:flex-row space-y-4 sm:space-y-0 sm:space-x-4">
                  <Link to="/chat">
                    <Button className="lloyds-button-primary text-lg py-6 px-8">
                      Start Planning Now
                    </Button>
                  </Link>
                  <Link to="/settings">
                    <Button variant="outline" className="border-white text-white hover:bg-white hover:text-lloyds-darkBlue text-lg py-6 px-8">
                      Configure AI Settings
                    </Button>
                  </Link>
                </div>
              </div>
              <div className="md:w-1/2 md:pl-10">
                <div className="bg-white rounded-lg p-6 shadow-lg">
                  <div className="border-b border-gray-200 pb-4 mb-4">
                    <p className="text-lloyds-darkBlue font-medium">RetireIQ Assistant</p>
                  </div>
                  <div className="space-y-4">
                    <div className="bg-lloyds-lightBlue text-lloyds-darkBlue p-3 rounded-lg inline-block">
                      Hello! I'm your RetireIQ assistant. How can I help with your retirement planning today?
                    </div>
                    <div className="bg-lloyds-green text-white p-3 rounded-lg inline-block ml-auto">
                      When should I start saving for retirement?
                    </div>
                    <div className="bg-lloyds-lightBlue text-lloyds-darkBlue p-3 rounded-lg inline-block animate-fade-in">
                      The best time to start saving is now! The power of compound interest means that starting earlier, even with smaller amounts, can have a significant impact on your retirement fund. Would you like me to explain more about how compound interest works?
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
        
        {/* Features Section */}
        <section className="py-16 bg-lloyds-lightGray">
          <div className="lloyds-container">
            <h2 className="text-3xl font-bold mb-12 text-center text-lloyds-darkGreen">Why Choose RetireIQ?</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="bg-white p-6 rounded-lg shadow-sm">
                <div className="h-12 w-12 bg-lloyds-lightBlue rounded-full flex items-center justify-center mb-4">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-lloyds-darkBlue" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold mb-3 text-lloyds-darkBlue">Personalized Planning</h3>
                <p className="text-gray-600">
                  Get retirement advice tailored to your specific financial situation, goals, and risk tolerance.
                </p>
              </div>
              
              <div className="bg-white p-6 rounded-lg shadow-sm">
                <div className="h-12 w-12 bg-lloyds-lightBlue rounded-full flex items-center justify-center mb-4">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-lloyds-darkBlue" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold mb-3 text-lloyds-darkBlue">Trustworthy Guidance</h3>
                <p className="text-gray-600">
                  Backed by Lloyds Bank's financial expertise and powered by state-of-the-art AI technologies.
                </p>
              </div>
              
              <div className="bg-white p-6 rounded-lg shadow-sm">
                <div className="h-12 w-12 bg-lloyds-lightBlue rounded-full flex items-center justify-center mb-4">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-lloyds-darkBlue" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold mb-3 text-lloyds-darkBlue">24/7 Assistance</h3>
                <p className="text-gray-600">
                  Get answers to your retirement questions anytime, anywhere, with our always-available AI assistant.
                </p>
              </div>
            </div>
          </div>
        </section>
        
        {/* How It Works Section */}
        <section className="py-16">
          <div className="lloyds-container">
            <h2 className="text-3xl font-bold mb-12 text-center text-lloyds-darkGreen">How RetireIQ Works</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
              <div className="text-center">
                <div className="h-16 w-16 bg-lloyds-green rounded-full flex items-center justify-center mx-auto mb-4 text-white font-bold text-xl">1</div>
                <h3 className="text-xl font-semibold mb-2 text-lloyds-darkBlue">Chat with RetireIQ</h3>
                <p className="text-gray-600">
                  Start a conversation with our AI assistant about your retirement goals and concerns.
                </p>
              </div>
              
              <div className="text-center">
                <div className="h-16 w-16 bg-lloyds-green rounded-full flex items-center justify-center mx-auto mb-4 text-white font-bold text-xl">2</div>
                <h3 className="text-xl font-semibold mb-2 text-lloyds-darkBlue">Share Your Situation</h3>
                <p className="text-gray-600">
                  Tell us about your age, income, current savings, and retirement timeline.
                </p>
              </div>
              
              <div className="text-center">
                <div className="h-16 w-16 bg-lloyds-green rounded-full flex items-center justify-center mx-auto mb-4 text-white font-bold text-xl">3</div>
                <h3 className="text-xl font-semibold mb-2 text-lloyds-darkBlue">Get Recommendations</h3>
                <p className="text-gray-600">
                  Receive personalized advice on savings strategies, investment options, and pension planning.
                </p>
              </div>
              
              <div className="text-center">
                <div className="h-16 w-16 bg-lloyds-green rounded-full flex items-center justify-center mx-auto mb-4 text-white font-bold text-xl">4</div>
                <h3 className="text-xl font-semibold mb-2 text-lloyds-darkBlue">Take Action</h3>
                <p className="text-gray-600">
                  Implement your retirement plan with confidence, checking back for updates and adjustments.
                </p>
              </div>
            </div>
          </div>
        </section>
        
        {/* Benefits Section */}
        <section className="py-16 bg-lloyds-lightGray">
          <div className="lloyds-container">
            <div className="flex flex-col md:flex-row items-center">
              <div className="md:w-1/2 mb-8 md:mb-0 md:pr-10">
                <h2 className="text-3xl font-bold mb-6 text-lloyds-darkGreen">Benefits of RetireIQ</h2>
                
                <div className="space-y-4">
                  <div className="flex items-start">
                    <CheckCircle className="text-lloyds-green mr-2 h-6 w-6 shrink-0" />
                    <div>
                      <h3 className="font-semibold text-lloyds-darkBlue">Informed Decision Making</h3>
                      <p className="text-gray-600 text-sm">Get clear, jargon-free explanations of complex retirement topics.</p>
                    </div>
                  </div>
                  
                  <div className="flex items-start">
                    <CheckCircle className="text-lloyds-green mr-2 h-6 w-6 shrink-0" />
                    <div>
                      <h3 className="font-semibold text-lloyds-darkBlue">Personalized Strategy</h3>
                      <p className="text-gray-600 text-sm">Receive advice tailored to your unique financial circumstances.</p>
                    </div>
                  </div>
                  
                  <div className="flex items-start">
                    <CheckCircle className="text-lloyds-green mr-2 h-6 w-6 shrink-0" />
                    <div>
                      <h3 className="font-semibold text-lloyds-darkBlue">Continuous Support</h3>
                      <p className="text-gray-600 text-sm">Update your plan as your circumstances change over time.</p>
                    </div>
                  </div>
                  
                  <div className="flex items-start">
                    <CheckCircle className="text-lloyds-green mr-2 h-6 w-6 shrink-0" />
                    <div>
                      <h3 className="font-semibold text-lloyds-darkBlue">Financial Confidence</h3>
                      <p className="text-gray-600 text-sm">Feel more secure about your future with a solid retirement plan.</p>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="md:w-1/2">
                <div className="bg-white rounded-lg p-6 shadow-md">
                  <h3 className="text-xl font-semibold mb-4 text-lloyds-darkBlue">Retirement Planning Calculator</h3>
                  <p className="mb-6 text-gray-600">
                    Get a quick estimate of your retirement needs based on your current age and desired retirement lifestyle.
                  </p>
                  
                  <div className="space-y-4 mb-6">
                    <div>
                      <Label htmlFor="current-age">Your Current Age</Label>
                      <Input id="current-age" type="number" placeholder="e.g., 35" />
                    </div>
                    
                    <div>
                      <Label htmlFor="retirement-age">Planned Retirement Age</Label>
                      <Input id="retirement-age" type="number" placeholder="e.g., 67" />
                    </div>
                    
                    <div>
                      <Label htmlFor="monthly-contribution">Monthly Contribution (£)</Label>
                      <Input id="monthly-contribution" type="number" placeholder="e.g., 500" />
                    </div>
                  </div>
                  
                  <Link to="/chat">
                    <Button className="lloyds-button-primary w-full">
                      Get Personalized Advice
                    </Button>
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </section>
        
        {/* CTA Section */}
        <section className="bg-lloyds-darkGreen text-white py-16">
          <div className="lloyds-container text-center">
            <h2 className="text-3xl font-bold mb-4">Start Your Retirement Journey Today</h2>
            <p className="text-xl mb-8 max-w-3xl mx-auto opacity-90">
              It's never too early or too late to begin planning for retirement. 
              Let RetireIQ help you create a personalized plan for financial security.
            </p>
            <Link to="/chat">
              <Button className="bg-white text-lloyds-darkGreen hover:bg-lloyds-lightGray text-lg py-6 px-10">
                Chat with RetireIQ Now
              </Button>
            </Link>
          </div>
        </section>
      </main>
      
      <Footer />
    </div>
  );
};

export default Index;
