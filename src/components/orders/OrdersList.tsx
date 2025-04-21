
import React from 'react';
import { OrderSummary } from '@/services/orderService';
import { formatDate } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';

interface OrdersListProps {
  orders: OrderSummary[];
  isLoading: boolean;
}

const OrdersList = ({ orders, isLoading }: OrdersListProps) => {
  // Function to determine badge color based on payment status
  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <Badge className="bg-green-500">Completed</Badge>;
      case 'pending':
        return <Badge className="bg-yellow-500">Pending</Badge>;
      case 'failed':
        return <Badge className="bg-red-500">Failed</Badge>;
      default:
        return <Badge className="bg-gray-500">{status}</Badge>;
    }
  };

  if (isLoading) {
    return <div className="flex justify-center p-4">Loading orders...</div>;
  }

  if (!orders || orders.length === 0) {
    return <div className="text-center p-4">No orders found.</div>;
  }

  return (
    <div className="overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Order ID</TableHead>
            <TableHead>Item</TableHead>
            <TableHead>Type</TableHead>
            <TableHead>Amount</TableHead>
            <TableHead>Date</TableHead>
            <TableHead>Status</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {orders.map((order) => (
            <TableRow key={order.id}>
              <TableCell className="font-medium">{order.id}</TableCell>
              <TableCell>{order.item_title}</TableCell>
              <TableCell className="capitalize">{order.type}</TableCell>
              <TableCell>KES {order.amount.toFixed(2)}</TableCell>
              <TableCell>{formatDate(order.created_at)}</TableCell>
              <TableCell>{getStatusBadge(order.payment_status)}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
};

export default OrdersList;
