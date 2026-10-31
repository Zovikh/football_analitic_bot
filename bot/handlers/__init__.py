from aiogram import Router

from bot.handlers import analyze, chart, common, hr, insight, matches, seo, smm, start, value


def setup_routers() -> Router:
    root = Router()
    root.include_router(start.router)
    root.include_router(matches.router)
    root.include_router(analyze.router)
    root.include_router(value.router)
    root.include_router(insight.router)
    root.include_router(chart.router)
    root.include_router(smm.router)
    root.include_router(hr.router)
    root.include_router(seo.router)
    root.include_router(common.router)
    return root
