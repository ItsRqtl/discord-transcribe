# Discord Transcribe

A open source python bot that transcribe voice notes to text with [OpenAI Whisper](https://github.com/openai/whisper).

## Installation

You can install all required modules/library by doing `pip install -r requirements.txt`  
You might need other requirements for [OpenAI Whisper](https://github.com/openai/whisper) if you want to run it with GPU.  
You also need to create a file `.env` under the same directory with your token in it. (`token=INSERT_YOUR_TOKEN`, check `.env.example`)

## Features

This bot has a queue system where it will transcribe the voice notes one by one.  
It also cache transcribed notes for 7 days so it doesn't have to transcribe the same voice note again.

## Usage

There is no slash commands in this bot.  
The only interactions is a message command where you right click on a message and click "Transcribe Voice Note" in the apps menu.

## License

This project is under `MIT License`. You can check the details in [LICENSE](/LICENSE).
