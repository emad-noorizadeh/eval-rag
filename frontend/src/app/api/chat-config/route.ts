/**
 * Chat Configuration API Route
 * Author: Emad Noorizadeh
 */

import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:9000';

export async function GET() {
    try {
        const response = await fetch(`${BACKEND_URL}/chat-config`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        if (!response.ok) {
            throw new Error(`Backend responded with status: ${response.status}`);
        }

        const data = await response.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error('Error fetching chat config:', error);
        return NextResponse.json(
            { error: 'Failed to fetch chat configuration' },
            { status: 500 }
        );
    }
}
