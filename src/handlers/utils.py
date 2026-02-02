import time
import re

def time_from_timestamp(timestamp: int) -> str:
    offset = 3 * 60 * 60
    t = time.gmtime(timestamp + offset)
    return f"{str(t.tm_mday).zfill(2)}.{str(t.tm_mon).zfill(2)} {t.tm_hour}:00"

def vk_text_to_tg(text: str) -> str:
    # [id558712784|Егор Пигин] [club221960296|PSA Union]

    text = re.sub(
        r'\[id(\d+)\|([^]]+)\]',
        r'<a href="https://vk.com/id\1">\2</a>',
        text
    )
    
    # Группы: [club123|Название] -> <a href="https://vk.com/club123">Название</a>
    for prefix in ['club', 'public', 'event']:
        text = re.sub(
            rf'\[{prefix}(\d+)\|([^]]+)\]',
            rf'<a href="https://vk.com/{prefix}\1">\2</a>',
            text
        )

    return text