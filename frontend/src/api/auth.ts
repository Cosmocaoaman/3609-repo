export type LoginResponse = { mfa_required: boolean; user_id: number; message: string };
export type VerifyResponse = { success: boolean; user_id: number; username: string; message: string } & Partial<{ is_staff: boolean; is_superuser: boolean; is_admin: boolean }>;
export type ResendOtpResponse = { success: boolean; message: string; email_status?: string; delivery_method?: string };
export type ToggleAnonymousResponse = { success: boolean; is_anonymous: boolean; message: string };

import { fetchJson } from './client';

export async function register(email: string, password: string, confirm: string, username: string, isAdmin: boolean = false) {
  const res = await fetchJson('/api/auth/register/', {
    method: 'POST',
    body: JSON.stringify({ email, password, confirm_password: confirm, username, is_admin: isAdmin })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Registration failed');
  return data;
}

export async function login(email: string, password: string): Promise<LoginResponse> {
  const res = await fetchJson('/api/auth/login/', {
    method: 'POST',
    body: JSON.stringify({ email, password })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Login failed');
  return data;
}

export async function verifyOtp(userId: number, otp: string): Promise<VerifyResponse> {
  const res = await fetchJson('/api/auth/verify-otp/', {
    method: 'POST',
    body: JSON.stringify({ user_id: userId, otp })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'OTP verify failed');
  return data;
}

export async function resendOtp(userId: number, email?: string): Promise<ResendOtpResponse> {
  const res = await fetchJson('/api/auth/resend-otp/', {
    method: 'POST',
    body: JSON.stringify({ user_id: userId, email })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to resend OTP');
  return data;
}

export async function logout() {
  const res = await fetchJson('/api/auth/logout/', { method: 'POST' });
  if (!res.ok) throw new Error('Logout failed');
}

export async function toggleAnonymousMode(isAnonymous: boolean): Promise<ToggleAnonymousResponse> {
  const res = await fetchJson('/api/auth/toggle-anonymous/', {
    method: 'POST',
    body: JSON.stringify({ is_anonymous: isAnonymous })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Toggle anonymous mode failed');
  return data;
}

