import httpx, uuid
user_id = 'pit-wall-user'
session_id = str(uuid.uuid4())
base = 'http://localhost:9001'
r1 = httpx.post(f'{base}/apps/rival_agent/users/{user_id}/sessions/{session_id}', json={}, timeout=10)
print('Session create:', r1.status_code)
r2 = httpx.post(f'{base}/run', json={'appName': 'rival_agent', 'userId': user_id, 'sessionId': session_id, 'newMessage': {'role': 'user', 'parts': [{'text': 'Call emit_bluff_signal now'}]}}, timeout=30)
print('Message send:', r2.status_code)
print(r2.text[:400])
