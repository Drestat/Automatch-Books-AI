// AutoMatch Books AI — Background Sync Runner
// Runs periodically in the background to check for new transactions

addEventListener('syncTransactions', async (resolve, reject, args) => {
    try {
        // Ping the backend to trigger a lightweight check
        const response = await fetch(
            'https://ifvckinglovef1--qbo-sync-engine-fastapi-app.modal.run/api/v1/health'
        );

        if (response.ok) {
            // Could store last sync time
            resolve();
        } else {
            reject('Backend health check failed');
        }
    } catch (err) {
        reject(err.message || 'Background sync failed');
    }
});
