import { API_URL } from '@/config';

export interface OrderSummary {
  id: string;
  user_id: string;
  reference_id?: string;
  item_title: string;
  amount: number;
  payment_status: string;
  type: 'artwork' | 'exhibition';
  created_at: string;
}

export const getUserOrders = async (userId: string, token: string): Promise<OrderSummary[]> => {
  try {
    console.log(`Fetching orders for user ${userId}`);
    const response = await fetch(`${API_URL}/orders/user/${userId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      }
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch orders: ${response.statusText}`);
    }

    const data = await response.json();
    console.log('Orders API response:', data);
    
    // Combine artwork orders and exhibition bookings
    let allOrders: OrderSummary[] = [];
    
    if (data.orders && Array.isArray(data.orders)) {
      const artworkOrders = data.orders.map((order: any) => ({
        ...order,
        type: 'artwork'
      }));
      allOrders = [...allOrders, ...artworkOrders];
    }
    
    if (data.bookings && Array.isArray(data.bookings)) {
      const exhibitionBookings = data.bookings.map((booking: any) => ({
        id: booking.id,
        user_id: booking.user_id,
        reference_id: booking.exhibition_id,
        item_title: booking.exhibition_title || 'Exhibition',
        amount: booking.total_amount,
        payment_status: booking.status || booking.payment_status,
        type: 'exhibition',
        created_at: booking.booking_date || booking.created_at
      }));
      allOrders = [...allOrders, ...exhibitionBookings];
    }
    
    console.log('Processed orders and bookings:', allOrders);
    return allOrders;
  } catch (error) {
    console.error('Error fetching user orders:', error);
    throw error;
  }
};

export const createOrder = async (orderData: any, token: string): Promise<any> => {
  try {
    const response = await fetch(`${API_URL}/orders`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(orderData)
    });

    if (!response.ok) {
      throw new Error(`Failed to create order: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error creating order:', error);
    throw error;
  }
};

// Add missing function getAllOrders
export const getAllOrders = async (token: string): Promise<OrderSummary[]> => {
  try {
    console.log('Fetching all orders');
    const response = await fetch(`${API_URL}/orders/all`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      }
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch orders: ${response.statusText}`);
    }

    const data = await response.json();
    console.log('All orders API response:', data);
    
    // Combine artwork orders and exhibition bookings
    let allOrders: OrderSummary[] = [];
    
    if (data.orders && Array.isArray(data.orders)) {
      const artworkOrders = data.orders.map((order: any) => ({
        ...order,
        type: 'artwork'
      }));
      allOrders = [...allOrders, ...artworkOrders];
    }
    
    if (data.bookings && Array.isArray(data.bookings)) {
      const exhibitionBookings = data.bookings.map((booking: any) => ({
        id: booking.id,
        user_id: booking.user_id,
        reference_id: booking.exhibition_id,
        item_title: booking.exhibition_title || 'Exhibition',
        amount: booking.total_amount,
        payment_status: booking.status || booking.payment_status,
        type: 'exhibition',
        created_at: booking.booking_date || booking.created_at
      }));
      allOrders = [...allOrders, ...exhibitionBookings];
    }
    
    console.log('Processed all orders and bookings:', allOrders);
    return allOrders;
  } catch (error) {
    console.error('Error fetching all orders:', error);
    throw error;
  }
};

// Add missing function processPayment
export const processPayment = async (
  phoneNumber: string,
  amount: number,
  orderType: 'artwork' | 'exhibition',
  referenceId: string,
  userId: string,
  token: string
): Promise<any> => {
  try {
    console.log(`Processing payment for ${orderType} with ID ${referenceId}`);
    
    // Format phone number (ensure it starts with 254)
    let formattedPhone = phoneNumber.trim();
    if (formattedPhone.startsWith('0')) {
      formattedPhone = `254${formattedPhone.substring(1)}`;
    } else if (!formattedPhone.startsWith('254')) {
      formattedPhone = `254${formattedPhone}`;
    }
    
    const response = await fetch(`${API_URL}/payment/mpesa`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        phoneNumber: formattedPhone,
        amount,
        orderType,
        referenceId,
        userId
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || `Payment processing failed: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error processing payment:', error);
    throw error;
  }
};
