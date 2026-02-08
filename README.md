# hackathon

Team Members:

1. Jemmy Qiu
2. Andrew Park
3. Devin Wang
4. Zion Picache

Purpose:
This project is a resource for users to learn or master a foreign language. This is achieved by capturing the audio of the foreign movie that the user is watching then prompting the user with a question based on what the audio interpreted and teaches the user if they make an error.

Tools Utilized:
Python: The core programming language.
OpenAI Whisper: Used for the local speech-to-text processing.
Google Gemini API: Our AI used for generating responses and prompts for user.

PyAudio and Wave: Used to capture audio from microphone streams and audio encoding.

Threading: used to allow simultaneous audio recording and API processing without UI freezing.
We use customtkinter for the UI.

Dotenv: For security for API keys and environmental variables.

Challenges and Solutions:

1. One of the problems we encountered initially was that the transcription prematurely started before the disk could capture the full audio file. To overcome this, we implemented threading and made flags to make sure the recorder and the Whisper processor did not overlap.

2. API Latency:
   One problem we had was fine tuning the duration of the audio recording because although this provided the AI with more information, it would cause longer response times making the app feel slow and in some cases errors. To solve this we optimized the Google GenAI to limit the response tokens making the feedback feel snappier and tested around the durations of the recording repeatedly to discover the sweet spot.

Public Frameworks and API Credits:

OpenAI Whisper
Google Gemini API: by Google AI Studio
PortAudio: The audio input output library by PyAudio

Project Log:
Friday
7:30 PM - 11:00 PM: Brainstorming ideas
11:00 PM - 1:00 AM: Outline project functions/plan development process
1:00 AM: Begin Checkpoint 1 (Capturing computer audio)
Saturday
11:00 AM: Testing/Debugging
2:00 PM: Begin Checkpoint 2 (Implement OpenAI Whisper API)
3:00 PM: Testing/Debugging
6:00 PM: Begin Checkpoint 3 (Implement GenAI API)
8:00 PM: Testing/Debugging
9:00 PM: Create UI/CustomTKinter
12:00 AM: Testing/Debugging and Finalize project

