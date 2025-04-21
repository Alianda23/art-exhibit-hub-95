
import { API_URL } from '@/config';

// Order interfaces
export interface OrderSummary {
  id: string;
  user_id: string;
  user_name: string;
  reference_id: string;
  item_title: string;
  amount: number;
  payment_status: 'pending' | 'completed' | 'failed';
  type: 'artwork' | 'exhibition';
  created_at: string;
}

export interface OrderDetail extends OrderSummary {
  name: string;
  email: string;
  phone: string;
  delivery_address?: string;
  mpesa_transaction_id?: string;
}

export interface ArtworkOrder {
  artworkId: string;
  userId: string;
  amount: number;
  name: string;
  email: string;
  phone: string;
  deliveryAddress: string;
}

// Get all orders (admin only)
export const getAllOrders = async (token: string): Promise<OrderSummary[]> => {
  try {
    const response = await fetch(`${API_URL}/api/orders`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to fetch orders');
    }
    
    const data = await response.json();
    return data.orders || [];
  } catch (error) {
    console.error('Error fetching orders:', error);
    throw error;
  }
};

// Get orders for a specific user
export const getUserOrders = async (userId: string, token: string): Promise<OrderSummary[]> => {
  try {
    const response = await fetch(`${API_URL}/api/users/${userId}/orders`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to fetch user orders');
    }
    
    const data = await response.json();
    return data.orders || [];
  } catch (error) {
    console.error('Error fetching user orders:', error);
    throw error;
  }
};

// Create new artwork order
export const createArtworkOrder = async (order: ArtworkOrder, token: string): Promise<any> => {
  try {
    const response = await fetch(`${API_URL}/api/orders/artwork`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(order)
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to create order');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error creating artwork order:', error);
    throw error;
  }
};

// Payment processing
export const processPayment = async (
  phoneNumber: string, 
  amount: number, 
  orderType: 'artwork' | 'exhibition',
  orderId: string, 
  userId: string, 
  token: string
): Promise<any> => {
  try {
    console.log('Processing payment:', { phoneNumber, amount, orderType, orderId, userId });
    
    const response = await fetch(`${API_URL}/api/mpesa/stkpush`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        phoneNumber,
        amount,
        orderType,
        orderId,
        userId,
        accountReference: `${orderType}-${orderId}`
      })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Payment processing failed');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error processing payment:', error);
    throw error;
  }
};

// Check payment status
export const checkPaymentStatus = async (checkoutRequestId: string): Promise<any> => {
  try {
    const response = await fetch(`${API_URL}/api/mpesa/status/${checkoutRequestId}`);
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to check payment status');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error checking payment status:', error);
    throw error;
  }
};
