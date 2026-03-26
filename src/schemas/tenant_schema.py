"""
Tenant schemas for tenant profile responses.
"""

from __future__ import annotations

from pydantic import BaseModel

from models.models import Tenant


class TenantResponse(BaseModel):
    id: int
    name: str
    created_at: str

    @classmethod
    def from_tenant(cls, tenant: Tenant) -> "TenantResponse":
        return cls(
            id=tenant.id,
            name=tenant.name,
            created_at=tenant.created_at.isoformat(),
        )
