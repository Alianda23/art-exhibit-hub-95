
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { processPayment } from '@/services/orderService';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/components/ui/use-toast';
import { formatCurrency, getAuthToken, getUserData } from '@/lib/utils';

interface ArtworkCheckoutProps {
  artwork: {
    id: string;
    title: string;
    artist: string;
    price: number;
    imageUrl: string;
  };
}

const ArtworkCheckout: React.FC<ArtworkCheckoutProps> = ({ artwork }) => {
  const [phoneNumber, setPhoneNumber] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();
  const navigate = useNavigate();
  
  const handleCheckout = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      setIsLoading(true);
      
      // Format phone number (ensure it starts with 254)
      let formattedPhone = phoneNumber.trim();
      if (formattedPhone.startsWith('0')) {
        formattedPhone = `254${formattedPhone.substring(1)}`;
      } else if (!formattedPhone.startsWith('254')) {
        formattedPhone = `254${formattedPhone}`;
      }
      
      // Get auth token and user data
      const token = getAuthToken();
      const userData = getUserData();
      
      if (!token || !userData) {
        toast({
          title: "Authentication Error",
          description: "Please login to complete your purchase",
          variant: "destructive"
        });
        navigate('/login');
        return;
      }
      
      // Process the payment
      console.log('Processing payment for artwork:', artwork.id);
      const result = await processPayment(
        formattedPhone,
        artwork.price,
        'artwork',
        artwork.id,
        userData.user_id,
        token
      );
      
      console.log('Payment response:', result);
      
      if (result.success) {
        toast({
          title: "Order Placed Successfully",
          description: "We've initiated the payment process. You'll receive an STK push notification on your phone.",
        });
        
        // Poll for payment status
        const checkStatusInterval = setInterval(async () => {
          try {
            const statusResult = await fetch(`/api/mpesa/status/${result.stk.checkout_request_id}`);
            const statusData = await statusResult.json();
            
            if (statusData.status === 'completed') {
              clearInterval(checkStatusInterval);
              toast({
                title: "Payment Completed",
                description: "Your payment has been completed successfully!",
                variant: "default"
              });
              navigate('/profile/orders');
            } else if (statusData.status === 'failed') {
              clearInterval(checkStatusInterval);
              toast({
                title: "Payment Failed",
                description: "Your payment attempt failed. Please try again.",
                variant: "destructive"
              });
            }
          } catch (error) {
            console.error('Error checking payment status:', error);
          }
        }, 5000); // Check every 5 seconds
        
        // Stop polling after 2 minutes
        setTimeout(() => {
          clearInterval(checkStatusInterval);
        }, 120000);
        
        // Navigate to orders page
        navigate('/profile/orders');
      } else {
        toast({
          title: "Payment Failed",
          description: result.error || "Failed to process your payment. Please try again.",
          variant: "destructive"
        });
      }
    } catch (error) {
      console.error('Checkout error:', error);
      toast({
        title: "Checkout Error",
        description: "Something went wrong during checkout. Please try again.",
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <Card className="max-w-md mx-auto">
      <CardHeader>
        <CardTitle>Checkout</CardTitle>
        <CardDescription>Purchase {artwork.title} by {artwork.artist}</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleCheckout}>
          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">Artwork:</span>
                <span className="text-sm">{artwork.title}</span>
              </div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">Artist:</span>
                <span className="text-sm">{artwork.artist}</span>
              </div>
              <div className="flex items-center justify-between mb-4">
                <span className="text-sm font-medium">Price:</span>
                <span className="text-sm font-bold">{formatCurrency(artwork.price)}</span>
              </div>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="phone">M-Pesa Phone Number</Label>
              <Input
                id="phone"
                placeholder="e.g. 0712345678 or 254712345678"
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
                required
              />
              <p className="text-xs text-gray-500">Enter your M-Pesa phone number to receive payment prompt</p>
            </div>
          </div>
          
          <CardFooter className="flex justify-between px-0 pt-4">
            <Button 
              type="button" 
              variant="outline" 
              onClick={() => navigate(-1)}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? 'Processing...' : 'Pay Now'}
            </Button>
          </CardFooter>
        </form>
      </CardContent>
    </Card>
  );
};

export default ArtworkCheckout;
