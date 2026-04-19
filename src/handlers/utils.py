import re

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