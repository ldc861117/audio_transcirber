#!/usr/bin/env node
/**
 * Patches the dev Electron.app's Info.plist with required usage descriptions.
 * Runs as a postinstall script so permissions work during development.
 */
const fs = require('fs');
const path = require('path');

const plistPath = path.join(
  __dirname, '..', 'node_modules', 'electron', 'dist',
  'Electron.app', 'Contents', 'Info.plist'
);

if (!fs.existsSync(plistPath)) {
  console.log('[patch-plist] Electron.app not found, skipping.');
  process.exit(0);
}

let plist = fs.readFileSync(plistPath, 'utf8');

const entries = {
  NSAudioCaptureUsageDescription:
    'Audio Transcriber needs audio capture for system audio recording.',
  NSScreenCaptureUsageDescription:
    'Audio Transcriber needs screen capture for system audio recording.',
  NSMicrophoneUsageDescription:
    'Audio Transcriber needs microphone access to record audio.',
};

let patched = false;
for (const [key, value] of Object.entries(entries)) {
  if (!plist.includes(`<key>${key}</key>`)) {
    // Insert before the closing </dict>
    const insertion = `\t<key>${key}</key>\n\t<string>${value}</string>\n`;
    plist = plist.replace('</dict>', insertion + '</dict>');
    console.log(`[patch-plist] Added ${key}`);
    patched = true;
  } else {
    console.log(`[patch-plist] ${key} already present, skipping.`);
  }
}

if (patched) {
  fs.writeFileSync(plistPath, plist, 'utf8');
  console.log('[patch-plist] Info.plist patched successfully.');
} else {
  console.log('[patch-plist] No changes needed.');
}
