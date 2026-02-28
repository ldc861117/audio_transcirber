---
description: Start the Audio Transcriber application (Flask backend + React frontend)
---

# Start Audio Transcriber

// turbo-all

1. Stop any existing processes on ports 5099 and 3000:

```bash
lsof -ti:5099 | xargs kill -9 2>/dev/null; lsof -ti:3000 | xargs kill -9 2>/dev/null; echo "Ports cleared"
```

2. Run the start script:

```bash
bash start.sh
```

The app will be available at:

- **Backend (old UI):** http://localhost:5099
- **Frontend (React):** http://localhost:3000
