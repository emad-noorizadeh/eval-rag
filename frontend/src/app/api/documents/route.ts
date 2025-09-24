/**
 * Documents API Route
 * Author: Emad Noorizadeh
 */

import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:9000';

export async function GET() {
    try {
        // Use the new metadata endpoint to get all document metadata
        const response = await fetch(`${BACKEND_URL}/documents/metadata`, {
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
        console.error('Error fetching documents metadata:', error);
        return NextResponse.json(
            { error: 'Failed to fetch documents metadata' },
            { status: 500 }
        );
    }
}
