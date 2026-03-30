#!/usr/bin/env node

import chokidar from 'chokidar';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Config
const SOURCE_DIR = path.join(process.env.HOME, '.openclaw', 'media', 'inbound');
const WORKSPACE_DIR = path.join(process.env.HOME, '.openclaw', 'workspace', 'telegram_media');
const PROCESSED_DIR = path.join(SOURCE_DIR, 'processed');

// Ensure destination exists
fs.mkdirSync(WORKSPACE_DIR, { recursive: true });
fs.mkdirSync(PROCESSED_DIR, { recursive: true });

// Initial scan: copy any existing files
console.log('Performing initial scan...');
const existingFiles = fs.readdirSync(SOURCE_DIR);
existingFiles.forEach(file => {
  const filePath = path.join(SOURCE_DIR, file);
  if (fs.statSync(filePath).isFile()) {
    copyFile(filePath);
  }
});

console.log(`Watching ${SOURCE_DIR} for new media...`);
console.log(`Copying to ${WORKSPACE_DIR}`);

function copyFile(filePath) {
  const filename = path.basename(filePath);
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-').split('T')[0];
  const destName = `${timestamp}_${filename}`;
  const destPath = path.join(WORKSPACE_DIR, destName);

  try {
    fs.copyFileSync(filePath, destPath);
    console.log(`Copied: ${filename} -> ${destName}`);
  } catch (err) {
    console.error(`Error copying ${filename}:`, err.message);
  }
}

// Watch for new files
const watcher = chokidar.watch(SOURCE_DIR, {
  ignored: /(^|[\/\\])\../, // ignore dotfiles
  persistent: true,
  depth: 0,
});

watcher
  .on('add', filePath => {
    console.log(`New file detected: ${path.basename(filePath)}`);
    copyFile(filePath);
  })
  .on('error', error => console.error('Watcher error:', error));

// Handle graceful shutdown
process.on('SIGINT', () => {
  console.log('\nShutting down...');
  watcher.close();
  process.exit(0);
});
