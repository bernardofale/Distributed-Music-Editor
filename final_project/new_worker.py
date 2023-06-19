#!/usr/bin/env python

import argparse
import pika, sys, os
from demucs.apply import apply_model
from demucs.pretrained import get_model
from demucs.audio import AudioFile, save_audio
import base64
import json
import tempfile
import time

# limit the number of thread used by pytorch
import torch
torch.set_num_threads(1)

def main(args):
    
    output_folder = 'worker_' + str(args.i)
    if not os.path.exists(output_folder):
        # Create the folder
        os.makedirs(output_folder)
        print(f"Folder '{output_folder}' created successfully.")
    else:
        print(f"Folder '{output_folder}' already exists.")
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    channel.queue_declare(queue='worker_queue')
    channel.queue_declare(queue='job_queue')

    def callback(ch, method, properties, body):
        print(" [x] Received ")
        data = json.loads(body.decode('utf-8'))

        job_id = data['job_id']
        audio_data = base64.b64decode(data['body'])
        requested_ids = data['tracks']
        song_id = data['song_id']
        block_id = data['block_id']
        group_id = data['group_id']
        # Create a temporary file to save the byte stream
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
            temp_file.write(audio_data)
            # Get the path to the temporary file
            file_path = temp_file.name
            
        process(file_path, job_id, block_id, requested_ids, song_id, channel, group_id)
        
        ch.basic_ack(delivery_tag = method.delivery_tag)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='worker_queue', on_message_callback=callback)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

def process(file_path, job_id, block_id, requested_ids, song_id, channel, group_id):
        start = time.time()
        # get the model
        model = get_model(name='htdemucs')
        model.cpu()
        model.eval()

        # load the audio file
        wav = AudioFile(file_path).read(streams=0,
        samplerate=model.samplerate, channels=model.audio_channels)
        ref = wav.mean(0)
        wav = (wav - ref.mean()) / ref.std()
            # apply the model
        sources = apply_model(model, wav[None], device='cpu', progress=True, num_workers=1)[0]
        sources = sources * ref.std() + ref.mean()
        end = time.time()
        processing_time = end - start
        # store the model
        for index, (source, name) in enumerate(zip(sources, model.sources)):
            #Only save the requested tracks
            if index in requested_ids:
                # Create a temporary file to save the byte stream
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                    save_audio(source, temp_file.name, samplerate=model.samplerate)
                    # Get the path to the temporary file
                    temp_file_path = temp_file.name
                with open(temp_file_path, 'rb') as wav_file:
                    chunk = wav_file.read()
                data = {
                    "job_id": job_id,
                    "song_id": str(song_id),
                    "block_id": block_id,
                    "body": base64.b64encode(chunk).decode('utf-8'),
                    "track_id": index,
                    "processing_time": processing_time,
                    "group_id": group_id
                }
                data = json.dumps(data)
                channel.basic_publish(exchange='', routing_key='job_queue', body=data)
                os.remove(temp_file_path)
        os.remove(file_path)
        print(" [x] Done")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Split an audio track', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', type = int, help = 'worker identification') 
    parser.add_argument('-s', type = str, help = 'Song storage folder')
    parser.add_argument('-o', type=str, help='output folder', default='tracks')

    args = parser.parse_args()

    try:
        main(args)
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)