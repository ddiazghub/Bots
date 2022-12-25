from datetime import datetime, timedelta, timezone
import json
from typing import Dict, List, Tuple
from youtube import upload_video


TZ = timezone(timedelta(hours=-5))

def datetime_from_hour(hour: int) -> datetime:
    dt = datetime.now(tz=TZ)

    return dt.replace(minute=0, second=0, microsecond=0, hour=hour)


class PostScheduler:
    current_video: int
    last_post: datetime
    next_post: datetime
    post_hours: Tuple[int, int, int]
    videos: List[Dict[str, str]]


    def __init__(self, current_video: int, last_post: datetime, next_post: datetime, post_hours: Tuple[int, int, int], videos: List[Dict[str, str]]):
        self.current_video = current_video
        self.last_post = last_post
        self.next_post = next_post
        self.videos = videos
        self.post_hours = post_hours


    def from_json(file, videos: List[Dict[str, str]]):
        obj = json.load(file)
        current_video = obj["current_video"]
        last_post = datetime.fromtimestamp(obj["last_post"], tz=TZ)
        next_post = datetime.fromtimestamp(obj["next_post"], tz=TZ)
        post_hours = obj["post_hours"]

        return PostScheduler(current_video, last_post, next_post, post_hours, videos)


    def to_json(self) -> Dict[str, str]:
        return {
            "current_video": self.current_video,
            "last_post": self.last_post.timestamp(),
            "next_post": self.next_post.timestamp(),
            "post_hours": self.post_hours
        }


    def upload_next(self):
        if self.current_video > len(self.videos) - 1:
            self.current_video = 0

        now = datetime.now(tz=TZ)
        
        if len(self.videos) > 0:
            video = self.videos[self.current_video]
            print(video)
            upload_video(video["title"], video["description"], video["filepath"], video["tags"])
            self.last_post = now
            self.current_video += 1
        
        if now.hour >= self.post_hours[2]:
            self.next_post = datetime_from_hour(self.post_hours[0])
            self.next_post = self.next_post.replace(day=self.next_post.day + 1)
        elif now.hour >= self.post_hours[1]:
            self.next_post = datetime_from_hour(self.post_hours[2])
        elif now.hour >= self.post_hours[0]:
            self.next_post = datetime_from_hour(self.post_hours[1])
        else:
            self.next_post = datetime_from_hour(self.post_hours[0])

        print("Next video scheduled for: ", self.next_post)


    def pending(self) -> int:
        now = datetime.now(tz=TZ)
        diff = self.next_post.timestamp() - now.timestamp()
        pend = diff if diff > 0 else 1
        print(f"Pending: {pend}")

        return int(pend * 1000)