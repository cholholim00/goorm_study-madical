// lib/authStorage.ts

export type StoredUser = {
    id: number;
    email: string;
    name?: string | null;
};

const TOKEN_KEY = 'hc_token';
const USER_KEY = 'hc_user';

export function getToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem(TOKEN_KEY);
}

export function setAuth(token: string, user: StoredUser) {
    if (typeof window === 'undefined') return;
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function getUser(): StoredUser | null {
    if (typeof window === 'undefined') return null;

    const raw = localStorage.getItem(USER_KEY);
    if (!raw) return null;

    try {
        return JSON.parse(raw) as StoredUser;
    } catch {
        return null;
    }
}

export function clearAuth() {
    if (typeof window === 'undefined') return;
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
}
