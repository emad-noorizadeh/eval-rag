/**
 * Session Management Hook
 * Author: Emad Noorizadeh
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { sessionService, SessionInfo } from '../services/sessionService';

export interface SessionStatus {
    isValid: boolean;
    sessionId: string | null;
    remainingTime?: number;
    isLoading: boolean;
    error: string | null;
}

export function useSession() {
    const [sessionStatus, setSessionStatus] = useState<SessionStatus>({
        isValid: false,
        sessionId: null,
        remainingTime: undefined,
        isLoading: true,
        error: null
    });

    const sessionInitialized = useRef(false);
    const sessionTimer = useRef<NodeJS.Timeout | null>(null);
    const activityTimer = useRef<NodeJS.Timeout | null>(null);

    // Initialize session on mount
    const initializeSession = useCallback(async () => {
        if (sessionInitialized.current) {
            console.log('Session already initialized, skipping...');
            return;
        }

        // Set flag immediately to prevent race conditions
        sessionInitialized.current = true;
        console.log('Initializing session...');
        try {
            setSessionStatus(prev => ({ ...prev, isLoading: true, error: null }));

            // Check if we have a valid session in localStorage
            const currentSessionId = sessionService.getCurrentSessionId();

            if (currentSessionId) {
                // Verify the session is still valid
                try {
                    const isValid = await sessionService.isSessionValid();
                    if (isValid) {
                        const sessionInfo = await sessionService.getSessionInfo();
                        setSessionStatus({
                            isValid: true,
                            sessionId: currentSessionId,
                            remainingTime: sessionInfo?.remaining_time,
                            isLoading: false,
                            error: null
                        });
                        return;
                    } else {
                        // Session expired, clear it
                        console.log('Session validation failed, clearing session');
                        await sessionService.endSession();
                    }
                } catch (error) {
                    // If validation fails, clear the session and start fresh
                    console.log('Session validation error, clearing session:', error);
                    await sessionService.endSession();
                }
            }

            // Create a new session
            const sessionData = await sessionService.createSession();
            setSessionStatus({
                isValid: true,
                sessionId: sessionData.session_id,
                remainingTime: sessionData.remaining_time,
                isLoading: false,
                error: null
            });
        } catch (error) {
            console.error('Error initializing session:', error);
            sessionInitialized.current = false; // Reset flag on error
            setSessionStatus({
                isValid: false,
                sessionId: null,
                remainingTime: undefined,
                isLoading: false,
                error: 'Failed to initialize session. Please refresh the page.'
            });
        }
    }, []);

    // Extend session on user activity
    const extendSession = useCallback(async () => {
        if (!sessionStatus.sessionId || !sessionStatus.isValid) {
            console.log('Skipping extend - no valid session');
            return;
        }

        console.log('Extending session:', sessionStatus.sessionId);
        try {
            const result = await sessionService.extendSession();
            if (result === null) {
                // Session was cleared due to 404, create a new session automatically
                console.log('Session expired, creating new session...');
                try {
                    await initializeSession();
                } catch (error) {
                    console.error('Failed to create new session:', error);
                    setSessionStatus(prev => ({
                        ...prev,
                        isValid: false,
                        error: 'Session expired and failed to create new session. Please refresh the page.'
                    }));
                }
                return;
            }

            const status = await sessionService.getSessionStatus();
            setSessionStatus(prev => ({
                ...prev,
                remainingTime: status.remainingTime
            }));
        } catch (error) {
            console.error('Error extending session:', error);
            // If extend fails, mark session as invalid
            setSessionStatus(prev => ({
                ...prev,
                isValid: false,
                error: 'Session error. Please refresh the page.'
            }));
        }
    }, [sessionStatus.sessionId, sessionStatus.isValid]);

    // Clear session
    const clearSession = useCallback(async () => {
        if (sessionStatus.sessionId) {
            await sessionService.endSession();
        }
        setSessionStatus({
            isValid: false,
            sessionId: null,
            remainingTime: undefined,
            isLoading: false,
            error: null
        });
        sessionInitialized.current = false;
    }, [sessionStatus.sessionId]);

    // Create new session
    const createNewSession = useCallback(async () => {
        await clearSession();
        sessionInitialized.current = false;
        // Call initializeSession directly without dependencies
        await initializeSession();
    }, [clearSession]);

    // Set up session monitoring
    useEffect(() => {
        const startSessionMonitoring = () => {
            // Clear existing timers
            if (sessionTimer.current) {
                clearInterval(sessionTimer.current);
            }
            if (activityTimer.current) {
                clearTimeout(activityTimer.current);
            }

            if (!sessionStatus.isValid || !sessionStatus.sessionId) {
                return;
            }

            // Check session validity every 2 minutes
            sessionTimer.current = setInterval(async () => {
                const isValid = await sessionService.isSessionValid();
                if (!isValid) {
                    setSessionStatus(prev => ({
                        ...prev,
                        isValid: false,
                        error: 'Session expired. Please refresh the page.'
                    }));
                    if (sessionTimer.current) {
                        clearInterval(sessionTimer.current);
                    }
                } else {
                    // Update remaining time
                    const status = await sessionService.getSessionStatus();
                    setSessionStatus(prev => ({
                        ...prev,
                        remainingTime: status.remainingTime
                    }));
                }
            }, 2 * 60 * 1000); // 2 minutes
        };

        startSessionMonitoring();

        return () => {
            if (sessionTimer.current) {
                clearInterval(sessionTimer.current);
            }
            if (activityTimer.current) {
                clearTimeout(activityTimer.current);
            }
        };
    }, [sessionStatus.isValid, sessionStatus.sessionId]);

    // Real-time countdown timer
    useEffect(() => {
        if (!sessionStatus.isValid || !sessionStatus.sessionId || !sessionStatus.remainingTime) {
            return;
        }

        const countdownTimer = setInterval(() => {
            setSessionStatus(prev => {
                if (prev.remainingTime && prev.remainingTime > 0) {
                    return {
                        ...prev,
                        remainingTime: prev.remainingTime - 1 // Subtract 1 second
                    };
                } else {
                    return {
                        ...prev,
                        isValid: false,
                        sessionId: null,
                        remainingTime: undefined,
                        error: 'Session expired. Please refresh the page.'
                    };
                }
            });
        }, 1000); // Update every second

        return () => clearInterval(countdownTimer);
    }, [sessionStatus.isValid, sessionStatus.sessionId, sessionStatus.remainingTime]);

    // Set up activity-based session extension
    useEffect(() => {
        const handleUserActivity = () => {
            if (!sessionStatus.isValid || !sessionStatus.sessionId) {
                return;
            }

            // Clear existing activity timer
            if (activityTimer.current) {
                clearTimeout(activityTimer.current);
            }

            // Extend session after 5 seconds of inactivity (only if session is valid)
            activityTimer.current = setTimeout(() => {
                if (sessionStatus.isValid && sessionStatus.sessionId) {
                    extendSession();
                }
            }, 5000);
        };

        // Add event listeners for user activity
        document.addEventListener('click', handleUserActivity);
        document.addEventListener('keypress', handleUserActivity);
        document.addEventListener('scroll', handleUserActivity);
        document.addEventListener('mousemove', handleUserActivity);

        return () => {
            document.removeEventListener('click', handleUserActivity);
            document.removeEventListener('keypress', handleUserActivity);
            document.removeEventListener('scroll', handleUserActivity);
            document.removeEventListener('mousemove', handleUserActivity);
        };
    }, [sessionStatus.isValid, sessionStatus.sessionId, extendSession]);

    // Initialize session on mount (only once)
    useEffect(() => {
        if (!sessionInitialized.current) {
            console.log('useEffect: Initializing session...');
            initializeSession();
        } else {
            console.log('useEffect: Session already initialized, skipping...');
        }
    }, []); // Empty dependency array - only run once on mount

    return {
        sessionStatus,
        extendSession,
        clearSession,
        createNewSession,
        initializeSession
    };
}
