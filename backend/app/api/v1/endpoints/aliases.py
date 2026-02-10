from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID

from app.api.v1.endpoints.qbo import get_db
from app.api.deps import verify_subscription
from app.models.qbo import VendorAlias, QBOConnection, Vendor

router = APIRouter()

class AliasBase(BaseModel):
    alias: str
    vendor_id: str

class AliasCreate(AliasBase):
    pass

class AliasSchema(AliasBase):
    id: UUID
    realm_id: str
    vendor_name: Optional[str] = None

    class Config:
        from_attributes = True

@router.get("/", response_model=List[AliasSchema])
def get_aliases(
    realm_id: str,
    db: Session = Depends(get_db),
    user=Depends(verify_subscription)
):
    aliases = db.query(VendorAlias).filter(
        VendorAlias.realm_id == realm_id
    ).all()
    
    # Enrich with vendor names if needed, or simple list
    results = []
    for a in aliases:
        vendor = db.query(Vendor).filter(Vendor.id == a.vendor_id).first()
        results.append(AliasSchema(
            id=a.id,
            realm_id=a.realm_id,
            alias=a.alias,
            vendor_id=a.vendor_id,
            vendor_name=vendor.display_name if vendor else "Unknown Vendor"
        ))
    
    return results

@router.post("/", response_model=AliasSchema)
def create_alias(
    realm_id: str,
    alias_in: AliasCreate,
    db: Session = Depends(get_db),
    user=Depends(verify_subscription)
):
    # Verify connection exists
    connection = db.query(QBOConnection).filter(QBOConnection.realm_id == realm_id).first()
    if not connection:
        raise HTTPException(status_code=404, detail="QBO Connection not found")
        
    # Verify vendor exists
    vendor = db.query(Vendor).filter(Vendor.id == alias_in.vendor_id, Vendor.realm_id == realm_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail=f"Vendor {alias_in.vendor_id} not found in this realm")

    alias = VendorAlias(
        realm_id=realm_id,
        alias=alias_in.alias,
        vendor_id=alias_in.vendor_id
    )
    db.add(alias)
    db.commit()
    db.refresh(alias)
    
    return AliasSchema(
        id=alias.id,
        realm_id=alias.realm_id,
        alias=alias.alias,
        vendor_id=alias.vendor_id,
        vendor_name=vendor.display_name
    )

@router.delete("/{alias_id}")
def delete_alias(
    realm_id: str,
    alias_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(verify_subscription)
):
    alias = db.query(VendorAlias).filter(
        VendorAlias.id == alias_id,
        VendorAlias.realm_id == realm_id
    ).first()
    
    if not alias:
        raise HTTPException(status_code=404, detail="Alias not found")
        
    db.delete(alias)
    db.commit()
    return {"status": "success", "message": "Alias deleted"}
