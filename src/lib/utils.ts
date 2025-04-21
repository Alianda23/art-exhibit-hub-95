
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { AUTH_TOKEN_KEY, USER_DATA_KEY } from "@/config";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Format currency
export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-KE', {
    style: 'currency',
    currency: 'KES',
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(amount);
}

// Format date
export function formatDate(dateString: string): string {
  try {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-KE', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date);
  } catch (error) {
    console.error(`Error formatting date: ${dateString}`, error);
    return dateString || 'N/A';
  }
}

// Authentication helper functions
export function getAuthToken(): string | null {
  return localStorage.getItem(AUTH_TOKEN_KEY);
}

export function setAuthToken(token: string): void {
  localStorage.setItem(AUTH_TOKEN_KEY, token);
}

export function removeAuthToken(): void {
  localStorage.removeItem(AUTH_TOKEN_KEY);
}

export function getUserData(): any {
  const userData = localStorage.getItem(USER_DATA_KEY);
  return userData ? JSON.parse(userData) : null;
}

export function setUserData(userData: any): void {
  localStorage.setItem(USER_DATA_KEY, JSON.stringify(userData));
}

export function removeUserData(): void {
  localStorage.removeItem(USER_DATA_KEY);
}

export function isAuthenticated(): boolean {
  return !!getAuthToken();
}

// Image URL helper to fix placeholder issues
export function getImageUrl(url: string | null | undefined): string {
  if (!url) return '/placeholder.svg';
  
  // If it's an absolute URL or a data URL, return it as is
  if (url.startsWith('http') || url.startsWith('data:')) {
    return url;
  }
  
  // If it's a localhost URL, replace with our hosted placeholder
  if (url.includes('localhost')) {
    return '/placeholder.svg';
  }
  
  // If it's a relative URL, ensure it starts with a slash
  return url.startsWith('/') ? url : `/${url}`;
}
