from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID

from app.api.v1.endpoints.qbo import get_db
from app.api.deps import verify_subscription
from app.models.qbo import ClassificationRule, QBOConnection

router = APIRouter()

class RuleBase(BaseModel):
    name: str
    priority: int = 0
    conditions: dict
    action: dict

class RuleCreate(RuleBase):
    pass

class RuleSchema(RuleBase):
    id: UUID
    realm_id: str

    class Config:
        from_attributes = True

@router.get("/", response_model=List[RuleSchema])
def get_rules(
    realm_id: str,
    db: Session = Depends(get_db),
    user=Depends(verify_subscription)
):
    rules = db.query(ClassificationRule).filter(
        ClassificationRule.realm_id == realm_id
    ).order_by(ClassificationRule.priority.desc()).all()
    return rules

@router.post("/", response_model=RuleSchema)
def create_rule(
    realm_id: str,
    rule_in: RuleCreate,
    db: Session = Depends(get_db),
    user=Depends(verify_subscription)
):
    # Verify connection exists
    connection = db.query(QBOConnection).filter(QBOConnection.realm_id == realm_id).first()
    if not connection:
        raise HTTPException(status_code=404, detail="QBO Connection not found")
        
    rule = ClassificationRule(
        realm_id=realm_id,
        name=rule_in.name,
        priority=rule_in.priority,
        conditions=rule_in.conditions,
        action=rule_in.action
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule

@router.delete("/{rule_id}")
def delete_rule(
    realm_id: str,
    rule_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(verify_subscription)
):
    rule = db.query(ClassificationRule).filter(
        ClassificationRule.id == rule_id,
        ClassificationRule.realm_id == realm_id
    ).first()
    
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
        
    db.delete(rule)
    db.commit()
    return {"status": "success", "message": "Rule deleted"}
