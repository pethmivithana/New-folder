# Quick Start Guide

## Prerequisites
- Python 3.8+ installed
- Node.js 16+ installed
- Internet connection (for MongoDB Atlas)

## Step 1: Setup Backend

### Windows:
1. Open Command Prompt or PowerShell
2. Navigate to backend folder:
   ```
   cd "New folder\services\sprint_impact_service"
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Run the backend:
   ```
   python main.py
   ```
   OR double-click `start_backend.bat`

### macOS/Linux:
1. Open Terminal
2. Navigate to backend folder:
   ```
   cd "New folder/services/sprint_impact_service"
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Run the backend:
   ```
   python3 main.py
   ```
   OR execute `./start_backend.sh`

**Backend should now be running on http://localhost:8000**

## Step 2: Setup Frontend

### Windows:
1. Open a NEW Command Prompt or PowerShell window
2. Navigate to frontend folder:
   ```
   cd "New folder\frontend"
   ```
3. Install dependencies:
   ```
   npm install
   ```
4. Run the frontend:
   ```
   npm run dev
   ```
   OR double-click `start_frontend.bat`

### macOS/Linux:
1. Open a NEW Terminal window
2. Navigate to frontend folder:
   ```
   cd "New folder/frontend"
   ```
3. Install dependencies:
   ```
   npm install
   ```
4. Run the frontend:
   ```
   npm run dev
   ```
   OR execute `./start_frontend.sh`

**Frontend should now be running on http://localhost:5173**

## Step 3: Access the Application

1. Open your web browser
2. Go to: http://localhost:5173
3. Click on "Requirement & Sprint Tracker" in the sidebar
4. Start creating your agile workspace!

## First Time Usage

1. **Create a Space**: Click "Create Space" and fill in the details
2. **Open the Space**: Click "Open" on your newly created space
3. **Create a Sprint**: Click "Create Sprint" and set up your first sprint
4. **Add Backlog Items**: Click "Add Backlog Item" to create tasks
5. **Start Sprint**: Click "Start Sprint" when ready to begin
6. **Open Board**: Use the Kanban board to manage items

## Troubleshooting

### Backend won't start:
- Check if Python is installed: `python --version` or `python3 --version`
- Ensure port 8000 is not in use
- Verify MongoDB URI in .env file

### Frontend won't start:
- Check if Node.js is installed: `node --version`
- Clear npm cache: `npm cache clean --force`
- Delete node_modules and reinstall: `rm -rf node_modules && npm install`

### Can't connect to MongoDB:
- Check your internet connection
- Verify the MONGODB_URI in the .env file
- For production, create your own MongoDB Atlas cluster

### Port already in use:
- **Backend**: Change port in main.py (last line)
- **Frontend**: Vite will automatically use next available port

## Next Steps

Read the full [SETUP_DOCUMENTATION.md](./SETUP_DOCUMENTATION.md) for:
- Detailed feature documentation
- API endpoints reference
- Database schema
- Production deployment guide
- Advanced configuration

## Need Help?

Check:
1. Backend logs in the terminal where you ran `python main.py`
2. Frontend logs in browser DevTools (F12)
3. API documentation at http://localhost:8000/docs
4. Full documentation in SETUP_DOCUMENTATION.md
