
import os
import unittest

# 실제 DB가 아니라 테스트용 메모리 DB 사용
# app 모듈을 import하기 전에 설정해야 합니다.
os.environ["TODO_DATABASE_URI"] = "sqlite:///:memory:"

import app as todo_app


class TodoApiTest(unittest.TestCase):

    def setUp(self):
        # 각 테스트마다 독립된 초기 상태 사용
        self.ctx = todo_app.app.app_context()
        self.ctx.push()

        todo_app.db.drop_all()
        todo_app.db.create_all()

        self.client = todo_app.app.test_client()

    def tearDown(self):
        todo_app.db.session.remove()
        self.ctx.pop()

    # 1. POST: note를 포함해 새 할 일을 만들 수 있는가?
    def test_create_with_note(self):
        response = self.client.post(
            "/api/todos/",
            json={
                "text": "우유 사기",
                "note": "2리터짜리로"
            }
        )

        self.assertEqual(response.status_code, 201)

        data = response.get_json()

        self.assertEqual(data["text"], "우유 사기")
        self.assertEqual(data["note"], "2리터짜리로")
        self.assertFalse(data["done"])
        self.assertIn("id", data)

        self.assertEqual(
            response.headers["Location"],
            f"/api/todos/{data['id']}"
        )

    # 2. POST: note를 생략하면 빈 문자열인가?
    def test_create_without_note(self):
        response = self.client.post(
            "/api/todos/",
            json={"text": "책 반납"}
        )

        self.assertEqual(response.status_code, 201)

        data = response.get_json()

        self.assertEqual(data["text"], "책 반납")
        self.assertEqual(data["note"], "")

    # 3. GET: 필터를 주지 않으면 전체 목록인가?
    def test_list_without_filter(self):
        self.client.post(
            "/api/todos/",
            json={"text": "우유 사기", "done": True}
        )

        self.client.post(
            "/api/todos/",
            json={"text": "책 반납", "done": False}
        )

        response = self.client.get("/api/todos/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.get_json()), 2)

    # 4. GET: done=true, done=false 필터링
    def test_filter_by_done(self):
        self.client.post(
            "/api/todos/",
            json={"text": "우유 사기", "done": True}
        )

        self.client.post(
            "/api/todos/",
            json={"text": "책 반납", "done": False}
        )

        completed = self.client.get(
            "/api/todos/?done=true"
        )
        incomplete = self.client.get(
            "/api/todos/?done=false"
        )

        self.assertEqual(completed.status_code, 200)
        self.assertEqual(incomplete.status_code, 200)

        self.assertEqual(len(completed.get_json()), 1)
        self.assertEqual(len(incomplete.get_json()), 1)

        self.assertEqual(
            completed.get_json()[0]["text"],
            "우유 사기"
        )
        self.assertEqual(
            incomplete.get_json()[0]["text"],
            "책 반납"
        )

    # 5. GET: 한 건 조회 및 없는 번호 404
    def test_get_one_and_not_found(self):
        made = self.client.post(
            "/api/todos/",
            json={"text": "과제 하기", "note": "HW4"}
        ).get_json()

        response = self.client.get(
            f"/api/todos/{made['id']}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["note"], "HW4")

        missing = self.client.get("/api/todos/999")

        self.assertEqual(missing.status_code, 404)
        self.assertEqual(
            missing.get_json()["message"],
            "999 번 할 일이 없습니다"
        )

    # 6. PATCH: 보낸 값만 수정하고 나머지는 유지하는가?
    def test_patch_only_sent_fields(self):
        made = self.client.post(
            "/api/todos/",
            json={
                "text": "책 반납",
                "note": "도서관에 반납",
                "done": False
            }
        ).get_json()

        response = self.client.patch(
            f"/api/todos/{made['id']}",
            json={"done": True}
        )

        self.assertEqual(response.status_code, 200)

        data = response.get_json()

        self.assertTrue(data["done"])
        self.assertEqual(data["text"], "책 반납")
        self.assertEqual(data["note"], "도서관에 반납")

        # note만 바꾸는 PATCH도 확인
        response = self.client.patch(
            f"/api/todos/{made['id']}",
            json={"note": "내일까지 반납"}
        )

        data = response.get_json()

        self.assertEqual(data["note"], "내일까지 반납")
        self.assertTrue(data["done"])
        self.assertEqual(data["text"], "책 반납")

    # 7. PUT: 전체 교체 시 생략된 칸은 기본값이 되는가?
    def test_put_replaces_fields(self):
        made = self.client.post(
            "/api/todos/",
            json={
                "text": "원래 할 일",
                "note": "원래 설명",
                "done": True
            }
        ).get_json()

        response = self.client.put(
            f"/api/todos/{made['id']}",
            json={"text": "바뀐 할 일"}
        )

        self.assertEqual(response.status_code, 200)

        data = response.get_json()

        self.assertEqual(data["text"], "바뀐 할 일")
        self.assertEqual(data["note"], "")
        self.assertFalse(data["done"])

    # 8. DELETE: 204 반환 후 다시 조회하면 404인가?
    def test_delete_returns_204(self):
        made = self.client.post(
            "/api/todos/",
            json={"text": "삭제할 일"}
        ).get_json()

        response = self.client.delete(
            f"/api/todos/{made['id']}"
        )

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.data, b"")

        response = self.client.get(
            f"/api/todos/{made['id']}"
        )

        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()