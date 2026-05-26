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
    
    def __str__(self):
        return self.label