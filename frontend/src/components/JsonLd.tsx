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

export function BreadcrumbJsonLd({ items }: { items: { name: string; url: string }[] }) {
    const breadcrumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": items.map((item, index) => ({
            "@type": "ListItem",
            "position": index + 1,
            "name": item.name,
            "item": `${siteConfig.url}${item.url}`
        }))
    };

    return (
        <script
            type="application/ld+json"
            dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumb) }}
        />
    );
}

export function PricingJsonLd() {
    const pricing = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebPage",
                "@id": `${siteConfig.url}/pricing`,
                "url": `${siteConfig.url}/pricing`,
                "name": "Pricing | AutoMatch Books AI",
                "description": "Flexible pricing tiers for businesses of all sizes.",
                "isPartOf": { "@id": `${siteConfig.url}/#website` }
            },
            {
                "@type": "Product",
                "name": "AutoMatch Books AI - Business Plan",
                "description": "AI-powered QuickBooks transaction matching with unlimited accounts, auto-sync, and AI reasoning narratives.",
                "brand": { "@type": "Brand", "name": "AutoMatch Books AI" },
                "offers": [
                    {
                        "@type": "Offer",
                        "name": "Free",
                        "price": "0",
                        "priceCurrency": "USD",
                        "availability": "https://schema.org/InStock",
                        "description": "1 bank account, 25 AI tokens/month"
                    },
                    {
                        "@type": "Offer",
                        "name": "Personal",
                        "price": "2.99",
                        "priceCurrency": "USD",
                        "availability": "https://schema.org/InStock",
                        "priceSpecification": {
                            "@type": "UnitPriceSpecification",
                            "price": "2.99",
                            "priceCurrency": "USD",
                            "billingDuration": { "@type": "QuantitativeValue", "value": 1, "unitCode": "MON" }
                        },
                        "description": "2 bank accounts, 100 AI tokens/month"
                    },
                    {
                        "@type": "Offer",
                        "name": "Business",
                        "price": "8.99",
                        "priceCurrency": "USD",
                        "availability": "https://schema.org/InStock",
                        "priceSpecification": {
                            "@type": "UnitPriceSpecification",
                            "price": "8.99",
                            "priceCurrency": "USD",
                            "billingDuration": { "@type": "QuantitativeValue", "value": 1, "unitCode": "MON" }
                        },
                        "description": "Unlimited accounts, 300 AI tokens/month, auto-sync"
                    },
                    {
                        "@type": "Offer",
                        "name": "Corporate",
                        "price": "49.99",
                        "priceCurrency": "USD",
                        "availability": "https://schema.org/InStock",
                        "priceSpecification": {
                            "@type": "UnitPriceSpecification",
                            "price": "49.99",
                            "priceCurrency": "USD",
                            "billingDuration": { "@type": "QuantitativeValue", "value": 1, "unitCode": "MON" }
                        },
                        "description": "Everything in Business plus 700 AI tokens, multi-user, custom rules"
                    }
                ]
            },
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": "Is there a free trial?",
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": "Yes, AutoMatch Books AI offers a free tier with 1 connected bank account and 25 AI tokens per month. No credit card required."
                        }
                    },
                    {
                        "@type": "Question",
                        "name": "Can I cancel anytime?",
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": "Yes, all plans can be cancelled at any time with no hidden fees or penalties."
                        }
                    }
                ]
            }
        ]
    };

    return (
        <script
            type="application/ld+json"
            dangerouslySetInnerHTML={{ __html: JSON.stringify(pricing) }}
        />
    );
}

export function ContactJsonLd() {
    const contact = {
        "@context": "https://schema.org",
        "@type": "ContactPage",
        "@id": `${siteConfig.url}/contact`,
        "url": `${siteConfig.url}/contact`,
        "name": "Contact Us | AutoMatch Books AI",
        "description": "Get in touch with our team for support or inquiries about AI-powered bookkeeping.",
        "isPartOf": { "@id": `${siteConfig.url}/#website` },
        "mainEntity": {
            "@type": "Organization",
            "name": siteConfig.name,
            "email": "hello@automatchbooks.ai",
            "contactPoint": [
                {
                    "@type": "ContactPoint",
                    "contactType": "customer support",
                    "email": "support@automatchbooksai.com"
                },
                {
                    "@type": "ContactPoint",
                    "contactType": "sales",
                    "email": "hello@automatchbooks.ai"
                }
            ]
        }
    };

    return (
        <script
            type="application/ld+json"
            dangerouslySetInnerHTML={{ __html: JSON.stringify(contact) }}
        />
    );
}

export function FeaturesJsonLd() {
    const features = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "@id": `${siteConfig.url}/features`,
        "url": `${siteConfig.url}/features`,
        "name": "Features & Testing Guide | AutoMatch Books AI",
        "description": "Detailed breakdown of features, architecture vision, and A-Z testing instructions for AutoMatch Books AI.",
        "isPartOf": { "@id": `${siteConfig.url}/#website` },
        "about": {
            "@type": "SoftwareApplication",
            "@id": `${siteConfig.url}/#application`
        }
    };

    return (
        <script
            type="application/ld+json"
            dangerouslySetInnerHTML={{ __html: JSON.stringify(features) }}
        />
    );
}
