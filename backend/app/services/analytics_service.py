from sqlalchemy.orm import Session
from sqlalchemy import func, case
from app.models.qbo import Transaction, Category, SyncLog, QBOConnection
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
        """Admin: Aggregates usage stats for all realms"""
        # 1. Get transaction counts per realm
        tx_stats = self.db.query(
            Transaction.realm_id,
            func.count(Transaction.id).label('tx_count')
        ).group_by(Transaction.realm_id).subquery()

        # 2. Aggregated Sync Logs
        sync_stats = self.db.query(
            SyncLog.realm_id,
            func.count(case((SyncLog.operation == 'sync', 1))).label('total_syncs'),
            func.sum(SyncLog.count).label('total_items')
        ).group_by(SyncLog.realm_id).subquery()

        # 3. Join with Connections to get names/dates
        results = self.db.query(
            QBOConnection.realm_id,
            QBOConnection.updated_at,
            func.coalesce(sync_stats.c.total_syncs, 0).label('syncs'),
            func.coalesce(sync_stats.c.total_items, 0).label('items'),
            func.coalesce(tx_stats.c.tx_count, 0).label('transactions')
        ).outerjoin(
            sync_stats, QBOConnection.realm_id == sync_stats.c.realm_id
        ).outerjoin(
            tx_stats, QBOConnection.realm_id == tx_stats.c.realm_id
        ).all()

        return [
            {
                "realmId": row.realm_id,
                "lastActive": row.updated_at.isoformat() if row.updated_at else None,
                "totalSyncs": int(row.syncs),
                "totalItems": int(row.items),
                "totalTransactions": int(row.transactions)
            }
            for row in results
        ]
