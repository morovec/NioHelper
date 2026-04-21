from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import (
    BigInteger, String, Text, Integer, Boolean,
    ForeignKey, Enum as SAEnum, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship


from src.types.enums import PostStatus

from typing import List, Optional

class Base(DeclarativeBase):
	pass

class Admin(Base):
    """Админы бота"""
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Telegram user_id
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)

    # Имя для удобства
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, default="Unknown")

    # Активен ли админ
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    def __repr__(self):
        return f"<Admin user_id={self.user_id} username={self.username} full_name={self.full_name} active={self.is_active}>"
    

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

    translation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("idx_post_status", "status"),
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

    # Связь
    post: Mapped["Post"] = relationship(back_populates="media")

    def __repr__(self):
        return f"<PostMedia id={self.id} type={self.media_type} post={self.post_id}>"