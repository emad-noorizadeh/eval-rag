/**
 * HighlightedText Component for displaying text with supported terms and entities highlighted
 * Author: Emad Noorizadeh
 */

'use client';

import React from 'react';

interface HighlightedTextProps {
    text: string;
    supportedTerms?: Array<{
        term: string;
        start: number;
        end: number;
    }>;
    supportedEntities?: Array<{
        type: string;
        text: string;
        start: number;
        end: number;
    }>;
    className?: string;
}

interface HighlightSpan {
    text: string;
    start: number;
    end: number;
    type: 'term' | 'entity' | 'normal';
    entityType?: string;
}

export default function HighlightedText({
    text,
    supportedTerms = [],
    supportedEntities = [],
    className = ''
}: HighlightedTextProps) {
    // Create a list of all highlights with their positions
    const highlights: HighlightSpan[] = [];

    // Add supported terms (blue highlighting)
    supportedTerms.forEach(term => {
        highlights.push({
            text: text.substring(term.start, term.end),
            start: term.start,
            end: term.end,
            type: 'term'
        });
    });

    // Add supported entities (green highlighting)
    supportedEntities.forEach(entity => {
        highlights.push({
            text: entity.text,
            start: entity.start,
            end: entity.end,
            type: 'entity',
            entityType: entity.type
        });
    });

    // Sort highlights by start position
    highlights.sort((a, b) => a.start - b.start);

    // Remove overlapping highlights (prioritize entities over terms)
    const filteredHighlights: HighlightSpan[] = [];
    let lastEnd = 0;

    highlights.forEach(highlight => {
        if (highlight.start >= lastEnd) {
            filteredHighlights.push(highlight);
            lastEnd = highlight.end;
        } else if (highlight.type === 'entity' && highlight.start < lastEnd) {
            // Entity takes priority, remove the last highlight if it overlaps
            const lastIndex = filteredHighlights.length - 1;
            if (lastIndex >= 0 && filteredHighlights[lastIndex].type === 'term') {
                filteredHighlights.pop();
                filteredHighlights.push(highlight);
                lastEnd = highlight.end;
            }
        }
    });

    // Build the JSX with highlights
    const renderHighlightedText = () => {
        if (filteredHighlights.length === 0) {
            return <span className={className}>{text}</span>;
        }

        const elements: React.ReactNode[] = [];
        let lastIndex = 0;

        filteredHighlights.forEach((highlight, index) => {
            // Add normal text before highlight
            if (highlight.start > lastIndex) {
                elements.push(
                    <span key={`normal-${index}`} className={className}>
                        {text.substring(lastIndex, highlight.start)}
                    </span>
                );
            }

            // Add highlighted text
            const highlightClass = highlight.type === 'entity'
                ? 'bg-green-200 text-green-900 px-1 rounded font-medium'
                : 'bg-blue-200 text-blue-900 px-1 rounded font-medium';

            elements.push(
                <span
                    key={`highlight-${index}`}
                    className={`${highlightClass} ${className}`}
                    title={highlight.type === 'entity' ? `Entity: ${highlight.entityType}` : 'Supported term'}
                >
                    {highlight.text}
                </span>
            );

            lastIndex = highlight.end;
        });

        // Add remaining normal text
        if (lastIndex < text.length) {
            elements.push(
                <span key="normal-end" className={className}>
                    {text.substring(lastIndex)}
                </span>
            );
        }

        return <>{elements}</>;
    };

    return (
        <div className="whitespace-pre-wrap text-left">
            {renderHighlightedText()}
        </div>
    );
}
