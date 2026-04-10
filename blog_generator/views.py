from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
import json
import os
import yt_dlp
from urllib.parse import urlparse, parse_qs
import assemblyai as aai
import openai
from .models import BlogPost
from dotenv import load_dotenv
import logging
import traceback
import ssl

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Fix SSL certificate issue on macOS
ssl._create_default_https_context = ssl._create_unverified_context

@login_required
def index(request):
    return render(request, 'index.html')

@csrf_exempt
@login_required
def generate_blog(request):
    try:
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                yt_link = data['link']
            except (KeyError, json.JSONDecodeError):
                return JsonResponse({'error': 'Invalid data sent'}, status=400)

            # get yt title
            title = yt_title(yt_link)

            # get transcript
            transcription = get_transcription(yt_link)
            if not transcription:
                return JsonResponse({'error': " Failed to get transcript"}, status=500)

            # use OpenAI to generate the blog
            blog_content = generate_blog_from_transcription(transcription)
            if not blog_content:
                return JsonResponse({'error': " Failed to generate blog article"}, status=500)

            # save blog article to database
            new_blog_article = BlogPost.objects.create(
                user=request.user,
                youtube_title=title,
                youtube_link=yt_link,
                generated_content=blog_content,
            )
            new_blog_article.save()

            # return blog article as a response
            return JsonResponse({'content': blog_content})
        else:
            return JsonResponse({'error': 'Invalid request method'}, status=405)
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)

def yt_title(link):
    parsed = urlparse(link)
    video_id = parse_qs(parsed.query).get('v', [None])[0]
    if not video_id:
        # handle youtu.be/VIDEO_ID short URLs
        video_id = parsed.path.lstrip('/')
    return video_id or ''

BOT_DETECTION_PHRASES = ('sign in to confirm', 'bot', 'blocked', 'captcha', 'unavailable')

def download_audio(link):
    output_template = os.path.join(settings.MEDIA_ROOT, '%(title)s.%(ext)s')
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_template,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'ffmpeg_location': os.getenv('FFMPEG_LOCATION', '/usr/bin'),
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=True)
            base = os.path.splitext(ydl.prepare_filename(info))[0]
    except yt_dlp.utils.DownloadError as e:
        msg = str(e).lower()
        if any(phrase in msg for phrase in BOT_DETECTION_PHRASES):
            raise RuntimeError(
                'YouTube is blocking this request, please try again in a few minutes or try a different video.'
            )
        raise
    return base + '.mp3'

def get_transcription(link):
    audio_file = download_audio(link)
    aai.settings.api_key = os.getenv('ASSEMBLYAI_API_KEY')
    transcript = aai.Transcriber().transcribe(audio_file)
    if transcript.status == aai.TranscriptStatus.error:
        raise RuntimeError(f"AssemblyAI transcription error: {transcript.error}")
    return transcript.text

def generate_blog_from_transcription(transcription):
    client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    prompt = f"Based on the following transcript from a YouTube video, write a comprehensive blog article, write it based on the transcript, but dont make it look like a youtube video, make it look like a proper blog article:\n\n{transcription}\n\nArticle:"

    response = client.completions.create(
        model="gpt-3.5-turbo-instruct",
        prompt=prompt,
        max_tokens=1000
    )

    generated_content = response.choices[0].text.strip()
    return generated_content

def blog_list(request):
    blog_articles = BlogPost.objects.filter(user=request.user)
    return render(request, "all-blogs.html", {'blog_articles': blog_articles})

def blog_details(request, pk):
    blog_article_detail = BlogPost.objects.get(id=pk)
    if request.user == blog_article_detail.user:
        return render(request, 'blog-details.html', {'blog_article_detail': blog_article_detail})
    else:
        return redirect('/')

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            error_message = "Invalid username or password"
            return render(request, 'login.html', {'error_message': error_message})
        
    return render(request, 'login.html')

def user_signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        repeatPassword = request.POST['repeatPassword']

        if password == repeatPassword:
            try:
                user = User.objects.create_user(username, email, password)
                user.save()
                login(request, user)
                return redirect('/')
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error('Signup failed for username "%s": %s', username, e, exc_info=True)
                error_message = f'Error creating account: {e}'
                return render(request, 'signup.html', {'error_message':error_message})
        else:
            error_message = 'Password do not match'
            return render(request, 'signup.html', {'error_message':error_message})
        
    return render(request, 'signup.html')

def user_logout(request):
    logout(request)
    return redirect('/')
