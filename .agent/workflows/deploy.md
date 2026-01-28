---
description: Standard Operating Procedure for Backend/Frontend Deployment with Versioning
---

# // turbo-all

Follow these steps for every deployment to ensure production stability and visual confirmation of changes:

1. **Bump Version Number**: 
   - Increment the version in `backend/app/main.py` (e.g., v3.9 -> v4.0).
   - Increment the version in `frontend/src/app/dashboard/page.tsx` (all occurrences).
   - Document the bump in your current `TaskSummary`.

2. **Validate Database Schema**:
   - If new models were added, run:
     `python3 -c "from app.db.session import engine; from app.models import Base; Base.metadata.create_all(bind=engine)"` in the `backend` directory.

3. **Deploy Backend**:
   - Run `modal deploy modal_app.py` from the `backend` directory.

4. **Verify Health**:
   - Run `curl https://ifvckinglovef1--qbo-sync-engine-fastapi-app.modal.run/health` to confirm the new version is live.

5. **Notify User**:
   - Confirm the new version number in the `notify_user` call.
