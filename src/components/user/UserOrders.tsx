
import React, { useEffect, useState } from 'react';
import { getUserOrders, OrderSummary } from '@/services/orderService';
import OrdersList from '@/components/orders/OrdersList';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useToast } from '@/components/ui/use-toast';
import { getAuthToken, getUserData } from '@/lib/utils';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

const UserOrders: React.FC = () => {
  const [orders, setOrders] = useState<OrderSummary[]>([]);
  const [bookings, setBookings] = useState<OrderSummary[]>([]);
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
        
        // Separate orders and bookings
        const artworkOrders = ordersData.filter((order: OrderSummary) => order.type === 'artwork');
        const exhibitionBookings = ordersData.filter((order: OrderSummary) => order.type === 'exhibition');
        
        setOrders(artworkOrders);
        setBookings(exhibitionBookings);
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
        <Tabs defaultValue="orders">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="orders">Artwork Orders</TabsTrigger>
            <TabsTrigger value="bookings">Exhibition Bookings</TabsTrigger>
          </TabsList>
          
          <TabsContent value="orders">
            <OrdersList orders={orders} isLoading={isLoading} />
          </TabsContent>
          
          <TabsContent value="bookings">
            <OrdersList orders={bookings} isLoading={isLoading} />
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};

export default UserOrders;
