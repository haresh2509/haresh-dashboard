#!/usr/bin/env node

import 'dotenv/config';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import FormData from 'form-data';
import fetch from 'node-fetch';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const API_KEY = process.env.GROQ_API_KEY;
const API_URL = 'https://api.groq.com/openai/v1/audio/transcriptions';
const MODEL = 'whisper-large-v3';

async function transcribeAudio(audioPath) {
  if (!API_KEY) {
    console.error('Error: GROQ_API_KEY not found in .env file');
    process.exit(1);
  }

  const absolutePath = path.resolve(audioPath);
  
  if (!fs.existsSync(absolutePath)) {
    console.error(`Error: File not found: ${absolutePath}`);
    process.exit(1);
  }

  const form = new FormData();
  form.append('file', fs.createReadStream(absolutePath));
  form.append('model', MODEL);
  // Optional: you can add other parameters like 'language', 'prompt', 'response_format'
  // form.append('response_format', 'json'); // or 'text', 'verbose_json', 'vtt'

  try {
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${API_KEY}`,
        ...form.getHeaders(),
      },
      body: form,
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`API Error ${response.status}: ${errorText}`);
      process.exit(1);
    }

    const data = await response.json();
    console.log(data.text); // Output just the transcription text
    return data.text;
  } catch (error) {
    console.error('Transcription failed:', error.message);
    process.exit(1);
  }
}

// Main execution
const args = process.argv.slice(2);
if (args.length === 0) {
  console.error('Usage: transcribe <audio_file_path>');
  console.error('Example: transcribe ./voice-note.ogg');
  process.exit(1);
}

const audioFilePath = args[0];
transcribeAudio(audioFilePath).catch(console.error);
