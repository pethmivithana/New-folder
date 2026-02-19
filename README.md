# Agile Management Tool

A comprehensive agile project management system built with React, FastAPI, and MongoDB.

## Quick Start

### Backend (Port 8000)
```bash
cd "New folder/services/sprint_impact_service"
pip install -r requirements.txt
python main.py
```

### Frontend (Port 5173)
```bash
cd "New folder/frontend"
npm install
npm run dev
```

## Access

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Features

✅ Space Management (Create, Edit, Delete)  
✅ Sprint Planning (1-4 weeks or custom duration)  
✅ Backlog Item Management (Task, Bug, Story, Subtask)  
✅ Kanban Board (Drag & Drop)  
✅ Sprint Lifecycle (Plan → Active → Completed)  
✅ Assignee Tracking  
✅ Priority & Story Points  

## Tech Stack

**Frontend:**
- React 18
- Vite
- Tailwind CSS
- React Router DOM

**Backend:**
- FastAPI
- Motor (Async MongoDB)
- Pydantic
- Python 3.8+

**Database:**
- MongoDB Atlas

## Documentation

See [SETUP_DOCUMENTATION.md](./SETUP_DOCUMENTATION.md) for detailed setup instructions, API endpoints, and usage guide.

## Project Structure

```
New folder/
├── frontend/                    # React frontend
│   └── src/components/features/sprint_impact_service/
├── services/
│   └── sprint_impact_service/  # FastAPI backend
└── SETUP_DOCUMENTATION.md
```

## Environment Variables

Backend `.env`:
```
MONGODB_URI=mongodb+srv://pethmi9:pethmi09@cluster0.furwrbi.mongodb.net/agile-tool
```

## Development

Both frontend and backend support hot reload for rapid development.

**Note**: This tool is integrated into a larger application. Navigate to "Requirement & Sprint Tracker" from the sidebar to access it.
