export { }

declare global {
    interface CustomJwtSessionClaims {
        metadata: {
            subscription_status?: 'active' | 'trialing' | 'inactive';
        };
    }
}
