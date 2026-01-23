from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.qbo import Transaction, Category
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

        # 2. Spend Trend (Daily)
        trend_data = self.db.query(
            func.date(Transaction.date).label('date'),
            func.sum(Transaction.amount).label('total')
        ).filter(
            Transaction.realm_id == self.realm_id,
            Transaction.date >= start_date,
            Transaction.amount < 0 # Spend only
        ).group_by(
            func.date(Transaction.date)
        ).order_by(
            func.date(Transaction.date)
        ).all()

        formatted_trend = [
            {"name": t.date.strftime("%b %d"), "value": float(abs(t.total))} 
            for t in trend_data
        ]

        # 3. Category Breakdown
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
            func.sum(Transaction.amount) # Most negative (biggest spend) first
        ).limit(5).all()

        formatted_cats = [
            {"name": c.suggested_category_name or "Uncategorized", "value": float(abs(c.total))}
            for c in cat_data
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
