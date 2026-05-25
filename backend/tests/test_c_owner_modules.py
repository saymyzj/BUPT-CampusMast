from __future__ import annotations


def login(client, email: str, password: str) -> dict:
    response = client.post("/api/auth/login", json={"studentEmail": email, "password": password})
    assert response.status_code == 200
    return response.json()["data"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_auth_register_login_refresh_and_profile_update(client) -> None:
    register_payload = {
        "studentEmail": "new.user@bupt.edu.cn",
        "password": "Password123",
        "nickname": "新同学",
    }
    register_response = client.post("/api/auth/register", json=register_payload)
    assert register_response.status_code == 201
    access_token = register_response.json()["data"]["accessToken"]

    me_response = client.get("/api/auth/me", headers=auth_headers(access_token))
    assert me_response.status_code == 200
    assert me_response.json()["data"]["studentEmail"] == "new.user@bupt.edu.cn"

    update_response = client.put(
        "/api/auth/me",
        headers=auth_headers(access_token),
        json={"nickname": "新昵称", "defaultBuildingCode": "BUPT_LIBRARY"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["nickname"] == "新昵称"

    login_response = client.post(
        "/api/auth/login",
        json={"studentEmail": "new.user@bupt.edu.cn", "password": "Password123"},
    )
    assert login_response.status_code == 200
    refresh_token = login_response.json()["data"]["refreshToken"]

    refresh_response = client.post("/api/auth/refresh", json={"refreshToken": refresh_token})
    assert refresh_response.status_code == 200
    assert refresh_response.json()["data"]["accessToken"]

    anonymous_password_response = client.put(
        "/api/auth/me/password",
        json={"currentPassword": "Password123", "newPassword": "NewPassword123"},
    )
    assert anonymous_password_response.status_code == 401

    wrong_password_response = client.put(
        "/api/auth/me/password",
        headers=auth_headers(access_token),
        json={"currentPassword": "wrong-password", "newPassword": "NewPassword123"},
    )
    assert wrong_password_response.status_code == 400

    change_password_response = client.put(
        "/api/auth/me/password",
        headers=auth_headers(access_token),
        json={"currentPassword": "Password123", "newPassword": "NewPassword123"},
    )
    assert change_password_response.status_code == 200

    old_password_login_response = client.post(
        "/api/auth/login",
        json={"studentEmail": "new.user@bupt.edu.cn", "password": "Password123"},
    )
    assert old_password_login_response.status_code == 401

    new_password_login_response = client.post(
        "/api/auth/login",
        json={"studentEmail": "new.user@bupt.edu.cn", "password": "NewPassword123"},
    )
    assert new_password_login_response.status_code == 200


def test_upload_notification_map_and_moderation_flows(client) -> None:
    auth = login(client, "demo.user@bupt.edu.cn", "Demo123456")
    token = auth["accessToken"]

    upload_response = client.post(
        "/api/upload/images",
        headers=auth_headers(token),
        files={"file": ("avatar.png", b"fake-image", "image/png")},
    )
    assert upload_response.status_code == 201
    assert upload_response.json()["data"]["fileKey"].startswith("uploads/")
    assert "/uploads/" in upload_response.json()["data"]["fileUrl"]

    notifications_response = client.get("/api/notifications", headers=auth_headers(token))
    assert notifications_response.status_code == 200
    notifications = notifications_response.json()["data"]
    assert len(notifications) >= 1

    first_notification_id = notifications[0]["id"]
    mark_response = client.patch(f"/api/notifications/{first_notification_id}/read", headers=auth_headers(token))
    assert mark_response.status_code == 200
    assert mark_response.json()["data"]["isRead"] is True

    read_all_response = client.patch("/api/notifications/read-all", headers=auth_headers(token))
    assert read_all_response.status_code == 200
    assert read_all_response.json()["data"]["updatedCount"] >= 0

    buildings_response = client.get("/api/map/buildings", headers=auth_headers(token))
    assert buildings_response.status_code == 200
    assert buildings_response.json()["data"][0]["latitude"]

    selected_location_response = client.get(
        "/api/map/current-location?latitude=39.9601&longitude=116.3501",
        headers=auth_headers(token),
    )
    assert selected_location_response.status_code == 200
    assert selected_location_response.json()["data"]["source"] == "SELECTED_POINT"

    nearby_response = client.get("/api/map/tasks/nearby?buildingCode=BUPT_MAIN", headers=auth_headers(token))
    assert nearby_response.status_code == 200
    assert nearby_response.json()["data"][0]["distanceScore"] >= 0

    moderation_response = client.get("/api/moderation/my-records", headers=auth_headers(token))
    assert moderation_response.status_code == 200


def test_admin_chat_and_websocket_flows(client) -> None:
    admin_auth = login(client, "admin@bupt.edu.cn", "Admin123456")
    demo_auth = login(client, "demo.user@bupt.edu.cn", "Demo123456")

    admin_headers = auth_headers(admin_auth["accessToken"])
    demo_headers = auth_headers(demo_auth["accessToken"])

    users_response = client.get("/api/admin/users", headers=admin_headers)
    assert users_response.status_code == 200
    assert users_response.json()["meta"]["total"] >= 2

    tasks_response = client.get("/api/admin/tasks", headers=admin_headers)
    assert tasks_response.status_code == 200
    assert tasks_response.json()["meta"]["total"] >= 1

    moderation_admin_response = client.get("/api/admin/moderation/records", headers=admin_headers)
    assert moderation_admin_response.status_code == 200
    record_id = moderation_admin_response.json()["data"][0]["id"]

    review_response = client.patch(
        f"/api/admin/moderation/records/{record_id}/review",
        headers=admin_headers,
        json={"decision": "approve", "note": "通过演示复审"},
    )
    assert review_response.status_code == 200
    assert review_response.json()["data"]["adminReviewStatus"] == "APPROVED"

    config_response = client.get("/api/admin/configs", headers=admin_headers)
    assert config_response.status_code == 200
    config_key = config_response.json()["data"][0]["configKey"]
    update_config_response = client.put(
        f"/api/admin/configs/{config_key}",
        headers=admin_headers,
        json={"configValue": {"value": 66}},
    )
    assert update_config_response.status_code == 200
    assert update_config_response.json()["data"]["configValue"]["value"] == 66

    homepage_blocks_response = client.get("/api/admin/homepage/blocks", headers=admin_headers)
    assert homepage_blocks_response.status_code == 200
    block_id = homepage_blocks_response.json()["data"][0]["id"]
    update_block_response = client.put(
        f"/api/admin/homepage/blocks/{block_id}",
        headers=admin_headers,
        json={
            "blockType": "ANNOUNCEMENT",
            "title": "更新后的公告",
            "content": {"text": "欢迎来到演示环境"},
            "sortOrder": 1,
            "isActive": True,
        },
    )
    assert update_block_response.status_code == 200
    assert update_block_response.json()["data"]["title"] == "更新后的公告"

    stats_response = client.get("/api/admin/stats", headers=admin_headers)
    assert stats_response.status_code == 200
    assert stats_response.json()["data"]["userCount"] >= 2

    conversations_response = client.get("/api/chat/conversations", headers=demo_headers)
    assert conversations_response.status_code == 200
    task_id = conversations_response.json()["data"][0]["taskId"]
    conversation_id = conversations_response.json()["data"][0]["id"]

    with client.websocket_connect(f"/ws/chat:{task_id}?accessToken={demo_auth['accessToken']}") as websocket:
        connected = websocket.receive_json()
        assert connected["event"] == "SYSTEM_NOTICE"

        send_message_response = client.post(
            f"/api/chat/tasks/{task_id}/messages",
            headers=admin_headers,
            json={"content": "请问现在方便取件吗？", "clientMessageId": "client-1"},
        )
        assert send_message_response.status_code == 201
        pushed = websocket.receive_json()
        assert pushed["event"] == "CHAT_MESSAGE"
        assert pushed["payload"]["content"] == "请问现在方便取件吗？"

    messages_response = client.get(f"/api/chat/tasks/{task_id}/messages", headers=demo_headers)
    assert messages_response.status_code == 200
    assert len(messages_response.json()["data"]) >= 2

    read_response = client.patch(
        f"/api/chat/conversations/{conversation_id}/read",
        headers=demo_headers,
        json={"lastReadMessageId": messages_response.json()["data"][-1]["id"]},
    )
    assert read_response.status_code == 200
    assert read_response.json()["data"]["conversationId"] == conversation_id
