"""下载历史 API"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import DownloadHistory, User
from api.auth import get_current_user

router = APIRouter(prefix="/api", tags=["history"])


@router.get("/history")
async def get_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的下载历史"""
    records = (
        db.query(DownloadHistory)
        .filter(DownloadHistory.user_id == current_user.id)
        .order_by(DownloadHistory.created_at.desc())
        .limit(50)
        .all()
    )

    return {
        "code": 0,
        "data": [
            {
                "id": r.id,
                "url": r.url,
                "title": r.title,
                "thumbnail": r.thumbnail,
                "platform": r.platform,
                "quality": r.quality,
                "file_size": r.file_size,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in records
        ],
    }
