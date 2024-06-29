import os
import subprocess
import random
from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip, CompositeAudioClip

# Paths to your media files
intro_path = 'intro.mp4'
outro_path = 'outro.mp4'
videos_dir = './videos/'  # Directory containing your video files
songs_dir = './songs/'    # Directory containing your audio files

# Standard size for YouTube (1080p)
standard_width = 1920
standard_height = 1080

# Function to resize video using FFMPEG
def resize_video(input_video, output_video, width, height):
    command = [
        'ffmpeg', '-i', input_video,
        '-vf', f'scale={width}:{height}',
        '-c:a', 'copy',
        output_video
    ]
    subprocess.run(command, check=True)

# Function to create the final movie
def create_movie(selected_video):
    try:
        # Resize selected video
        resized_video_path = os.path.splitext(selected_video)[0] + '_resized.mp4'
        resize_video(selected_video, resized_video_path, standard_width, standard_height)
        
        # Load intro and outro clips
        intro_clip = VideoFileClip(intro_path)
        outro_clip = VideoFileClip(outro_path)
        
        # Load resized selected video clip
        resized_selected_clip = VideoFileClip(resized_video_path)
        
        # Increase the volume of the selected video clip
        resized_selected_clip = resized_selected_clip.volumex(5)  # Increase volume by 5 times
        
        # Concatenate clips
        final_clip = concatenate_videoclips([intro_clip, resized_selected_clip, outro_clip])
        
        # Add background music
        # Select a random song
        song_choices = os.listdir(songs_dir)
        selected_song = random.choice(song_choices)
        song_path = os.path.join(songs_dir, selected_song)
        
        # Load audio clip
        audio_clip = AudioFileClip(song_path)
        
        # Loop the audio clip to match the duration of the final video
        looped_audio = audio_clip.audio_loop(duration=final_clip.duration)
        
        # Adjust volume of the background music
        looped_audio = looped_audio.volumex(0.5)
        
        # Create CompositeAudioClip
        final_audio = CompositeAudioClip([final_clip.audio, looped_audio])
        
        # Set audio for the final video
        final_clip = final_clip.set_audio(final_audio)
        
        # Set the output filename
        output_filename = 'final_movie.mp4'
        
        # Write the final clip to a file
        final_clip.write_videofile(output_filename, codec='libx264', audio_codec='aac')
        
        # Close the clips to free up memory
        intro_clip.close()
        resized_selected_clip.close()
        outro_clip.close()
        final_clip.close()
        audio_clip.close()
        
        # Clean up: Delete resized video file
        os.remove(resized_video_path)
    
    except Exception as e:
        print(f"Error occurred: {e}")

# Prompt user for input
def get_user_video_choice():
    try:
        videos = os.listdir(videos_dir)
        print("Available videos:")
        for idx, video in enumerate(videos, start=1):
            print(f"{idx}. {video}")
        
        while True:
            try:
                choice = int(input("Enter the number of the video you want to use: "))
                selected_video = os.path.join(videos_dir, videos[choice - 1])
                if not os.path.isfile(selected_video):
                    raise ValueError
                break
            except (ValueError, IndexError):
                print("Invalid choice. Please enter a valid number.")
        
        return selected_video
    
    except Exception as e:
        print(f"Error occurred: {e}")
        return None

# Example usage
if __name__ == '__main__':
    try:
        # Get user's video choice
        selected_video = get_user_video_choice()
        
        if selected_video:
            # Create the movie using the selected video
            create_movie(selected_video)
        else:
            print("No valid video selected.")
    
    except Exception as e:
        print(f"Error occurred: {e}")
