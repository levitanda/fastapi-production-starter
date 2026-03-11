import pytest
from httpx import AsyncClient

from app.models.user import User


@pytest.mark.asyncio
class TestGetMe:
    async def test_get_me_success(
        self, client: AsyncClient, regular_user: User, user_token: str
    ) -> None:
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == regular_user.email
        assert data["username"] == regular_user.username
        assert data["is_admin"] is False

    async def test_get_me_no_token(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/users/me")
        assert response.status_code == 401

    async def test_get_me_invalid_token(self, client: AsyncClient) -> None:
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert response.status_code == 401

    async def test_get_me_admin(
        self, client: AsyncClient, admin_user: User, admin_token: str
    ) -> None:
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_admin"] is True


@pytest.mark.asyncio
class TestListUsers:
    async def test_list_users_as_admin(
        self,
        client: AsyncClient,
        regular_user: User,
        admin_user: User,
        admin_token: str,
    ) -> None:
        response = await client.get(
            "/api/v1/users/",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2
        emails = [u["email"] for u in data]
        assert regular_user.email in emails
        assert admin_user.email in emails

    async def test_list_users_as_regular_user_forbidden(
        self, client: AsyncClient, user_token: str
    ) -> None:
        response = await client.get(
            "/api/v1/users/",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403

    async def test_list_users_unauthenticated(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/users/")
        assert response.status_code == 401

    async def test_list_users_pagination(
        self, client: AsyncClient, admin_token: str
    ) -> None:
        response = await client.get(
            "/api/v1/users/?skip=0&limit=1",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 1
