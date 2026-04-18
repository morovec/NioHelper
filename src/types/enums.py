# utils/enums.py
import enum


class PostStatus(str, enum.Enum):
    """Состояния поста"""
    READY = "ready"                          # ✅ Готов к публикации
    NEEDS_TEXT_EDIT = "needs_text_edit"      # ✏️ Требуется редакция текста
    NEEDS_IMAGE_TRANSLATE = "needs_img_tr"   # 🖼 Нужно перевести картинку
    NEEDS_EDIT_AND_TRANSLATE = "needs_both"  # 🔄 Редакция + перевод картинки

    @property
    def label(self) -> str:
        labels = {
            "ready": "✅ Готов к публикации",
            "needs_text_edit": "✏️ Требуется редакция текста",
            "needs_img_tr": "🖼️ Нужно перевести картинку",
            "needs_both": "🔄 Редакция + перевод картинки",
        }
        return labels[self.value]


class Permission(str, enum.Enum):
    """Права админов"""
    ADD_POST = "add_post"               # Добавлять посты
    EDIT_POST = "edit_post"             # Редактировать посты
    DELETE_POST = "delete_post"         # Удалять посты
    CHANGE_STATUS = "change_status"     # Менять статус поста
    MANAGE_QUEUE = "manage_queue"       # Управлять очередью
    MANAGE_ADMINS = "manage_admins"     # Управлять админами (добавлять/удалять)
    VIEW_QUEUE = "view_queue"           # Просматривать очередь

    @property
    def label(self) -> str:
        labels = {
            "add_post": "📝 Добавление постов",
            "edit_post": "✏️ Редактирование постов",
            "delete_post": "🗑 Удаление постов",
            "change_status": "🔄 Смена статуса",
            "manage_queue": "📋 Управление очередью",
            "manage_admins": "👑 Управление админами",
            "view_queue": "👁 Просмотр очереди",
        }
        return labels[self.value]