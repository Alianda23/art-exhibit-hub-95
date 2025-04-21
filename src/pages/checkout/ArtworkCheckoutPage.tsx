
import React from 'react';
import { useParams, useLocation } from 'react-router-dom';
import ArtworkCheckout from '@/components/checkout/ArtworkCheckout';
import { formatCurrency } from '@/lib/utils';

const ArtworkCheckoutPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const location = useLocation();
  const { artwork } = location.state || { artwork: null };
  
  // If artwork data wasn't passed in location state, we'd normally fetch it
  // But for simplicity, we'll just use what was passed
  
  if (!artwork) {
    return (
      <div className="container mx-auto py-8 px-4">
        <div className="bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 p-4 mb-4">
          <p>Artwork information not available. Please go back and try again.</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="container mx-auto py-8 px-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <img 
            src={artwork.imageUrl} 
            alt={artwork.title} 
            className="w-full h-auto object-cover rounded-lg shadow-md"
            onError={(e) => {
              const target = e.target as HTMLImageElement;
              target.src = '/placeholder.svg';
            }}
          />
          
          <div className="mt-4">
            <h2 className="text-2xl font-bold">{artwork.title}</h2>
            <p className="text-gray-600">by {artwork.artist}</p>
            <p className="text-xl font-bold mt-2">{formatCurrency(artwork.price)}</p>
          </div>
        </div>
        
        <div>
          <ArtworkCheckout artwork={artwork} />
        </div>
      </div>
    </div>
  );
};

export default ArtworkCheckoutPage;
