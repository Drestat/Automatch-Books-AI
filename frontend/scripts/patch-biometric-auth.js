#!/usr/bin/env node
/**
 * Patch capacitor-biometric-auth to work with Capacitor 8.
 * The package imports `registerWebPlugin` which was removed in Capacitor 4+.
 * This script replaces that import with a no-op.
 */
const fs = require('fs');
const path = require('path');

const webJsPath = path.join(
    __dirname, '..', 'node_modules', 'capacitor-biometric-auth', 'dist', 'esm', 'web.js'
);

if (fs.existsSync(webJsPath)) {
    let content = fs.readFileSync(webJsPath, 'utf8');
    if (content.includes('registerWebPlugin')) {
        content = content
            .replace(
                "import { registerWebPlugin } from '@capacitor/core';",
                "// patched: registerWebPlugin removed in Capacitor 4+"
            )
            .replace(
                'registerWebPlugin(BiometricAuth);',
                '// patched: registerWebPlugin(BiometricAuth);'
            );
        fs.writeFileSync(webJsPath, content);
        console.log('✅ Patched capacitor-biometric-auth for Capacitor 8 compatibility');
    }
}
