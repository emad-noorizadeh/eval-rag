/**
 * Session Management Service
 * Author: Emad Noorizadeh
 */

const API_BASE_URL = 'http://localhost:9000';

export interface SessionInfo {
    session_id: string;
    created_at: string;
    remaining_time: number;
    timeout_minutes: number;
}

export interface SessionCreateRequest {
    data_folder?: string;
    collection_name?: string;
}

export interface SessionCreateResponse {
    session_id: string;
    created_at: string;
    remaining_time: number;
    timeout_minutes: number;
}

export interface SessionExtendResponse {
    message: string;
    remaining_time: number;
}

class SessionService {
    private sessionId: string | null = null;
    private sessionTimer: NodeJS.Timeout | null = null;
    private onSessionExpired: (() => void) | null = null;

    constructor() {
        // Don't load session from localStorage during SSR
        // This will be called when needed in the browser
    }

    /**
     * Create a new session
     */
    async createSession(request?: SessionCreateRequest): Promise<SessionCreateResponse> {
        try {
            const response = await fetch(`${API_BASE_URL}/sessions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(request || {}),
            });

            if (!response.ok) {
                throw new Error(`Failed to create session: ${response.statusText}`);
            }

            const sessionData: SessionCreateResponse = await response.json();
            this.sessionId = sessionData.session_id;

            // Save to localStorage
            this.saveSessionToStorage(sessionData);

            // Start session monitoring
            this.startSessionMonitoring();

            return sessionData;
        } catch (error) {
            console.error('Error creating session:', error);
            throw error;
        }
    }

    /**
     * Get current session ID
     */
    getCurrentSessionId(): string | null {
        // Load session from localStorage if not already loaded
        if (this.sessionId === null) {
            this.loadSessionFromStorage();
        }
        return this.sessionId;
    }

    /**
     * Get session information
     */
    async getSessionInfo(sessionId?: string): Promise<SessionInfo | null> {
        const id = sessionId || this.sessionId;
        if (!id) return null;

        try {
            const response = await fetch(`${API_BASE_URL}/sessions/${id}`);

            if (response.status === 404) {
                // Session not found or expired - clear everything
                console.log('Session not found (404), clearing session data');
                this.clearSession();
                return null;
            }

            if (!response.ok) {
                throw new Error(`Failed to get session info: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error getting session info:', error);
            return null;
        }
    }

    /**
     * Extend current session
     */
    async extendSession(sessionId?: string): Promise<SessionExtendResponse | null> {
        const id = sessionId || this.sessionId;
        if (!id) return null;

        try {
            const response = await fetch(`${API_BASE_URL}/sessions/${id}/extend`, {
                method: 'POST',
            });

            if (response.status === 404) {
                // Session not found or expired - clear everything
                console.log('Session extend failed (404), clearing session data');
                this.clearSession();
                return null;
            }

            if (!response.ok) {
                throw new Error(`Failed to extend session: ${response.statusText}`);
            }

            const result = await response.json();

            // Update localStorage with new remaining time
            this.updateSessionInStorage(result.remaining_time);

            return result;
        } catch (error) {
            console.error('Error extending session:', error);
            return null;
        }
    }

    /**
     * End current session
     */
    async endSession(sessionId?: string): Promise<boolean> {
        const id = sessionId || this.sessionId;
        if (!id) return false;

        try {
            const response = await fetch(`${API_BASE_URL}/sessions/${id}`, {
                method: 'DELETE',
            });

            this.clearSession();
            return response.ok;
        } catch (error) {
            console.error('Error ending session:', error);
            this.clearSession();
            return false;
        }
    }

    /**
     * Check if current session is valid
     */
    async isSessionValid(): Promise<boolean> {
        if (!this.sessionId) return false;

        const sessionInfo = await this.getSessionInfo();
        return sessionInfo !== null;
    }

    /**
     * Set callback for session expiration
     */
    setOnSessionExpired(callback: () => void): void {
        this.onSessionExpired = callback;
    }

    /**
     * Start monitoring session expiration
     */
    private startSessionMonitoring(): void {
        // Clear existing timer
        if (this.sessionTimer) {
            clearInterval(this.sessionTimer);
        }

        // Check session every 5 minutes
        this.sessionTimer = setInterval(async () => {
            const isValid = await this.isSessionValid();
            if (!isValid && this.onSessionExpired) {
                this.onSessionExpired();
            }
        }, 5 * 60 * 1000); // 5 minutes
    }

    /**
     * Load session from localStorage
     */
    private loadSessionFromStorage(): void {
        // Check if we're in the browser environment
        if (typeof window === 'undefined' || typeof localStorage === 'undefined') {
            return;
        }

        try {
            const stored = localStorage.getItem('rag_session');
            if (stored) {
                const sessionData = JSON.parse(stored);
                const now = Date.now();
                const sessionAge = now - sessionData.timestamp;
                const thirtyMinutes = 30 * 60 * 1000;

                // Check if session is still valid (less than 30 minutes old)
                if (sessionAge < thirtyMinutes) {
                    this.sessionId = sessionData.session_id;
                    this.startSessionMonitoring();
                } else {
                    // Session expired, clear it
                    localStorage.removeItem('rag_session');
                }
            }
        } catch (error) {
            console.error('Error loading session from storage:', error);
            if (typeof localStorage !== 'undefined') {
                localStorage.removeItem('rag_session');
            }
        }
    }

    /**
     * Save session to localStorage
     */
    private saveSessionToStorage(sessionData: SessionCreateResponse): void {
        // Check if we're in the browser environment
        if (typeof window === 'undefined' || typeof localStorage === 'undefined') {
            return;
        }

        try {
            const sessionInfo = {
                session_id: sessionData.session_id,
                timestamp: Date.now(),
                created_at: sessionData.created_at,
                timeout_minutes: sessionData.timeout_minutes,
            };
            localStorage.setItem('rag_session', JSON.stringify(sessionInfo));
        } catch (error) {
            console.error('Error saving session to storage:', error);
        }
    }

    /**
     * Update session in localStorage
     */
    private updateSessionInStorage(remainingTime: number): void {
        // Check if we're in the browser environment
        if (typeof window === 'undefined' || typeof localStorage === 'undefined') {
            return;
        }

        try {
            const stored = localStorage.getItem('rag_session');
            if (stored) {
                const sessionData = JSON.parse(stored);
                sessionData.remaining_time = remainingTime;
                localStorage.setItem('rag_session', JSON.stringify(sessionData));
            }
        } catch (error) {
            console.error('Error updating session in storage:', error);
        }
    }

    /**
     * Clear session data
     */
    private clearSession(): void {
        this.sessionId = null;
        if (this.sessionTimer) {
            clearInterval(this.sessionTimer);
            this.sessionTimer = null;
        }
        // Check if we're in the browser environment
        if (typeof window !== 'undefined' && typeof localStorage !== 'undefined') {
            localStorage.removeItem('rag_session');
        }
    }

    /**
     * Get session status for display
     */
    async getSessionStatus(): Promise<{
        isValid: boolean;
        sessionId: string | null;
        remainingTime?: number;
    }> {
        const isValid = await this.isSessionValid();
        const sessionInfo = isValid ? await this.getSessionInfo() : null;

        return {
            isValid,
            sessionId: this.sessionId,
            remainingTime: sessionInfo?.remaining_time,
        };
    }
}

// Export singleton instance
export const sessionService = new SessionService();
