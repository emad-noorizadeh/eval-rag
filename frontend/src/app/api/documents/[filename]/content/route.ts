/**
 * Document Content API Route
 * Author: Emad Noorizadeh
 */

import { NextRequest, NextResponse } from 'next/server';
import { API_BASE_URL } from '@/config/api';

const BACKEND_URL = API_BASE_URL;

export async function GET(
    request: NextRequest,
    { params }: { params: { filename: string } }
) {
    try {
        const { filename } = params;

        const response = await fetch(`${BACKEND_URL}/documents/${filename}/content`, {
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
        console.error('Error fetching document content:', error);
        return NextResponse.json(
            { error: 'Failed to fetch document content' },
            { status: 500 }
        );
    }
}
