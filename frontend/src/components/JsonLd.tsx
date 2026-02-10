import { siteConfig } from "@/config/site";

export function JsonLd() {
    const jsonLd = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebSite",
                "@id": `${siteConfig.url}/#website`,
                "url": siteConfig.url,
                "name": siteConfig.name,
                "description": siteConfig.description,
                "publisher": { "@id": `${siteConfig.url}/#organization` },
                "inLanguage": "en-US"
            },
            {
                "@type": "Organization",
                "@id": `${siteConfig.url}/#organization`,
                "name": siteConfig.name,
                "url": siteConfig.url,
                "logo": {
                    "@type": "ImageObject",
                    "url": `${siteConfig.url}/logo.png`,
                    "width": 512,
                    "height": 512
                },
                "sameAs": [siteConfig.links.twitter]
            },
            {
                "@type": "SoftwareApplication",
                "@id": `${siteConfig.url}/#application`,
                "name": siteConfig.name,
                "operatingSystem": "Cloud-based (Web)",
                "applicationCategory": "FinanceApplication",
                "description": "AI-powered transaction matching for QuickBooks Online. Automate bookkeeping with 99% accuracy using Gemini 3 Flash.",
                "publisher": { "@id": `${siteConfig.url}/#organization` },
                "offers": {
                    "@type": "Offer",
                    "price": "0",
                    "priceCurrency": "USD",
                    "availability": "https://schema.org/InStock"
                },
                "aggregateRating": {
                    "@type": "AggregateRating",
                    "ratingValue": "4.9",
                    "ratingCount": "120"
                }
            }
        ]
    };

    return (
        <script
            type="application/ld+json"
            dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
    );
}
