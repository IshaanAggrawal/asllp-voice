# 📮 Postman Collection Setup Guide

Complete guide to creating and using the Postman collection for the Voice Orchestration API.

---

## 🎯 Quick Import (If Collection Exists)

If you already have the `Voice_Orchestration_API.postman_collection.json` file:

1. Open Postman
2. Click **Import** (top left)
3. Drag and drop `postman/Voice_Orchestration_API.postman_collection.json`
4. Click **Import**
5. Done! Skip to [Usage](#-usage)

---

## 🛠️ Creating Collection from Scratch

### Step 1: Create New Collection

1. Open Postman
2. Click **Collections** in sidebar
3. Click **+ New Collection**
4. Name it: `Voice Orchestration API`
5. Add description:
   ```
   Real-Time AI Voice Orchestration System API
   Includes authentication, agent management, and session endpoints
   ```

### Step 2: Create Environment

1. Click **Environments** (left sidebar)
2. Click **+ Create Environment**
3. Name: `Voice Orchestration - Local`
4. Add variables:

| Variable | Initial Value | Current Value |
|----------|---------------|---------------|
| `base_url` | `http://localhost:8000` | `http://localhost:8000` |
| `fastapi_url` | `http://localhost:8001` | `http://localhost:8001` |
| `access_token` | *(leave empty)* | *(leave empty)* |
| `refresh_token` | *(leave empty)* | *(leave empty)* |
| `agent_id` | *(leave empty)* | *(leave empty)* |
| `session_id` | *(leave empty)* | *(leave empty)* |

5. Click **Save**

### Step 3: Add Requests

Create folders and requests as follows:

---

## 📁 Folder 1: Authentication

### 1.1 Register User

- **Method**: `POST`
- **URL**: `{{base_url}}/api/auth/register/`
- **Headers**:
  ```
  Content-Type: application/json
  ```
- **Body** (raw JSON):
  ```json
  {
    "username": "testuser",
    "email": "test@example.com",
    "password": "TestPass123!",
    "first_name": "Test",
    "last_name": "User"
  }
  ```
- **Tests** (Scripts tab):
  ```javascript
  pm.test("Status code is 201", function () {
      pm.response.to.have.status(201);
  });
  
  pm.test("Response has success field", function () {
      var jsonData = pm.response.json();
      pm.expect(jsonData).to.have.property('success');
      pm.expect(jsonData.success).to.be.true;
  });
  ```

### 1.2 Login

- **Method**: `POST`
- **URL**: `{{base_url}}/api/auth/login/`
- **Headers**:
  ```
  Content-Type: application/json
  ```
- **Body** (raw JSON):
  ```json
  {
    "username": "testuser",
    "password": "TestPass123!"
  }
  ```
- **Tests**:
  ```javascript
  pm.test("Status code is 200", function () {
      pm.response.to.have.status(200);
  });
  
  pm.test("Response has tokens", function () {
      var jsonData = pm.response.json();
      pm.expect(jsonData).to.have.property('access');
      pm.expect(jsonData).to.have.property('refresh');
      
      // Save tokens to environment
      pm.environment.set("access_token", jsonData.access);
      pm.environment.set("refresh_token", jsonData.refresh);
  });
  ```

### 1.3 Refresh Token

- **Method**: `POST`
- **URL**: `{{base_url}}/api/auth/token/refresh/`
- **Headers**:
  ```
  Content-Type: application/json
  ```
- **Body** (raw JSON):
  ```json
  {
    "refresh": "{{refresh_token}}"
  }
  ```
- **Tests**:
  ```javascript
  pm.test("Status code is 200", function () {
      pm.response.to.have.status(200);
  });
  
  pm.test("New access token received", function () {
      var jsonData = pm.response.json();
      pm.expect(jsonData).to.have.property('access');
      pm.environment.set("access_token", jsonData.access);
  });
  ```

---

## 📁 Folder 2: Agents

### 2.1 Create Agent

- **Method**: `POST`
- **URL**: `{{base_url}}/api/agents/`
- **Headers**:
  ```
  Content-Type: application/json
  Authorization: Bearer {{access_token}}
  ```
- **Body** (raw JSON):
  ```json
  {
    "name": "Customer Support Bot",
    "system_prompt": "You are a helpful and friendly customer support agent. Always be polite and professional.",
    "orchestration_model": "qwen2:1.5b",
    "conversation_model": "llama3.2:1b"
  }
  ```
- **Tests**:
  ```javascript
  pm.test("Status code is 201", function () {
      pm.response.to.have.status(201);
  });
  
  pm.test("Agent created with ID", function () {
      var jsonData = pm.response.json();
      pm.expect(jsonData.data).to.have.property('id');
      pm.environment.set("agent_id", jsonData.data.id);
  });
  ```

### 2.2 List Agents

- **Method**: `GET`
- **URL**: `{{base_url}}/api/agents/`
- **Headers**:
  ```
  Authorization: Bearer {{access_token}}
  ```
- **Tests**:
  ```javascript
  pm.test("Status code is 200", function () {
      pm.response.to.have.status(200);
  });
  
  pm.test("Response is array", function () {
      var jsonData = pm.response.json();
      pm.expect(jsonData.data).to.be.an('array');
  });
  ```

### 2.3 Get Agent Details

- **Method**: `GET`
- **URL**: `{{base_url}}/api/agents/{{agent_id}}/`
- **Headers**:
  ```
  Authorization: Bearer {{access_token}}
  ```

### 2.4 Update Agent

- **Method**: `PUT`
- **URL**: `{{base_url}}/api/agents/{{agent_id}}/`
- **Headers**:
  ```
  Content-Type: application/json
  Authorization: Bearer {{access_token}}
  ```
- **Body** (raw JSON):
  ```json
  {
    "name": "Updated Agent Name",
    "system_prompt": "Updated system prompt..."
  }
  ```

### 2.5 Delete Agent

- **Method**: `DELETE`
- **URL**: `{{base_url}}/api/agents/{{agent_id}}/`
- **Headers**:
  ```
  Authorization: Bearer {{access_token}}
  ```

---

## 📁 Folder 3: Sessions

### 3.1 Create Session

- **Method**: `POST`
- **URL**: `{{base_url}}/api/sessions/`
- **Headers**:
  ```
  Content-Type: application/json
  Authorization: Bearer {{access_token}}
  ```
- **Body** (raw JSON):
  ```json
  {
    "agent_id": {{agent_id}}
  }
  ```
- **Tests**:
  ```javascript
  pm.test("Status code is 201", function () {
      pm.response.to.have.status(201);
  });
  
  pm.test("Session created with ID", function () {
      var jsonData = pm.response.json();
      pm.expect(jsonData.data).to.have.property('id');
      pm.environment.set("session_id", jsonData.data.id);
  });
  ```

### 3.2 List Sessions

- **Method**: `GET`
- **URL**: `{{base_url}}/api/sessions/`
- **Headers**:
  ```
  Authorization: Bearer {{access_token}}
  ```

### 3.3 Get Session Details

- **Method**: `GET`
- **URL**: `{{base_url}}/api/sessions/{{session_id}}/`
- **Headers**:
  ```
  Authorization: Bearer {{access_token}}
  ```

### 3.4 End Session

- **Method**: `POST`
- **URL**: `{{base_url}}/api/sessions/{{session_id}}/end/`
- **Headers**:
  ```
  Authorization: Bearer {{access_token}}
  ```

---

## 📁 Folder 4: Health Checks

### 4.1 Django Health

- **Method**: `GET`
- **URL**: `{{base_url}}/api/`
- **Tests**:
  ```javascript
  pm.test("Django API is running", function () {
      pm.response.to.have.status(200);
  });
  ```

### 4.2 FastAPI Health

- **Method**: `GET`
- **URL**: `{{fastapi_url}}/`
- **Tests**:
  ```javascript
  pm.test("FastAPI is running", function () {
      pm.response.to.have.status(200);
  });
  ```

### 4.3 Ollama Status

- **Method**: `GET`
- **URL**: `http://localhost:11434/api/tags`
- **Tests**:
  ```javascript
  pm.test("Ollama is running", function () {
      pm.response.to.have.status(200);
  });
  
  pm.test("Required models installed", function () {
      var jsonData = pm.response.json();
      var models = jsonData.models.map(m => m.name);
      pm.expect(models.some(m => m.includes('qwen'))).to.be.true;
      pm.expect(models.some(m => m.includes('llama'))).to.be.true;
  });
  ```

---

## 📤 Export Collection

1. Right-click collection name
2. Click **Export**
3. Select **Collection v2.1** (recommended)
4. Click **Export**
5. Save as: `postman/Voice_Orchestration_API.postman_collection.json`

---

## 🎮 Usage

### Running the Full Test Sequence

1. Select environment: `Voice Orchestration - Local`
2. Run requests in order:
   - **Register User** (once)
   - **Login** (saves tokens)
   - **Create Agent** (saves agent_id)
   - **Create Session** (saves session_id)
   - **Get Session Details**
   - **End Session**

### Using Collection Runner

1. Click collection name
2. Click **Run**
3. Select all requests
4. Click **Run Voice Orchestration API**
5. View results

### Testing WebSocket (Advanced)

Postman doesn't support WebSockets natively. Use browser console:

```javascript
// Copy session_id from Postman environment
const sessionId = "your-session-id-here";
const ws = new WebSocket(`ws://localhost:8001/ws/voice/${sessionId}`);

ws.onopen = () => {
    console.log('✅ Connected');
    
    // Send config
    ws.send(JSON.stringify({
        type: 'config',
        config: {
            name: 'Test Agent',
            system_prompt: 'You are helpful.'
        }
    }));
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('📨 Received:', data);
};

ws.onerror = (error) => {
    console.error('❌ Error:', error);
};
```

---

## 🔧 Troubleshooting

### "Unauthorized" Errors

- Run **Login** request again
- Check if `access_token` is set in environment
- Token expires after 24 hours - use **Refresh Token**

### "Agent not found"

- Run **Create Agent** first
- Check if `agent_id` is set in environment

### Connection Refused

- Ensure servers are running:
  ```bash
  # Django (Terminal 1)
  cd backend/django_app && python manage.py runserver
  
  # FastAPI (Terminal 2)
  cd backend/fastapi_app && uvicorn main:app --port 8001
  ```

### Environment Variables Not Working

- Select correct environment (top right dropdown)
- Check variable names match exactly (case-sensitive)
- Save environment after changes

---

## 📋 Pre-Request Scripts (Optional)

Add to collection-level Pre-request Script for automatic token refresh:

```javascript
// Check if token is about to expire
const tokenExp = pm.environment.get("token_expiry");
const now = Date.now();

if (!tokenExp || now >= tokenExp) {
    // Refresh token
    pm.sendRequest({
        url: pm.environment.get("base_url") + "/api/auth/token/refresh/",
        method: 'POST',
        header: {
            'Content-Type': 'application/json'
        },
        body: {
            mode: 'raw',
            raw: JSON.stringify({
                refresh: pm.environment.get("refresh_token")
            })
        }
    }, function (err, res) {
        if (!err) {
            const newToken = res.json().access;
            pm.environment.set("access_token", newToken);
            pm.environment.set("token_expiry", now + (24 * 60 * 60 * 1000)); // 24 hours
        }
    });
}
```

---

## 🎯 Best Practices

1. **Use Environments** - Separate Local, Staging, Production
2. **Add Tests** - Validate responses automatically
3. **Use Variables** - Avoid hardcoding IDs
4. **Document** - Add descriptions to requests
5. **Version Control** - Commit collection JSON to git
6. **Share** - Export and share with team

---

**Happy Testing! 🚀**
