"""Orgs resource — organization, user, and team management."""

from __future__ import annotations

from typing import Any

from vibops.resources import Resource

__all__ = ["OrgsResource"]


class OrgsResource(Resource):
    """Organization operations."""

    async def get(self, org_id: str) -> dict[str, Any]:
        """Get organization details."""
        return await self._get(f"orgs/{org_id}")

    async def update(
        self,
        org_id: str,
        *,
        name: str | None = None,
        contact_email: str | None = None,
    ) -> dict[str, Any]:
        """Update organization details."""
        body: dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if contact_email is not None:
            body["contact_email"] = contact_email
        return await self._patch(f"orgs/{org_id}", json=body)

    async def users(self, org_id: str) -> list[dict[str, Any]]:
        """List users in an organization."""
        return await self._get(f"orgs/{org_id}/users")

    async def teams(self, org_id: str) -> list[dict[str, Any]]:
        """List teams in an organization."""
        return await self._get(f"orgs/{org_id}/teams")

    async def create_user(
        self,
        org_id: str,
        username: str,
        password: str,
        *,
        email: str | None = None,
        is_org_admin: bool = False,
    ) -> dict[str, Any]:
        """Create a new user in an organization."""
        body: dict[str, Any] = {
            "username": username,
            "password": password,
            "is_org_admin": is_org_admin,
        }
        if email is not None:
            body["email"] = email
        return await self._post(f"orgs/{org_id}/users", json=body)

    async def create_team(self, org_id: str, name: str) -> dict[str, Any]:
        """Create a new team in an organization."""
        return await self._post(f"orgs/{org_id}/teams", json={"name": name})

    async def invite(
        self,
        org_id: str,
        email: str,
        *,
        is_org_admin: bool = False,
    ) -> dict[str, Any]:
        """Invite a user to an organization."""
        return await self._post(
            f"orgs/{org_id}/invites",
            json={"email": email, "is_org_admin": is_org_admin},
        )
