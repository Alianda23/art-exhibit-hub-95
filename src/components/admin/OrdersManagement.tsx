
import React, { useEffect, useState } from 'react';
import { getAllOrders, OrderSummary } from '@/services/orderService';
import OrdersList from '@/components/orders/OrdersList';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/components/ui/use-toast';
import { getAuthToken } from '@/lib/utils';

const OrdersManagement: React.FC = () => {
  const [orders, setOrders] = useState<OrderSummary[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const { toast } = useToast();
  
  useEffect(() => {
    const fetchOrders = async () => {
      try {
        setIsLoading(true);
        const token = getAuthToken();
        
        if (!token) {
          toast({
            title: "Authentication Error",
            description: "Please login to view orders",
            variant: "destructive"
          });
          return;
        }
        
        const ordersData = await getAllOrders(token);
        console.log('Fetched orders:', ordersData);
        setOrders(ordersData);
      } catch (error) {
        console.error('Failed to fetch orders:', error);
        toast({
          title: "Error",
          description: "Failed to load orders. Please try again.",
          variant: "destructive"
        });
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchOrders();
  }, [toast]);
  
  // Filter orders by type
  const artworkOrders = orders.filter(order => order.type === 'artwork');
  const exhibitionOrders = orders.filter(order => order.type === 'exhibition');
  
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-2xl font-bold">Orders Management</CardTitle>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="all">
          <TabsList className="mb-4">
            <TabsTrigger value="all">All Orders ({orders.length})</TabsTrigger>
            <TabsTrigger value="artwork">Artwork Orders ({artworkOrders.length})</TabsTrigger>
            <TabsTrigger value="exhibition">Exhibition Orders ({exhibitionOrders.length})</TabsTrigger>
          </TabsList>
          
          <TabsContent value="all">
            <OrdersList orders={orders} isLoading={isLoading} />
          </TabsContent>
          
          <TabsContent value="artwork">
            <OrdersList orders={artworkOrders} isLoading={isLoading} />
          </TabsContent>
          
          <TabsContent value="exhibition">
            <OrdersList orders={exhibitionOrders} isLoading={isLoading} />
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};

export default OrdersManagement;
