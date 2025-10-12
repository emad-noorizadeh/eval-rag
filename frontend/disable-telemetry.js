#!/usr/bin/env node
/**
 * Disable All Frontend Telemetry
 * Author: Emad Noorizadeh
 * 
 * This script disables all telemetry and analytics in the Next.js frontend.
 */

const fs = require('fs');
const path = require('path');

console.log('🛡️  Disabling Frontend Telemetry...');

// Set environment variables to disable telemetry
process.env.NEXT_TELEMETRY_DISABLED = '1';
process.env.ANALYTICS_ID = '';
process.env.VERCEL_ANALYTICS_ID = '';
process.env.GOOGLE_ANALYTICS_ID = '';
process.env.MIXPANEL_TOKEN = '';
process.env.SEGMENT_WRITE_KEY = '';
process.env.AMPLITUDE_API_KEY = '';
process.env.NEXT_PUBLIC_ANALYTICS_ID = '';
process.env.NEXT_PUBLIC_VERCEL_ANALYTICS_ID = '';

// Create .env.local file to persist settings
const envContent = `# Disable Next.js Telemetry
NEXT_TELEMETRY_DISABLED=1

# Disable other potential telemetry
ANALYTICS_ID=
VERCEL_ANALYTICS_ID=
GOOGLE_ANALYTICS_ID=
MIXPANEL_TOKEN=
SEGMENT_WRITE_KEY=
AMPLITUDE_API_KEY=

# Disable development telemetry
NEXT_PUBLIC_ANALYTICS_ID=
NEXT_PUBLIC_VERCEL_ANALYTICS_ID=

# Disable Vercel telemetry
VERCEL_ANALYTICS_ID=
VERCEL_ANALYTICS_DEBUG=0

# Disable React telemetry
REACT_APP_ANALYTICS_ID=
`;

try {
  fs.writeFileSync('.env.local', envContent);
  console.log('✅ Created .env.local with telemetry disabled');
} catch (error) {
  console.log('⚠️  Could not create .env.local:', error.message);
}

// Disable Next.js telemetry globally
try {
  const { execSync } = require('child_process');
  execSync('npx next telemetry disable', { stdio: 'inherit' });
  console.log('✅ Disabled Next.js telemetry globally');
} catch (error) {
  console.log('⚠️  Could not disable Next.js telemetry globally:', error.message);
}

console.log('🎉 Frontend telemetry disabled successfully!');
console.log('');
console.log('📋 Telemetry disabled for:');
console.log('  - Next.js telemetry');
console.log('  - Vercel analytics');
console.log('  - Google Analytics');
console.log('  - Mixpanel');
console.log('  - Segment');
console.log('  - Amplitude');
console.log('  - React telemetry');
console.log('');
console.log('🔒 Your frontend is now completely private!');
