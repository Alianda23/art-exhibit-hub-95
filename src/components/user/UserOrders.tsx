
import React, { useEffect, useState } from 'react';
import { getUserOrders, OrderSummary } from '@/services/orderService';
import OrdersList from '@/components/orders/OrdersList';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useToast } from '@/components/ui/use-toast';
import { getAuthToken, getUserData } from '@/lib/utils';

const UserOrders: React.FC = () => {
  const [orders, setOrders] = useState<OrderSummary[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const { toast } = useToast();
  
  useEffect(() => {
    const fetchUserOrders = async () => {
      try {
        setIsLoading(true);
        const token = getAuthToken();
        const userData = getUserData();
        
        if (!token || !userData) {
          toast({
            title: "Authentication Error",
            description: "Please login to view your orders",
            variant: "destructive"
          });
          return;
        }
        
        const ordersData = await getUserOrders(userData.user_id, token);
        console.log('Fetched user orders:', ordersData);
        setOrders(ordersData);
      } catch (error) {
        console.error('Failed to fetch user orders:', error);
        toast({
          title: "Error",
          description: "Failed to load your orders. Please try again.",
          variant: "destructive"
        });
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchUserOrders();
  }, [toast]);
  
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-xl font-bold">My Orders</CardTitle>
      </CardHeader>
      <CardContent>
        <OrdersList orders={orders} isLoading={isLoading} />
      </CardContent>
    </Card>
  );
};

export default UserOrders;
