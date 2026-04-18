from sqlalchemy.orm import declarative_base
from sqlalchemy import (
    BigInteger, String, Text, Integer, Boolean,
    ForeignKey, Enum as SAEnum, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ARRAY

from src.types.enums import PostStatus, Permission

from typing import List, Optional

Base = declarative_base()


class Admin(Base):
    """Админы бота"""
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Telegram user_id
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)

    # Имя для удобства
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, default="Unknown")

    # Список прав — хранится как массив строк
    permissions: Mapped[List[str]] = mapped_column(
        ARRAY(String), nullable=False, default=list
    )

    # Активен ли админ
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    def has_permission(self, perm: Permission) -> bool:
        return perm.value in self.permissions

    def __repr__(self):
        return f"<Admin user_id={self.user_id} perms={self.permissions}>"
    

class Post(Base):
    """Пост для публикации"""
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Текст поста (caption)
    caption: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Статус поста
    status: Mapped[PostStatus] = mapped_column(
        SAEnum(PostStatus, name="post_status", create_constraint=True),
        nullable=False,
        default=PostStatus.NEEDS_TEXT_EDIT
    )

    media: Mapped[List["PostMedia"]] = relationship(
        back_populates="post",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="PostMedia.sort_order"
    )

    __table_args__ = (
        Index("status"),
    )

    def __repr__(self):
        return f"<Post id={self.id} status={self.status.value}>"


class PostMedia(Base):
    """Медиа-файлы поста"""
    __tablename__ = "post_media"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    post_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False
    )

    # Порядок в альбоме
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Тип: photo / video / animation / document
    media_type: Mapped[str] = mapped_column(String(20), nullable=False)

    # Telegram file_id — главное, что нужно для повторной отправки
    telegram_file_id: Mapped[str] = mapped_column(Text, nullable=False)

    # Уникальный id файла (для дедупликации)
    telegram_file_unique_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Где хранится в storage-канале
    storage_message_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    # Связь
    post: Mapped["Post"] = relationship(back_populates="media")

    def __repr__(self):
        return f"<PostMedia id={self.id} type={self.media_type} post={self.post_id}>"