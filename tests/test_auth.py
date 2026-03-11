import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.auth import create_refresh_token


@pytest.mark.asyncio
class TestRegister:
    async def test_register_success(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "Password1",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"
        assert "id" in data
        assert "hashed_password" not in data

    async def test_register_duplicate_email(
        self, client: AsyncClient, regular_user: User
    ) -> None:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": regular_user.email,
                "username": "another_username",
                "password": "Password1",
            },
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    async def test_register_duplicate_username(
        self, client: AsyncClient, regular_user: User
    ) -> None:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "unique@example.com",
                "username": regular_user.username,
                "password": "Password1",
            },
        )
        assert response.status_code == 400
        assert "Username already taken" in response.json()["detail"]

    async def test_register_weak_password(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "weak@example.com",
                "username": "weakuser",
                "password": "password",  # no uppercase, no digit
            },
        )
        assert response.status_code == 422

    async def test_register_invalid_email(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "username": "someuser",
                "password": "Password1",
            },
        )
        assert response.status_code == 422

    async def test_register_short_username(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "short@example.com",
                "username": "ab",
                "password": "Password1",
            },
        )
        assert response.status_code == 422


@pytest.mark.asyncio
class TestLogin:
    async def test_login_success(
        self, client: AsyncClient, regular_user: User
    ) -> None:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": regular_user.email, "password": "Password1"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(
        self, client: AsyncClient, regular_user: User
    ) -> None:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": regular_user.email, "password": "WrongPassword1"},
        )
        assert response.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "Password1"},
        )
        assert response.status_code == 401

    async def test_login_invalid_email_format(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "bad-email", "password": "Password1"},
        )
        assert response.status_code == 422


@pytest.mark.asyncio
class TestRefresh:
    async def test_refresh_success(
        self, client: AsyncClient, regular_user: User
    ) -> None:
        refresh_token = create_refresh_token(subject=str(regular_user.id))
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_refresh_invalid_token(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "this.is.invalid"},
        )
        assert response.status_code == 401

    async def test_refresh_with_access_token_fails(
        self, client: AsyncClient, user_token: str
    ) -> None:
        """Access tokens should NOT work as refresh tokens."""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": user_token},
        )
        assert response.status_code == 401
