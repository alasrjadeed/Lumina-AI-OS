import sys

import httpx

BASE = "http://localhost:8000"
PASS = 0
FAIL = 0


def test(name, method, path, status=200, body=None, check=None):
    global PASS, FAIL
    url = f"{BASE}{path}"
    label = f"{method} {path}"
    try:
        timeout = 60 if method == "POST" else 10
        if method == "GET":
            r = httpx.get(url, timeout=timeout)
        else:
            r = httpx.post(url, json=body, timeout=timeout)

        ok = r.status_code == status
        if ok and check:
            data = r.json()
            ok = check(data)

        icon = "\033[92m\u2714\033[0m" if ok else "\033[91m\u2718\033[0m"
        if ok:
            PASS += 1
            print(f"  {icon} {label}")
        else:
            FAIL += 1
            print(f"  {icon} {label}")
            if r.status_code != status:
                print(f"       expected {status}, got {r.status_code}")
            if r.text:
                preview = r.text[:120].replace("\n", " ")
                print(f"       response: {preview}")
    except Exception as e:
        FAIL += 1
        print(f"  \033[91m\u2718\033[0m {label}")
        print(f"       error: {e}")


def has_keys(*keys):
    def check(data):
        return all(k in data for k in keys)
    return check


def field_contains(key, substr):
    def check(data):
        val = data.get(key, "")
        return substr.lower() in val.lower()
    return check


def main():
    print()
    print("=" * 55)
    print("  LUMINA AI OS — INTERACTIVE TEST SUITE")
    print("=" * 55)
    print()

    test("Server info", "GET", "/", check=has_keys("app", "version", "status"))
    test("Health check", "GET", "/system/health", check=has_keys("status", "providers"))
    test("Config", "GET", "/system/config", check=has_keys("provider_priority", "models"))

    print()
    print("  --- CEO AI Chat ---")
    test("Chat - simple query", "POST", "/chat", body={"message": "Say hello in 3 words"},
         check=field_contains("reply", "hello"))

    print()
    print("  --- Code Generation ---")
    test("Code - hello world", "POST", "/code/generate",
         body={"description": "print hello world", "language": "python"},
         check=lambda d: len(d.get("code", "")) >= 10)

    print()
    print("  --- Agents ---")
    test("Agents list", "GET", "/agents", check=lambda d: len(d.get("agents", [])) >= 5)
    test("Agent - software_engineer", "POST", "/agents/run",
         body={"agent": "software_engineer", "task": "say hi"},
         check=lambda d: d.get("status") == "success")

    print()
    print("  --- Memory ---")
    test("Chat history", "GET", "/chat/history", check=has_keys("conversations"))

    print()
    print("=" * 55)
    total = PASS + FAIL
    if FAIL == 0:
        print(f"  \033[92mALL {total} TESTS PASSED\033[0m")
    else:
        print(f"  \033[91m{PASS}/{total} passed, {FAIL} failed\033[0m")
    print("=" * 55)
    print()
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
