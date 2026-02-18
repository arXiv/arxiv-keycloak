from typing import Optional

class MockKCConnection:
    def __init__(self, realm_name: str):
        self.realm_name = realm_name
        self.headers = {"redirect": ""}
        self.server_url = "http://localhost:8080/auth"

    # kc_admin.connection.raw_post(f"admin/realms/{kc_admin.connection.user_realm_name}/users/{user_id}/impersonation", {})  # type: ignore
    def raw_post(self, url: str, payload: dict) -> dict:
        return {"headers": {"redirect": "http://localhost:8000/login"}}

    #     impersonation_url = impersonation_response.headers.get("redirect")

class MockKeycloakAdmin:
    def __init__(self):
        self.connection = MockKCConnection("arxiv")
        pass

    def get_user(self, user_id: str, user_profile_metadata: bool = False) -> dict:
        return {"username": user_id, "emailVerified": True}

    #            "realmRoles": kc_admin.get_realm_roles_of_user(user_id),
    def get_realm_roles_of_user(self, user_id: str) -> list[str]:
        return ["Public"]

    def create_user(self, payload: dict, exist_ok: bool = False) -> None:
        return None

    def get_credentials(self, user_id: str) -> dict:
        return {}

    #    kc_admin.update_user(user_id=str(tapir_user.user_id), payload=changes)
    def update_user(self, user_id: str, payload: dict) -> None:
        return None

    #kc_user_id = kc_admin.get_user_id(nick.nickname)
    def get_user_id(self, username: str) -> Optional[str]:
        return None

    # kc_admin.user_logout(kc_user_id)
    def user_logout(self, user_id: str) -> None:
        return None

    #     kc_admin.set_user_password(kc_user["id"], data.new_password, temporary=False)
    def set_user_password(self, user_id: str, password: str, temporary: bool = False) -> None:
        return None

    #        kc_admin.send_update_account(user_id=str(user_id), payload={"requiredActions": ["UPDATE_PASSWORD"]})
    def send_update_account(self, user_id: str, payload: dict) -> None:
        return None


    # admin_role = kc_admin.get_realm_role("Administrator")
    def get_realm_role(self, role_name: str) -> dict:
        return {"name": role_name}

    #    kc_admin.assign_realm_roles(user_id, [admin_role])
    def assign_realm_roles(self, user_id: str, roles: list[dict]) -> None:
        return None

    # kc_admin.delete_realm_roles_of_user(user_id, [admin_role])
    def delete_realm_roles_of_user(self, user_id: str, roles: list[dict]) -> None:
        return None

    #kc_admin.delete_credential(user_id=str(user_id), credential_id=credential_id)
    def delete_credential(self, user_id: str, credential_id: str) -> None:
        return None

    # kc_admin.send_verify_email(account_id)
    def send_verify_email(self, user_id: str) -> None:
        return None

    #         kc_admin.create_user({
    #             "id": user.id,
    #             "username": user.username,
    #             "firstName": user.firstName,
    #             "lastName": user.lastName,
    #             "email": user.email,
    #             "emailVerified": user.emailVerified,
    #             "enabled": True,
    #             "credentials": [],
    #             "realmRoles": user.roles,
    #             "groups": user.groups,
    #             "attributes": user.attributes  # To have the attributes, make sure the unmanaged user profile is enabled
    #         }, exist_ok=exist_ok)
