from typing import List
from pydantic import BaseModel, Field

tracks = [{
            "track_id": 0, 
            "name": "drums"
            },
            {
            "track_id": 1, 
            "name": "bass"
            },
            {
            "track_id": 2, 
            "name": "other"
            },
            {
            "track_id": 3, 
            "name": "vocals"
            }
        ]

class Song(BaseModel):
    music_id : str = Field(default = None)
    name : str = Field(default = None)
    tracks : List[dict] = Field(default = tracks)
    size : int = Field(default = None)
    time : int = Field(default = None)

    class config:
        u_schema = {
            "music_id": "2364hfdsjf",
            "name": "example.mp3", 
            "tracks": [
                    {
                    "track_id": 0, 
                    "name": "bass"
                    },
                    {
                    "track_id": 1, 
                    "name": "drums"
                    },
                    {
                    "track_id": 2, 
                    "name": "other"
                    },
                    {
                    "track_id": 3, 
                    "name": "vocals"
                    }
            ],
            "time" : 0
            }

class ProcessSong(BaseModel):
    tracks : List[int]

    class config:
        u_schema = {
            "example" : {
                "tracks" : [0, 3]
            }
        }

class ProcessSongResponse(BaseModel):
    progress : int = Field(default = 0)
    instruments : List[dict] = Field(default = None)
    final : str = Field(default = None)

    class config:
        u_schema = {
            "progress": 0,
            "instruments": [
                {
                "name": "guitar",
                "track": "http://localhost/file/12314"
                },
                {
                "name": "bass",
                "track": "http://localhost/file/34567"
                }
            ],
            "final": "http://localhost/file/31231234"
            }
        
class Job(BaseModel):
    job_id : int = Field(default = None)
    size : int = Field(default = None)
    music_id : str = Field(default = None)
    block_id : int = Field(default = None)
    tracks : List[int] = Field(default = None)
    size_of_block : int = Field(default = None)
    status : str = Field(default = 'processing')
    processing_time : int = Field(default = 0)