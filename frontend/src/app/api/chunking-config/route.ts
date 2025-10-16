/**
 * Chunking Configuration API Route
 * Author: Emad Noorizadeh
 */

import { NextRequest, NextResponse } from 'next/server';
import { API_BASE_URL } from '@/config/api';

const BACKEND_URL = API_BASE_URL;

export async function GET() {
    try {
        const response = await fetch(`${BACKEND_URL}/chunking-config`, {
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
        console.error('Error fetching chunking config:', error);
        return NextResponse.json(
            { error: 'Failed to fetch chunking configuration' },
            { status: 500 }
        );
    }
}
