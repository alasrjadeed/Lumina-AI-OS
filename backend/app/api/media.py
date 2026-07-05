from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from backend.app.services.ai.engine import AIEngine
from backend.app.services.media.writer_service import WriterService
from backend.app.services.media.video_service import VideoService
from backend.app.services.media.podcast_service import PodcastService

router = APIRouter()
engine = AIEngine()
writer = WriterService(engine)
video = VideoService(engine)
podcast = PodcastService(engine)


class ArticleRequest(BaseModel):
    topic: str
    length: str = "medium"
    tone: str = "professional"
    format: str = "article"


class VideoScriptRequest(BaseModel):
    topic: str
    duration: str = "5min"
    style: str = "educational"


class PodcastRequest(BaseModel):
    title: str
    topic: str
    duration: str = "20min"
    style: str = "conversational"


@router.post("/article")
async def write_article(req: ArticleRequest):
    return await writer.write_article(req.topic, req.length, req.tone, req.format)


@router.post("/edit")
async def edit_content(content: str, instructions: str):
    return await writer.edit_content(content, instructions)


@router.post("/video/script")
async def video_script(req: VideoScriptRequest):
    return await video.create_script(req.topic, req.duration, req.style)


@router.post("/video/storyboard")
async def storyboard(script: str):
    return await video.storyboard(script)


@router.post("/podcast/episode")
async def podcast_episode(req: PodcastRequest):
    return await podcast.create_episode(req.title, req.topic, req.duration, req.style)


@router.post("/podcast/notes")
async def show_notes(episode_title: str, transcript: str):
    return await podcast.show_notes(episode_title, transcript)


@router.post("/podcast/interview")
async def interview_questions(guest: str, topic: str):
    return await podcast.interview_questions(guest, topic)
