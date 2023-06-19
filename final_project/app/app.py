from fastapi import FastAPI, status, Response, UploadFile, File
from resp_models.models import Song, Job, ProcessSong
from typing import Dict, List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import pika
import aio_pika
from demucs.pretrained import SOURCES
import json
import asyncio
import base64
from pymongo import MongoClient
from bson import ObjectId
from gridfs import GridFS, NoFile
from mutagen.mp3 import MP3
import uuid
import tempfile
from pydub import AudioSegment
from fastapi.responses import FileResponse

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect to MongoDB
client = MongoClient('mongodb://admin:admin@localhost:27017')

db = client['database']

songs_db = GridFS(db, collection="songs")
jobs_db = db['jobs']
track_db = db['tracks']

async def consume_job_queue():
    connection = await aio_pika.connect_robust("amqp://localhost")
    channel = await connection.channel() 

    await channel.set_qos(prefetch_count=1)
    queue = await channel.declare_queue("job_queue")

    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            async with message.process():
                data = json.loads(message.body.decode('utf-8'))
                await process_job(data)

async def process_job(data):
    audio_data = base64.b64decode(data['body'])
    # Define the filter to identify the document and update the status
    filter = {"job_id": data['job_id']}
    update = {
        "$set": {
            "status": "done",
            "processing_time": data['processing_time']
        }
    }
    track_db.insert_one({
            "job_id": data['job_id'],
            "music_id": str(data['song_id']), 
            "block_id": data['block_id'], 
            "track_id": data['track_id'],
            "group_id" : data['group_id'],
            "body" : audio_data
            })

    # Update the document
    jobs_db.update_one(filter, update)


asyncio.create_task(consume_job_queue())

def save_file(file):
    
    # Create a document with the file data
    metadata = {
        "size" : os.fstat(file.file.fileno()).st_size,
    }
    
    # Insert the document into the collection
    id = songs_db.put(file.file, filename=file.filename, metadata=metadata)
    # Return the file ID for reference
    return id

#Submit song
@app.post("/music", status_code = 200, tags = ["Music"], )
async def submit_song(file : UploadFile = File(...), response : Response = Response()) -> Song:
    if file.filename.endswith('.mp3'):
        id = save_file(file)
        
        return Song(music_id = str(id), name = file.filename, size=os.fstat(file.file.fileno()).st_size, time = MP3(file.file).info.length)
    
    else:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {"message": "Invalid Input"}
    

#List all songs
@app.get("/music", status_code = 200, tags = ["Music"])
async def list_songs() -> List[Song]:
    files = songs_db.find()
    response = []
    for file in files:
        # Access the file metadata
        metadata = file.metadata
        response.append(Song(music_id = str(file._id), name = file.filename, size=metadata["size"]))
        
        # Close the file
        file.close()
    
    # Return the response body
    return response

async def process_song_task(music_id, tracks, file):

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='worker_queue')

    counter = 0    
    chunk_size = 400000 # Specify the desired chunk size
    rand_hash = uuid.uuid4().hex

    while True:
        job_id = jobs_db.count_documents({})
        chunk = file.read(chunk_size)
        
        data = {
            "job_id": job_id,
            "song_id": str(music_id),
            "block_id": counter,
            "body": base64.b64encode(chunk).decode('utf-8'),
            "tracks": tracks.tracks,
            "group_id" : rand_hash
        }
        data = json.dumps(data)
        if not chunk:
            break
        # Publish the data to RabbitMQ and mongoDB
        jobs_db.insert_one({
            "job_id": job_id,
            "size": file.metadata["size"],
            "music_id": str(music_id), 
            "block_id": counter, 
            "tracks": tracks.tracks,
            "size_of_block": len(chunk),
            "status": "processing",
            "processing_time": 0,
            "group_id" : rand_hash,
            })
        channel.basic_publish(exchange='', routing_key='worker_queue', body=data)
        counter += 1
    # Close the file
    file.close()
    connection.close()

@app.post("/music/{music_id}", status_code=200, tags=["Music"])
async def process_song(music_id: str, tracks : ProcessSong, response: Response = Response()):
    try:
        file = songs_db.get(ObjectId(music_id))
    except NoFile:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"message": "Music not found"}
    
    for track in tracks.tracks:
        if track not in range(0, 4):
            response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
            return {"message": "Track not found"}
    
    asyncio.create_task(process_song_task(music_id, tracks, file))

    return {"message": "Song processing started"}

@app.get("/music/{music_id}", status_code=200, tags=["Music"])
async def get_processing_state(music_id: str, response: Response = Response()):
    try:
        file = songs_db.get(ObjectId(music_id))
    except NoFile:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"message": "Music not found"}
    
    documents = jobs_db.find({'music_id': music_id})
    req_tracks = jobs_db.find_one({'music_id': music_id}).get('tracks')
    done = jobs_db.count_documents({'music_id': music_id, 'status': 'done'})
    c = jobs_db.count_documents({'music_id': music_id})

    processing_state = int(done/c) * 100

    drums_f = []
    bass_f = []
    other_f = []
    vocals_f = []
    keys = range(4)
    my_dict = {key: 0 for key in keys}

    if processing_state == 100 :
        documents = track_db.find({'music_id': music_id}).sort('block_id', 1)
        for document in documents:
            track_id = document['track_id']
            print({
                "block_id" : document['block_id'],
                "track_id" : track_id
            })
            if track_id == 0:
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                    temp_file.write(document['body'])
                    # Get the path to the temporary file
                    drums_f.append(temp_file.name)
            elif track_id == 1 :
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                    temp_file.write(document['body'])
                    # Get the path to the temporary file
                    bass_f.append(temp_file.name)
            elif track_id == 2:
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                    temp_file.write(document['body'])
                    # Get the path to the temporary file
                    other_f.append(temp_file.name)
            elif track_id == 3:
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                    temp_file.write(document['body'])
                    # Get the path to the temporary file
                    vocals_f.append(temp_file.name)
        for track in req_tracks:
            if track == 0:
                for f in drums_f:
                    my_dict[0] += AudioSegment.from_wav(f)
            if track == 1:
                for f in bass_f:
                    my_dict[1] += AudioSegment.from_wav(f)
            if track == 2:
                for f in other_f:
                    my_dict[2] += AudioSegment.from_wav(f)
            if track == 3:
                for f in vocals_f:
                    my_dict[3] += AudioSegment.from_wav(f)
        if len(req_tracks) == 1:
            my_dict[req_tracks[0]].export(document['music_id']+'.wav', format = 'wav')
        elif len(req_tracks) == 2:
            audio = my_dict[req_tracks[0]].overlay(my_dict[req_tracks[1]], position=0)
            audio.export(document['music_id']+'.wav', format = 'wav')
        elif len(req_tracks) == 3:
            audio = my_dict[req_tracks[0]].overlay(my_dict[req_tracks[1]], position=0)
            audio = audio.overlay(my_dict[req_tracks[2]])
            audio.export(document['music_id']+'.wav', format = 'wav')
        else:
            audio = my_dict[req_tracks[0]].overlay(my_dict[req_tracks[1]], position=0)
            audio = audio.overlay(my_dict[req_tracks[2]])
            audio = audio.overlay(my_dict[req_tracks[3]])
            audio.export(document['music_id']+'.wav', format = 'wav')

    return {
        "processing_state" : int(done/c) * 100,
        "tracks" : req_tracks
    }

@app.get("/download/{music_id}", status_code=200, tags=["System"])
async def download_file(music_id : str):
    file_path = music_id+'.wav'

    return FileResponse(file_path, filename=file_path)

@app.get("/job", status_code=200, tags=["Job"])
async def list_jobs():
    documents = jobs_db.find({})
    result = []

    for document in documents:
        result.append(document["job_id"])

    return result


@app.get("/job/{job_id}", status_code=200, tags=["Job"])
async def get_job_info(job_id: int, response: Response = Response()) -> Job:
    
    document = jobs_db.find_one({"job_id": job_id})

    if document is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"message": "Job not found"}
    
    document.pop('_id', None)
    if document is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"message": "Job not found"}
    
    return document


@app.post("/reset", status_code=200, tags=["System"])
async def reboot_system():

    for filename in os.listdir('./'):
        file_path = os.path.join('./', filename)
        if os.path.isfile(file_path) and filename.endswith('.wav'):
            os.remove(file_path)

    client.drop_database('database')

    # File with the worker PIDs
    pid_file = "../worker_pids.txt"

    try:
        with open(pid_file, "r+") as file:
            # Read the lines of the file
            lines = file.readlines()
            
            # Kill the processes based on the PIDs
            for line in lines:
                pid = int(line.strip())
                os.kill(pid, 9)  # Send SIGKILL signal to terminate the process
                
        # Delete the PID file
        os.remove(pid_file)
        print("Processes killed successfully!")
    except Exception as e:
        print(f"An error occurred while killing processes: {str(e)}")


    return {"message": "System rebooted successfully"}