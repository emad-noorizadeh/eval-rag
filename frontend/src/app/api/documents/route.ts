/**
 * Documents API Route
 * Author: Emad Noorizadeh
 */

import { NextRequest, NextResponse } from 'next/server';
import { API_BASE_URL } from '@/config/api';

const BACKEND_URL = API_BASE_URL;

export async function GET() {
    try {
        const [collectionResponse, metadataResponse] = await Promise.all([
            fetch(`${BACKEND_URL}/collection/info`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            }),
            fetch(`${BACKEND_URL}/documents/metadata`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            })
        ]);

        if (!collectionResponse.ok) {
            throw new Error(`Collection info request failed with status: ${collectionResponse.status}`);
        }

        if (!metadataResponse.ok) {
            throw new Error(`Documents metadata request failed with status: ${metadataResponse.status}`);
        }

        const collection = await collectionResponse.json();
        const metadata = await metadataResponse.json();

        return NextResponse.json({
            collection,
            metadata,
        });
    } catch (error) {
        console.error('Error fetching documents metadata:', error);
        return NextResponse.json(
            { error: 'Failed to fetch documents metadata' },
            { status: 500 }
        );
    }
}
