
// API URL configuration
// Use environment variable in production, fallback to localhost for development
export const API_URL = import.meta.env.VITE_API_URL || 'https://id-preview--c0ba9a66-2837-4741-8fe8-0099b7c50041.lovable.app';

// Default placeholder image that's hosted on our own server
export const DEFAULT_PLACEHOLDER = '/placeholder.svg';

// Authentication token storage key
export const AUTH_TOKEN_KEY = 'afriart_auth_token';
export const USER_DATA_KEY = 'afriart_user_data';
