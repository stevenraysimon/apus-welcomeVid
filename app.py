from flask import Flask, request, send_file, render_template, jsonify
import os
import subprocess
import random
from moviepy.editor import *
import tempfile
import json
import time
import threading

app = Flask(__name__)

# Paths to your media files
intro_path = 'intro.mp4'
outro_path = 'outro.mp4'
songs_dir = './songs/'  # Directory containing your audio files

# Standard size for YouTube (1080p)
standard_width = 1920
standard_height = 1080

# Function to resize video using FFMPEG
def resize_video(input_video, output_video, width, height):
    command = [
        'ffmpeg', '-y',  # The -y option forces overwrite of output files without prompting
        '-i', input_video,
        '-vf', f'scale={width}:{height}',
        '-c:a', 'copy',
        output_video
    ]
    subprocess.run(command, check=True)

def create_movie(selected_video_path, overlay_text, output_filename):
    try:
        # Create a temporary file for the final video
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_output_file:
            temp_output_path = temp_output_file.name

        # Resize selected video
        with tempfile.NamedTemporaryFile(delete=False, suffix='_resized.mp4') as temp_resized_file:
            resized_video_path = temp_resized_file.name
            resize_video(selected_video_path, resized_video_path, standard_width, standard_height)
        
        # Load intro and outro clips
        intro_clip = VideoFileClip(intro_path)
        outro_clip = VideoFileClip(outro_path)
        
        # Load resized selected video clip
        resized_selected_clip = VideoFileClip(resized_video_path)
        
        # Increase the volume of the selected video clip
        resized_selected_clip = resized_selected_clip.volumex(5)  # Increase volume by 5 times
        
        # Generate a text clip with user input
        txt_clip = TextClip(overlay_text, fontsize=75, color='white', font='Arial')
        # Calculate padding
        padding_y = 60
        # Position the text at the bottom center
        txt_clip = txt_clip.set_pos(lambda t: ('center', resized_selected_clip.h - txt_clip.h - padding_y)).set_duration(resized_selected_clip.duration)

        # Apply fade-in after 2 seconds and fade-out after 5 seconds
        fadein_duration = 1  # Duration of the fade-in effect
        fadeout_duration = 1  # Duration of the fade-out effect
        display_duration = 5  # Total duration for which the text should be visible

        # Set the start time and duration for the text clip
        txt_clip = txt_clip.set_start(2).set_duration(display_duration + fadein_duration + fadeout_duration)

        # Apply the fade-in and fade-out effects
        txt_clip = txt_clip.crossfadein(fadein_duration).crossfadeout(fadeout_duration)

        # Overlay the text clip on the resized selected video
        video_with_text = CompositeVideoClip([resized_selected_clip, txt_clip])
        
        # Concatenate clips
        final_clip = concatenate_videoclips([intro_clip, video_with_text, outro_clip])
        
        # Add background music
        song_choices = os.listdir(songs_dir)
        selected_song = random.choice(song_choices)
        song_path = os.path.join(songs_dir, selected_song)
        
        # Load audio clip
        audio_clip = AudioFileClip(song_path)
        
        # Loop the audio clip to match the duration of the final video
        looped_audio = audio_clip.audio_loop(duration=final_clip.duration)
        
        # Adjust volume of the background music
        looped_audio = looped_audio.volumex(0.5)
        
        # Apply fade out to the last 2 seconds of the background music
        fade_duration = 2
        looped_audio = looped_audio.audio_fadeout(fade_duration)
        
        # Create CompositeAudioClip
        final_audio = CompositeAudioClip([final_clip.audio, looped_audio])
        
        # Set audio for the final video
        final_clip = final_clip.set_audio(final_audio)

        # Define a simulated progress function
        def simulated_progress():
            for progress in range(0, 101, 10):  # Simulate progress from 0% to 100% in steps of 10%
                with open('progress.json', 'w') as f:
                    json.dump({'progress': progress}, f)
                time.sleep(0.05)  # Simulate time taken for each progress step

        # Run the simulated progress in a separate thread
        progress_thread = threading.Thread(target=simulated_progress)
        progress_thread.start()

        # Write the final clip to the user-specified filename
        final_clip.write_videofile(temp_output_path, codec='libx264', audio_codec='aac')

        # Wait for the progress thread to finish
        progress_thread.join()
        
        # Close the clips to free up memory
        intro_clip.close()
        resized_selected_clip.close()
        outro_clip.close()
        video_with_text.close()
        final_clip.close()
        audio_clip.close()
        
        # Clean up: Delete resized video file
        os.remove(resized_video_path)

        return temp_output_path

    except Exception as e:
        print(f"Error occurred: {e}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/progress')
def get_progress():
    try:
        with open('progress.json') as f:
            progress = json.load(f)
        return jsonify(progress)
    except Exception as e:
        return jsonify({"error": "Could not get progress"}), 500


@app.route('/upload', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({"error": "No video file provided"}), 400

    video_file = request.files['video']
    if video_file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    # Clear previous progress
    if os.path.exists('progress.json'):
        os.remove('progress.json')

    # Save the uploaded file to a temporary location
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video_file:
        video_path = temp_video_file.name
        video_file.save(video_path)

    # Get the text input
    overlay_text = request.form.get('text', 'Default Text')
    
    # Get the desired filename for the processed video
    output_filename = request.form.get('filename', 'final_movie.mp4')
    output_filename = output_filename if output_filename.endswith('.mp4') else output_filename + '.mp4'

    # Process the video
    processed_video_path = create_movie(video_path, overlay_text, output_filename)
    
    if processed_video_path:
        response = send_file(processed_video_path, as_attachment=True, download_name=output_filename)
        
        # Clean up: Delete the temporary processed video file after sending
        os.remove(processed_video_path)
        
        return response
    else:
        return jsonify({"error": "Failed to process video"}), 500

if __name__ == '__main__':
    app.run(debug=True)