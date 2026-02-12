from sqlalchemy.orm import Session
from sqlalchemy import func, case
from app.models.qbo import Transaction, Category, SyncLog, QBOConnection, BankAccount
from app.models.user import User
from datetime import datetime, timedelta

class AnalyticsService:
    def __init__(self, db: Session, realm_id: str):
        self.db = db
        self.realm_id = realm_id

    def get_dashboard_stats(self):
        """Aggregates all analytics data for the dashboard"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        # Base query for last 30 days
        base_query = self.db.query(Transaction).filter(
            Transaction.realm_id == self.realm_id,
            Transaction.date >= start_date
        )

        # 1. KPI Totals
        transactions = base_query.all()
        total_spend = sum(abs(t.amount) for t in transactions if t.amount < 0)
        total_income = sum(t.amount for t in transactions if t.amount > 0)
        net_flow = total_income - total_spend

        # 2. Dual Stream Trend (Income & Expense)
        # We'll create a dictionary mapping dates to {income, expense}
        trend_map = {}
        
        # Populate dates for the last 30 days to ensure no gaps
        for i in range(31):
            date_str = (start_date + timedelta(days=i)).strftime("%b %d")
            trend_map[date_str] = {"income": 0.0, "expense": 0.0}

        # Query Trend Data
        daily_stats = self.db.query(
            func.date(Transaction.date).label('date'),
            func.sum(func.case((Transaction.amount > 0, Transaction.amount), else_=0)).label('income'),
            func.sum(func.case((Transaction.amount < 0, func.abs(Transaction.amount)), else_=0)).label('expense')
        ).filter(
            Transaction.realm_id == self.realm_id,
            Transaction.date >= start_date
        ).group_by(
            func.date(Transaction.date)
        ).all()

        for stat in daily_stats:
            date_str = stat.date.strftime("%b %d")
            if date_str in trend_map:
                trend_map[date_str]["income"] = float(stat.income)
                trend_map[date_str]["expense"] = float(stat.expense)

        formatted_trend = [
            {"name": date, "income": data["income"], "expense": data["expense"]}
            for date, data in trend_map.items()
        ]

        # 3. Detailed Category Breakdown (Expenses Only)
        cat_data = self.db.query(
            Transaction.suggested_category_name,
            func.sum(Transaction.amount).label('total')
        ).filter(
            Transaction.realm_id == self.realm_id,
            Transaction.date >= start_date,
            Transaction.amount < 0
        ).group_by(
            Transaction.suggested_category_name
        ).order_by(
            func.sum(Transaction.amount) # Most negative first
        ).limit(5).all()

        formatted_cats = [
            {
                "name": c.suggested_category_name or "Uncategorized", 
                "value": float(abs(c.total)),
                "isTop": i == 0
            }
            for i, c in enumerate(cat_data)
        ]

        return {
            "kpi": {
                "totalSpend": float(total_spend),
                "totalIncome": float(total_income),
                "netFlow": float(net_flow)
            },
            "trend": formatted_trend,
            "categories": formatted_cats
        }

    def get_all_user_usage(self):
        """Admin: Aggregates usage stats for all realms + Business Intelligence"""
        
        # 1. User & Subscription Stats
        users = self.db.query(User).all()
        
        tier_pricing = {
            "free": 0,
            "free_user": 0,
            "personal": 2.99,
            "business": 8.99,
            "corporate": 49.99,
            "starter": 2.99, # Legacy
            "pro": 2.99, # Legacy
            "founder": 29.99, # Legacy
            "empire": 99.99 # Legacy
        }
        
        mrr = 0.0
        tier_counts = {}
        
        for u in users:
            # MRR
            price = tier_pricing.get(u.subscription_tier, 0)
            mrr += price
            
            # Tiers
            tier = u.subscription_tier or "free"
            tier_counts[tier] = tier_counts.get(tier, 0) + 1

        # 2. Global Volume (Total Transaction Value Processed)
        # We sum absolute value of all transactions to show "Activity Volume"
        total_vol_query = self.db.query(func.sum(func.abs(Transaction.amount))).scalar()
        total_volume = float(total_vol_query) if total_vol_query else 0.0

        # 3. Location Proxy (via Currency)
        # Group BankAccounts by Currency to guess region
        currency_stats = self.db.query(
            BankAccount.currency,
            func.count(BankAccount.id)
        ).group_by(BankAccount.currency).all()
        
        location_data = []
        for curr, count in currency_stats:
            if not curr: continue
            region = "Global"
            if curr == "USD": region = "United States"
            elif curr == "CAD": region = "Canada"
            elif curr == "GBP": region = "United Kingdom"
            elif curr == "EUR": region = "Europe"
            elif curr == "AUD": region = "Australia"
            elif curr == "INR": region = "India"
            
            location_data.append({"currency": curr, "region": region, "count": count})

        # 4. User Leaderboard Data (Existing logic)
        tx_stats = self.db.query(
            Transaction.realm_id,
            func.count(Transaction.id).label('tx_count')
        ).group_by(Transaction.realm_id).subquery()

        sync_stats = self.db.query(
            SyncLog.realm_id,
            func.count(case((SyncLog.operation == 'sync', 1))).label('total_syncs'),
            func.sum(SyncLog.count).label('total_items')
        ).group_by(SyncLog.realm_id).subquery()

        results = self.db.query(
            QBOConnection.realm_id,
            QBOConnection.updated_at,
            func.coalesce(sync_stats.c.total_syncs, 0).label('syncs'),
            func.coalesce(sync_stats.c.total_items, 0).label('items'),
            func.coalesce(tx_stats.c.tx_count, 0).label('transactions'),
            User.email, 
            User.subscription_tier
        ).outerjoin(
            sync_stats, QBOConnection.realm_id == sync_stats.c.realm_id
        ).outerjoin(
            tx_stats, QBOConnection.realm_id == tx_stats.c.realm_id
        ).outerjoin(
            User, QBOConnection.user_id == User.id
        ).all()

        leaderboard = [
            {
                "realmId": row.realm_id,
                "email": row.email, # Admin only
                "tier": row.subscription_tier,
                "lastActive": row.updated_at.isoformat() if row.updated_at else None,
                "totalSyncs": int(row.syncs),
                "totalItems": int(row.items),
                "totalTransactions": int(row.transactions)
            }
            for row in results
        ]
        
        return {
            "kpi": {
                "mrr": mrr,
                "totalVolume": total_volume,
                "activeUsers": len(users),
                "avgRevenuePerUser": mrr / len(users) if users else 0
            },
            "distributions": {
                "tiers": [{"name": k, "value": v} for k, v in tier_counts.items()],
                "locations": location_data
            },
            "leaderboard": leaderboard
        }
