from .commands import command_router
from .switcher import switcher_router
from .post import post_router
from .comments import comments_router
from .stats import stats_router

routers = [command_router, switcher_router, post_router, comments_router, stats_router]