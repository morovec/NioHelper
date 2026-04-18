from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import Admin, Post, PostMedia
from src.types.enums import PostStatus, Permission

# ═══════════════════════════════════════════
#  АДМИНЫ
# ═══════════════════════════════════════════

async def get_admin(session: AsyncSession, user_id: int) -> Optional[Admin]:
    result = await session.execute(
        select(Admin).where(Admin.user_id == user_id, Admin.is_active == True)
    )
    return result.scalar_one_or_none()

async def get_all_admins(session: AsyncSession) -> List[Admin]:
    result = await session.execute(
        select(Admin).where(Admin.is_active == True).order_by(Admin.created_at)
    )
    return list(result.scalars().all())

async def add_admin(
    session: AsyncSession,
    user_id: int,
    full_name: str,
    username: Optional[str]
) -> Admin:
    admin = Admin(
        user_id=user_id,
        full_name=full_name,
        username=username,
    )
    session.add(admin)
    await session.commit()
    await session.refresh(admin)
    return admin

async def remove_admin(session: AsyncSession, user_id: int) -> bool:
    result = await session.execute(
        update(Admin)
        .where(Admin.user_id == user_id)
        .values(is_active=False)
    )
    await session.commit()
    return result.rowcount > 0

# ═══════════════════════════════════════════
#  ПОСТЫ
# ═══════════════════════════════════════════

async def create_post(
    session: AsyncSession,
    caption: Optional[str],
    status: PostStatus = PostStatus.NEEDS_TEXT_EDIT,
) -> Post:
    """Создать пост"""

    post = Post(
        caption=caption,
        status=status,
    )
    session.add(post)
    await session.commit()
    await session.refresh(post)
    return post

async def add_media_to_post(
    session: AsyncSession,
    post_id: int,
    media_type: str,
    telegram_file_id: str,
    telegram_file_unique_id: Optional[str] = None,
    storage_message_id: Optional[int] = None,
    sort_order: int = 0
) -> PostMedia:
    media = PostMedia(
        post_id=post_id,
        media_type=media_type,
        telegram_file_id=telegram_file_id,
        telegram_file_unique_id=telegram_file_unique_id,
        storage_message_id=storage_message_id,
        sort_order=sort_order
    )
    session.add(media)
    await session.commit()
    await session.refresh(media)
    return media

async def get_post(session: AsyncSession, post_id: int) -> Optional[Post]:
    result = await session.execute(
        select(Post)
        .options(selectinload(Post.media))
        .where(Post.id == post_id)
    )
    return result.scalar_one_or_none()

async def get_ready_posts(session: AsyncSession) -> List[Post]:
    """Посты со статусом READY, отсортированные по очереди."""
    result = await session.execute(
        select(Post)
        .options(selectinload(Post.media))
        .where(
            Post.status == PostStatus.READY
        )
    )
    return list(result.scalars().all())

async def get_next_ready_post(session: AsyncSession) -> Optional[Post]:
    """Следующий пост для публикации."""
    result = await session.execute(
        select(Post)
        .options(selectinload(Post.media))
        .where(
            Post.status == PostStatus.READY
        )
        .limit(1)
    )
    return result.scalar_one_or_none()

async def get_next_raw_post(session: AsyncSession) -> Optional[Post]:
    """Следующий пост для редакции."""
    result = await session.execute(
        select(Post)
        .options(selectinload(Post.media))
        .where(
            Post.status != PostStatus.READY
        )
        .limit(1)
    )
    return result.scalar_one_or_none()

async def get_raw_posts(session: AsyncSession) -> List[Post]:
    """Посты со статусом READY, отсортированные по очереди."""
    result = await session.execute(
        select(Post)
        .options(selectinload(Post.media))
        .where(
            Post.status != PostStatus.READY
        )
    )
    return list(result.scalars().all())

async def get_tr_posts(session: AsyncSession) -> List[Post]:
    """Посты со статусом READY, отсортированные по очереди."""
    result = await session.execute(
        select(Post)
        .options(selectinload(Post.media))
        .where(
            Post.status != PostStatus.READY,
            Post.status != PostStatus.NEEDS_TEXT_EDIT
        )
    )
    return list(result.scalars().all())

async def update_post_status(
    session: AsyncSession, post_id: int, status: PostStatus
) -> bool:
    result = await session.execute(
        update(Post).where(Post.id == post_id).values(status=status)
    )
    await session.commit()
    return result.rowcount > 0

async def update_post_caption(
    session: AsyncSession, post_id: int, caption: str
) -> bool:
    result = await session.execute(
        update(Post).where(Post.id == post_id).values(caption=caption)
    )
    await session.commit()
    return result.rowcount > 0

async def delete_post(session: AsyncSession, post_id: int) -> bool:
    result = await session.execute(
        delete(Post).where(Post.id == post_id)
    )
    await session.commit()
    return result.rowcount > 0