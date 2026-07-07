from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Depends
from app.schemas import UserRead, UserCreate, UserUpdate
from app.db import Post, create_db_and_tables, get_async_session, User
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from sqlalchemy import select, func
from app.images import imagekit
import shutil
import tempfile
import os
from app.users import auth_backend, fastapi_users, current_active_user

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield
  
app = FastAPI(lifespan=lifespan)
app.include_router(fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"])
app.include_router(fastapi_users.get_register_router(UserRead, UserCreate), prefix="/auth", tags=["auth"])
app.include_router(fastapi_users.get_reset_password_router(), prefix="/auth", tags=["auth"])
app.include_router(fastapi_users.get_verify_router(UserRead), prefix="/auth", tags=["auth"])
app.include_router(fastapi_users.get_users_router(UserRead, UserUpdate), prefix="/users", tags=["users"])


@app.post("/upload")
async def upload_file(file: UploadFile = File(...), steps: int = Form(None), distance: float = Form(None), duration: float = Form(None), caption: str = Form(""), user: User = Depends(current_active_user), session: AsyncSession = Depends(get_async_session)):
    temp_file_path = None
    try:
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file_path = temp_file.name
            shutil.copyfileobj(file.file, temp_file)
        with open(temp_file_path, "rb") as f:
            upload_result = imagekit.files.upload(
                file=f,
                file_name=file.filename,
                use_unique_file_name=True,
                tags=["backend-upload"],
            )

        post = Post(caption=caption, user_id=user.id,url=upload_result.url, steps=steps, distance=distance, duration=duration, file_type="video" if file.content_type.startswith("video/") else "photo", file_name=upload_result.name)
        session.add(post)
        await session.commit()
        await session.refresh(post)
        return post
    except Exception as e:
        pass
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        file.file.close()


@app.get("/feed")
async def get_feed(session: AsyncSession = Depends(get_async_session), user: User = Depends(current_active_user)):
    result = await session.execute(select(Post, User).join(User, Post.user_id == User.id).order_by(Post.created_at.desc()))
    rows = result.all()

    posts_data = []
    for post, post_user in rows:
        posts_data.append(
            {
                "id": str(post.id),
                "email": post_user.email,
                "caption": post.caption,
                "steps": post.steps,
                "distance": post.distance,
                "duration": post.duration,
                "file_type": post.file_type,
                "file_name": post.file_name,
                "url": post.url,
                "is_owner": post.user_id == user.id,
                "created_at": post.created_at.isoformat(),
            }
        )
    return {"posts": posts_data}


@app.get("/leaderboard")
async def get_leaderboard(session: AsyncSession = Depends(get_async_session), user: User = Depends(current_active_user)):
    result = await session.execute(
        select(
            User.id,
            User.email,
            func.coalesce(func.sum(Post.steps), 0).label("total_steps"),
            func.coalesce(func.sum(Post.distance), 0).label("total_distance"),
            func.count(Post.id).label("post_count"),
        )
        .outerjoin(Post, Post.user_id == User.id)
        .group_by(User.id, User.email)
        .order_by(func.coalesce(func.sum(Post.steps), 0).desc())
    )
    rows = result.all()

    leaderboard = []
    for rank, row in enumerate(rows, start=1):
        # Fetch the most recent screenshot/post URL for this user
        latest_post_result = await session.execute(
            select(Post.url, Post.file_type)
            .where(Post.user_id == row.id)
            .order_by(Post.created_at.desc())
            .limit(1)
        )
        latest_post = latest_post_result.first()

        leaderboard.append(
            {
                "rank": rank,
                "email": row.email,
                "total_steps": row.total_steps,
                "total_distance": round(row.total_distance, 2),
                "post_count": row.post_count,
                "latest_screenshot_url": latest_post.url if latest_post else None,
                "latest_file_type": latest_post.file_type if latest_post else None,
            }
        )
    return {"leaderboard": leaderboard}