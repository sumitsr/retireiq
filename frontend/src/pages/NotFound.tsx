
import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import Navbar from '@/components/Navbar';
import Footer from '@/components/Footer';

const NotFound: React.FC = () => {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      
      <main className="flex-1 flex items-center justify-center">
        <div className="lloyds-container py-20 text-center">
          <div className="w-24 h-24 bg-lloyds-lightBlue rounded-full flex items-center justify-center mx-auto mb-6">
            <span className="text-4xl font-bold text-lloyds-darkBlue">404</span>
          </div>
          
          <h1 className="text-3xl font-bold mb-4 text-lloyds-darkGreen">Page Not Found</h1>
          <p className="text-xl text-gray-600 mb-8 max-w-md mx-auto">
            Sorry, we couldn't find the page you were looking for.
          </p>
          
          <Link to="/">
            <Button className="lloyds-button-primary">
              Return to Home
            </Button>
          </Link>
        </div>
      </main>
      
      <Footer />
    </div>
  );
};

export default NotFound;
