---
description: Custom Vercel Deployment for Monorepo (Frontend Subdirectory)
---

# Vercel Deployment Strategy

To deploy this project to Vercel, where the Next.js application lives in the `frontend/` subdirectory, we use a "Project Hoisting" strategy designated in `vercel.json`.

**Problem:** Vercel expects `package.json` and the `.next` build output to be in the root directory. Using `distDir` changes caused runtime errors, and symlinking `node_modules` was unreliable.

**Solution:** 
We hoist the entire frontend application to the root directory during the build process.

## Configuration (`vercel.json`)

```json
{
    "version": 2,
    "installCommand": "cp -R frontend/. . && npm install",
    "buildCommand": "npm run build",
    "framework": "nextjs"
}
```

### Explanation
1. **Host Frontend**: `cp -R frontend/. .` copies all files (code, config, assets) from the subdirectory to the root.
2. **Install**: `npm install` runs in the root, installing dependencies exactly where Vercel's runtime looks for them.
3. **Build**: `npm run build` runs the standard Next.js build in the root.

This ensures zero configuration drift between "Development" (subdirectory) and "Production" (root) in Vercel's eyes.
