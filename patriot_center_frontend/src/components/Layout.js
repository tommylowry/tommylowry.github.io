import React from 'react';
import { Link } from 'react-router-dom';
import SearchBar from './SearchBar';

export default function Layout({ children }) {
    return (
        <div style={{ position: 'relative', minHeight: '100vh' }}>
            {/* Header with Title and Search Bar */}
            <div style={{
                position: 'sticky',
                top: 0,
                zIndex: 100,
                backgroundColor: 'var(--bg)',
                borderBottom: '1px solid var(--border)',
                padding: '1rem 2rem',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                gap: '2rem'
            }}>
                {/* Centered Title */}
                <div style={{ flex: 1 }} />
                <Link
                    to="/?year=2025"
                    style={{
                        textDecoration: 'none',
                        color: 'var(--text)',
                        fontSize: '1.5rem',
                        fontWeight: 600,
                        whiteSpace: 'nowrap'
                    }}
                >
                    Patriot Center Database
                </Link>
                {/* Search Bar on Right */}
                <div style={{ flex: 1, display: 'flex', justifyContent: 'flex-end' }}>
                    <SearchBar />
                </div>
            </div>

            {/* Page Content - Add padding to prevent header from covering */}
            <div style={{ paddingTop: '1rem' }}>
                {children}
            </div>
        </div>
    );
}
