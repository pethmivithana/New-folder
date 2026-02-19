# Agile Management Tool - Setup Documentation

## Overview
This is a full-stack agile management tool built with React + Vite + Tailwind CSS (frontend) and FastAPI + MongoDB (backend).

## Features
- **Space Management**: Create, edit, delete project spaces with team size limits
- **Sprint Management**: Create sprints with flexible durations (1-4 weeks or custom)
- **Backlog Items**: Manage tasks, bugs, stories, and subtasks with priorities and story points
- **Kanban Board**: Drag-and-drop interface for managing item status
- **Sprint Lifecycle**: Start, manage, and finish sprints with incomplete item handling
- **Assignee Management**: Track team members assigned to sprints

## Project Structure

```
New folder/
├── frontend/                           # React + Vite Frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── features/
│   │   │   │   └── sprint_impact_service/
│   │   │   │       ├── AgileManagement.jsx       # Main component
│   │   │   │       ├── SpaceManagement.jsx       # Space CRUD
│   │   │   │       ├── Dashboard.jsx             # Sprint & Backlog view
│   │   │   │       ├── SprintModal.jsx           # Sprint create/edit
│   │   │   │       ├── BacklogModal.jsx          # Backlog item create/edit
│   │   │   │       ├── KanbanBoard.jsx           # Drag-drop board
│   │   │   │       ├── FinishSprintModal.jsx     # Sprint completion
│   │   │   │       ├── RequirementTrackerModule.jsx  # Module wrapper
│   │   │   │       └── api.js                    # API client
│   │   │   └── common/                           # Shared components
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── postcss.config.js
│
└── services/
    └── sprint_impact_service/          # FastAPI Backend
        ├── main.py                     # FastAPI app entry
        ├── database.py                 # MongoDB connection
        ├── models.py                   # Pydantic models
        ├── routes/
        │   ├── space_routes.py         # Space endpoints
        │   ├── sprint_routes.py        # Sprint endpoints
        │   └── backlog_routes.py       # Backlog endpoints
        ├── .env                        # Environment variables
        └── requirements.txt            # Python dependencies
```

## Prerequisites

### Backend Requirements
- Python 3.8 or higher
- pip (Python package installer)
- MongoDB Atlas account (or local MongoDB)

### Frontend Requirements
- Node.js 16 or higher
- npm or yarn

## Installation & Setup

### 1. Backend Setup

#### Step 1: Navigate to backend directory
```bash
cd "New folder/services/sprint_impact_service"
```

#### Step 2: Create virtual environment (recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### Step 3: Install dependencies
```bash
pip install -r requirements.txt
```

#### Step 4: Configure environment variables
The `.env` file is already created with:
```
MONGODB_URI=mongodb+srv://pethmi9:pethmi09@cluster0.furwrbi.mongodb.net/agile-tool
```

**Important**: For production, create your own MongoDB cluster and update the credentials.

#### Step 5: Start the backend server
```bash
python main.py
```

The backend will start on: **http://localhost:8000**

You can access the API documentation at: **http://localhost:8000/docs**

### 2. Frontend Setup

#### Step 1: Navigate to frontend directory
```bash
cd "New folder/frontend"
```

#### Step 2: Install dependencies
```bash
npm install
```

#### Step 3: Start development server
```bash
npm run dev
```

The frontend will start on: **http://localhost:5173**

## Usage Guide

### 1. Creating a Space
1. Open http://localhost:5173 in your browser
2. Navigate to "Requirement & Sprint Tracker" from the sidebar
3. Click "Create Space"
4. Fill in:
   - Space Name
   - Description
   - Maximum Assignees (team size limit)
5. Click "Create"

### 2. Managing Spaces
- **View**: All spaces are displayed as cards
- **Edit**: Click the edit icon on any space card
- **Delete**: Click the delete icon (warning: deletes all sprints and items)
- **Open**: Click "Open" to enter the space dashboard

### 3. Creating Sprints
1. Inside a space, click "Create Sprint"
2. Fill in:
   - Sprint Name
   - Sprint Goal (description)
   - Duration: Select from 1-4 weeks or custom
   - If custom: Select start and end dates
3. Click "Create"

### 4. Managing Sprints
- **Edit**: Click edit icon (only name and goal can be changed)
- **Delete**: Click delete icon (items move back to backlog)
- **Start Sprint**: Click "Start Sprint" for planned sprints
- **Open Board**: Click "Open Board" for active/completed sprints
- **Finish Sprint**: Click "Finish Sprint" for active sprints

### 5. Creating Backlog Items
1. Click "Add Backlog Item"
2. Fill in:
   - Title
   - Description
   - Type: Task, Subtask, Bug, or Story
   - Priority: Low, Medium, High, or Critical
   - Story Points: 3-15
   - Assign to Sprint (optional)
3. Click "Create"

### 6. Managing Backlog Items
- **View**: Items are shown in sprints and backlog sections
- **Edit**: Click edit icon on any item
- **Delete**: Click delete icon
- **Assign to Sprint**: Use dropdown to assign unassigned items

### 7. Using the Kanban Board
1. Click "Open Board" on an active sprint
2. Drag and drop items between columns:
   - **To Do**: Items not started
   - **In Progress**: Currently being worked on
   - **In Review**: Under review
   - **Done**: Completed items
3. Close the board when finished

### 8. Finishing a Sprint
1. Click "Finish Sprint" on an active sprint
2. Choose what to do with incomplete items:
   - Move to Backlog
   - Move to Another Sprint (select from dropdown)
3. Click "Finish Sprint"
4. Sprint status changes to "Completed"

### 9. Adding Assignees
- Assignees can be added to sprints up to the space's maximum
- This feature tracks team members working on the sprint

## API Endpoints

### Spaces
- `POST /api/spaces/` - Create space
- `GET /api/spaces/` - Get all spaces
- `GET /api/spaces/{id}` - Get space by ID
- `PUT /api/spaces/{id}` - Update space
- `DELETE /api/spaces/{id}` - Delete space

### Sprints
- `POST /api/sprints/` - Create sprint
- `GET /api/sprints/space/{space_id}` - Get sprints by space
- `GET /api/sprints/{id}` - Get sprint by ID
- `PUT /api/sprints/{id}` - Update sprint
- `DELETE /api/sprints/{id}` - Delete sprint
- `POST /api/sprints/{id}/start` - Start sprint
- `POST /api/sprints/{id}/finish` - Finish sprint
- `POST /api/sprints/{id}/assignees` - Add assignee
- `DELETE /api/sprints/{id}/assignees/{number}` - Remove assignee

### Backlog Items
- `POST /api/backlog/` - Create item
- `GET /api/backlog/space/{space_id}` - Get all items in space
- `GET /api/backlog/space/{space_id}/backlog` - Get unassigned items
- `GET /api/backlog/sprint/{sprint_id}` - Get items in sprint
- `GET /api/backlog/{id}` - Get item by ID
- `PUT /api/backlog/{id}` - Update item
- `DELETE /api/backlog/{id}` - Delete item
- `PATCH /api/backlog/{id}/status` - Update item status

## Database Collections

### spaces
```javascript
{
  _id: ObjectId,
  name: String,
  description: String,
  max_assignees: Number,
  created_at: DateTime,
  updated_at: DateTime
}
```

### sprints
```javascript
{
  _id: ObjectId,
  name: String,
  goal: String,
  duration_type: String, // "1 Week", "2 Weeks", etc.
  start_date: Date,
  end_date: Date,
  space_id: String,
  status: String, // "Planned", "Active", "Completed"
  assignees: [Number],
  created_at: DateTime,
  updated_at: DateTime
}
```

### backlog_items
```javascript
{
  _id: ObjectId,
  title: String,
  description: String,
  type: String, // "Task", "Subtask", "Bug", "Story"
  priority: String, // "Low", "Medium", "High", "Critical"
  story_points: Number, // 3-15
  status: String, // "To Do", "In Progress", "In Review", "Done"
  space_id: String,
  sprint_id: String | null,
  created_at: DateTime,
  updated_at: DateTime
}
```

## Running in Production

### Backend
```bash
# Install production server
pip install gunicorn

# Run with gunicorn
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Frontend
```bash
# Build for production
npm run build

# Serve the build folder with any static file server
# For example, using serve:
npm install -g serve
serve -s dist -l 5173
```

## Troubleshooting

### Backend Issues

**MongoDB Connection Error**
- Verify MONGODB_URI in .env file
- Check network connectivity
- Ensure MongoDB Atlas IP whitelist includes your IP

**Port 8000 Already in Use**
```bash
# Find process using port 8000
# Windows
netstat -ano | findstr :8000

# macOS/Linux
lsof -i :8000

# Kill the process or change port in main.py
```

### Frontend Issues

**Dependencies Installation Failed**
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and package-lock.json
rm -rf node_modules package-lock.json

# Reinstall
npm install
```

**Port 5173 Already in Use**
- Vite will automatically try the next available port
- Or change port in vite.config.js

**API Connection Error**
- Ensure backend is running on port 8000
- Check CORS settings in backend main.py
- Verify API_BASE_URL in api.js matches backend URL

## Development Tips

1. **Hot Reload**: Both frontend and backend support hot reload during development
2. **API Testing**: Use the auto-generated Swagger docs at http://localhost:8000/docs
3. **Database Inspection**: Use MongoDB Compass to view/edit data directly
4. **Browser DevTools**: Check Network tab for API call debugging

## Feature Additions

To add new features:

1. **Backend**: Add new routes in `routes/` directory
2. **Frontend**: Add new components in `components/features/sprint_impact_service/`
3. **API Client**: Update `api.js` with new endpoints
4. **Models**: Update `models.py` for new data structures

## Notes

- Duration cannot be changed after sprint creation
- Only one active sprint allowed per space at a time
- Incomplete items from finished sprints can be moved to backlog or another sprint
- Story points range is limited to 3-15
- All dates and times are stored in UTC

## Support

For issues or questions:
1. Check API documentation at http://localhost:8000/docs
2. Review browser console for frontend errors
3. Check backend logs for API errors
4. Verify MongoDB connection and data

## License

This project is for educational/internal use.
