<!-- Transcribe — Sonic Architect -->
<!DOCTYPE html>

<html class="dark" lang="en"><head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>Sonic Architect | Transcribe</title>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&amp;family=Inter:wght@400;500;600&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
<script id="tailwind-config">
        tailwind.config = {
            darkMode: "class",
            theme: {
                extend: {
                    colors: {
                        "secondary": "#b7c8e1",
                        "surface-container": "#171f33",
                        "surface-container-highest": "#2d3449",
                        "on-error-container": "#ffdad6",
                        "tertiary": "#ffb869",
                        "primary": "#d0bcff",
                        "on-secondary-container": "#a9bad3",
                        "on-primary-fixed-variant": "#5516be",
                        "surface-variant": "#2d3449",
                        "surface-tint": "#d0bcff",
                        "on-tertiary-container": "#3f2300",
                        "error-container": "#93000a",
                        "on-primary-container": "#340080",
                        "on-primary-fixed": "#23005c",
                        "on-primary": "#3c0091",
                        "on-tertiary-fixed-variant": "#673d00",
                        "surface": "#0b1326",
                        "tertiary-fixed-dim": "#ffb869",
                        "tertiary-fixed": "#ffdcbb",
                        "surface-container-low": "#131b2e",
                        "on-surface-variant": "#cbc3d7",
                        "inverse-surface": "#dae2fd",
                        "background": "#0b1326",
                        "on-tertiary-fixed": "#2c1700",
                        "on-tertiary": "#482900",
                        "primary-fixed": "#e9ddff",
                        "on-secondary-fixed-variant": "#38485d",
                        "error": "#ffb4ab",
                        "surface-container-lowest": "#060e20",
                        "tertiary-container": "#ca801e",
                        "secondary-container": "#3a4a5f",
                        "inverse-primary": "#6d3bd7",
                        "on-error": "#690005",
                        "on-surface": "#dae2fd",
                        "on-secondary": "#213145",
                        "primary-container": "#a078ff",
                        "surface-bright": "#31394d",
                        "secondary-fixed": "#d3e4fe",
                        "outline": "#958ea0",
                        "on-background": "#dae2fd",
                        "inverse-on-surface": "#283044",
                        "primary-fixed-dim": "#d0bcff",
                        "outline-variant": "#494454",
                        "surface-dim": "#0b1326",
                        "secondary-fixed-dim": "#b7c8e1",
                        "on-secondary-fixed": "#0b1c30",
                        "surface-container-high": "#222a3d"
                    },
                    fontFamily: {
                        "headline": ["Manrope"],
                        "body": ["Inter"],
                        "label": ["Inter"]
                    },
                    borderRadius: { "DEFAULT": "0.25rem", "lg": "0.5rem", "xl": "0.75rem", "full": "9999px" },
                },
            },
        }
    </script>
<style>
        .material-symbols-outlined {
            font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
        }
        .glass-panel {
            background: rgba(19, 27, 46, 0.7);
            backdrop-filter: blur(20px);
        }
        .ai-glow {
            box-shadow: 0 0 15px -2px rgba(208, 188, 255, 0.3);
        }
        body {
            background-color: #0b1326;
            color: #dae2fd;
        }
    </style>
</head>
<body class="font-body selection:bg-primary-container selection:text-on-primary-container overflow-hidden">
<!-- SideNavBar (Shared Component) -->
<aside class="fixed left-0 top-0 h-full z-40 bg-slate-950/70 backdrop-blur-xl w-64 flex flex-col border-none shadow-2xl shadow-violet-900/20 font-manrope text-sm font-medium tracking-tight">
<div class="p-6">
<div class="flex items-center gap-3 mb-10">
<div class="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-primary-container flex items-center justify-center ai-glow">
<span class="material-symbols-outlined text-on-primary-container" style="font-variation-settings: 'FILL' 1;">graphic_eq</span>
</div>
<div>
<h1 class="text-lg font-bold text-violet-100 tracking-tighter">Sonic Architect</h1>
<p class="text-[10px] text-violet-400 uppercase tracking-widest font-bold">AI Audio Studio</p>
</div>
</div>
<nav class="space-y-2">
<a class="flex items-center gap-3 px-4 py-2 text-slate-400 hover:text-slate-200 transition-colors hover:bg-slate-800/40 transition-all duration-300 active:scale-95" href="#">
<span class="material-symbols-outlined" data-icon="dashboard">dashboard</span>
                    Dashboard
                </a>
<a class="flex items-center gap-3 px-4 py-2 text-violet-100 bg-violet-500/10 rounded-lg shadow-inner active:scale-95 duration-200" href="#">
<span class="material-symbols-outlined" data-icon="mic_none">mic_none</span>
                    Transcribe
                </a>
<a class="flex items-center gap-3 px-4 py-2 text-slate-400 hover:text-slate-200 transition-colors hover:bg-slate-800/40 transition-all duration-300 active:scale-95" href="#">
<span class="material-symbols-outlined" data-icon="history">history</span>
                    History
                </a>
<a class="flex items-center gap-3 px-4 py-2 text-slate-400 hover:text-slate-200 transition-colors hover:bg-slate-800/40 transition-all duration-300 active:scale-95" href="#">
<span class="material-symbols-outlined" data-icon="groups">groups</span>
                    Speakers
                </a>
<a class="flex items-center gap-3 px-4 py-2 text-slate-400 hover:text-slate-200 transition-colors hover:bg-slate-800/40 transition-all duration-300 active:scale-95" href="#">
<span class="material-symbols-outlined" data-icon="settings">settings</span>
                    Settings
                </a>
</nav>
</div>
<div class="mt-auto p-6 space-y-6">
<div class="p-4 rounded-xl bg-surface-container-high/50 border border-outline-variant/10">
<div class="flex justify-between items-center mb-2">
<span class="text-xs text-on-surface-variant">Quota: 80% used</span>
<span class="material-symbols-outlined text-violet-400 text-sm" data-icon="cloud_queue">cloud_queue</span>
</div>
<div class="h-1.5 w-full bg-surface-container-highest rounded-full overflow-hidden">
<div class="h-full w-[80%] bg-primary"></div>
</div>
</div>
<button class="w-full py-3 px-4 bg-primary text-on-primary font-bold rounded-xl active:scale-95 transition-transform">
                Upgrade Plan
            </button>
<div class="flex items-center gap-3 pt-4 border-t border-outline-variant/10">
<img alt="User Profile Avatar" class="w-8 h-8 rounded-full border border-primary/20" data-alt="Close up of a professional male user profile picture" src="https://lh3.googleusercontent.com/aida-public/AB6AXuDJ6Cb-vXaB51Yxqg-fICgx2hCSNDBWAnlx5qIOh0SKZHkxtdjfO6ICZur4smylTfRgREMbKSKXxPWDbG4CBkqMpg50YhqnZYH2q9pGyk2TYPC4bFapQcF98N6W3YXARATZYh9zHmAyh4VZOlnh22QjCLKg9E8fI5kD8NWeAju9_Sq18spffwP7fi4KeCOPaQnlHNTLgQNbg_NmDvrcQNx7FArHbm_2Ut29--ed4J0zlLbaDqhFjhFZapHuNDZIIOQ98UY8hZ0nqgM"/>
<div class="flex flex-col">
<span class="text-xs text-on-surface font-semibold">Alex Rivera</span>
<span class="text-[10px] text-on-surface-variant">Pro Architect</span>
</div>
</div>
</div>
</aside>
<!-- Main Content Shell -->
<main class="ml-64 min-h-screen flex flex-col bg-surface overflow-y-auto">
<!-- TopNavBar (Shared Component Style) -->
<header class="flex justify-between items-center w-full px-8 h-16 sticky top-0 z-30 bg-slate-950/40 backdrop-blur-md">
<div class="flex items-center gap-4">
<button class="p-2 hover:bg-white/5 rounded-full transition-all text-on-surface-variant">
<span class="material-symbols-outlined" data-icon="arrow_back">arrow_back</span>
</button>
<h2 class="text-xl font-black text-slate-100 font-manrope">New Transcription</h2>
</div>
<div class="flex items-center gap-4">
<div class="hidden md:flex items-center gap-6 px-4 py-1.5 bg-surface-container-low rounded-full">
<span class="text-slate-400 text-sm font-semibold hover:text-violet-200 cursor-pointer transition-colors">Recent</span>
<span class="text-slate-400 text-sm font-semibold hover:text-violet-200 cursor-pointer transition-colors">Pinned</span>
<span class="text-slate-400 text-sm font-semibold hover:text-violet-200 cursor-pointer transition-colors">Shared</span>
</div>
<div class="flex items-center gap-2 ml-4">
<button class="p-2 text-slate-400 hover:text-violet-200 transition-all"><span class="material-symbols-outlined">notifications</span></button>
<button class="p-2 text-slate-400 hover:text-violet-200 transition-all"><span class="material-symbols-outlined">help_outline</span></button>
</div>
</div>
</header>
<!-- Canvas Area -->
<div class="p-8 max-w-6xl mx-auto w-full space-y-8">
<!-- Bento Layout Start -->
<div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
<!-- Drop Zone (Large Column) -->
<section class="lg:col-span-2 group">
<div class="relative h-[420px] rounded-3xl border-2 border-dashed border-outline-variant/30 bg-surface-container-low/30 hover:bg-surface-container-low/50 hover:border-primary/40 transition-all duration-500 flex flex-col items-center justify-center p-12 overflow-hidden">
<!-- Abstract Background Decoration -->
<div class="absolute -top-24 -right-24 w-64 h-64 bg-primary/5 rounded-full blur-3xl group-hover:bg-primary/10 transition-colors"></div>
<div class="absolute -bottom-24 -left-24 w-64 h-64 bg-tertiary/5 rounded-full blur-3xl group-hover:bg-tertiary/10 transition-colors"></div>
<div class="w-20 h-20 rounded-2xl bg-surface-container-high flex items-center justify-center mb-6 shadow-xl border border-outline-variant/10">
<span class="material-symbols-outlined text-primary text-4xl" data-icon="upload_file">upload_file</span>
</div>
<h3 class="text-2xl font-bold font-headline text-on-surface mb-2">Architect Your Audio</h3>
<p class="text-on-surface-variant text-center max-w-sm mb-8">Drop your audio files here (mp3, wav, m4a...) or click to browse from your device.</p>
<div class="flex gap-4">
<button class="px-6 py-3 bg-primary-container text-on-primary-container font-bold rounded-xl active:scale-95 transition-all flex items-center gap-2">
<span class="material-symbols-outlined text-sm">add</span>
                                New Recording
                            </button>
<button class="px-6 py-3 bg-surface-container-highest text-on-surface font-bold rounded-xl active:scale-95 transition-all flex items-center gap-2 border border-outline-variant/20">
<span class="material-symbols-outlined text-sm">cloud_upload</span>
                                Upload Audio
                            </button>
</div>
</div>
</section>
<!-- Ongoing Tasks (Right Column) -->
<section class="lg:col-span-1 space-y-6">
<div class="flex items-center justify-between mb-2">
<h4 class="text-sm font-bold uppercase tracking-widest text-violet-400">Ongoing Tasks</h4>
<span class="px-2 py-0.5 bg-violet-500/20 text-violet-300 text-[10px] font-bold rounded uppercase">Active (1)</span>
</div>
<div class="bg-surface-container-low p-5 rounded-2xl border border-outline-variant/10 hover:border-primary/20 transition-all">
<div class="flex items-start justify-between mb-4">
<div class="flex items-center gap-3">
<div class="w-10 h-10 rounded-lg bg-surface-container-highest flex items-center justify-center">
<span class="material-symbols-outlined text-primary" data-icon="audio_file">audio_file</span>
</div>
<div>
<h5 class="text-sm font-bold text-on-surface truncate w-32">Interview_Q3_Final.wav</h5>
<p class="text-[10px] text-on-surface-variant">12.4 MB • 45:12</p>
</div>
</div>
<span class="text-xs font-bold text-primary">65%</span>
</div>
<!-- Progress Bar -->
<div class="h-2 w-full bg-surface-container-highest rounded-full overflow-hidden mb-6">
<div class="h-full w-[65%] bg-gradient-to-r from-primary to-primary-container ai-glow"></div>
</div>
<!-- Sub-steps -->
<div class="space-y-4">
<div class="flex items-center gap-3">
<span class="material-symbols-outlined text-primary text-sm" data-icon="check_circle" style="font-variation-settings: 'FILL' 1;">check_circle</span>
<span class="text-xs text-on-surface font-medium">Splitting Audio</span>
<span class="ml-auto text-[10px] text-on-surface-variant font-mono">Done</span>
</div>
<div class="flex items-center gap-3">
<div class="w-4 h-4 rounded-full border-2 border-primary border-t-transparent animate-spin"></div>
<span class="text-xs text-on-surface font-bold text-primary">Gemini Transcribing</span>
<span class="ml-auto text-[10px] text-primary font-mono font-bold">Active</span>
</div>
<div class="flex items-center gap-3 opacity-40">
<span class="material-symbols-outlined text-on-surface-variant text-sm" data-icon="radio_button_unchecked">radio_button_unchecked</span>
<span class="text-xs text-on-surface-variant font-medium">Stitching Segments</span>
<span class="ml-auto text-[10px] text-on-surface-variant font-mono">Pending</span>
</div>
</div>
</div>
<!-- Task Progress Visual Element -->
<div class="bg-gradient-to-br from-violet-600/20 to-surface-container p-6 rounded-2xl border border-violet-500/10 flex flex-col items-center text-center">
<div class="w-12 h-12 bg-white/5 rounded-full flex items-center justify-center mb-4">
<span class="material-symbols-outlined text-violet-300" data-icon="auto_awesome">auto_awesome</span>
</div>
<p class="text-xs text-on-surface-variant px-4">AI is currently enhancing speaker diarization for better accuracy.</p>
</div>
</section>
</div>
<!-- Detailed Task Progress / Status Insights -->
<section class="grid grid-cols-1 md:grid-cols-4 gap-6">
<div class="bg-surface-container-low/40 p-6 rounded-2xl">
<p class="text-[10px] font-bold text-on-surface-variant uppercase mb-2">Time Remaining</p>
<p class="text-2xl font-black text-on-surface font-manrope">~ 2m 45s</p>
</div>
<div class="bg-surface-container-low/40 p-6 rounded-2xl">
<p class="text-[10px] font-bold text-on-surface-variant uppercase mb-2">Words Detected</p>
<p class="text-2xl font-black text-on-surface font-manrope">4,812</p>
</div>
<div class="bg-surface-container-low/40 p-6 rounded-2xl">
<p class="text-[10px] font-bold text-on-surface-variant uppercase mb-2">Speakers</p>
<p class="text-2xl font-black text-on-surface font-manrope">3 Identified</p>
</div>
<div class="bg-surface-container-low/40 p-6 rounded-2xl">
<p class="text-[10px] font-bold text-on-surface-variant uppercase mb-2">Confidence Score</p>
<p class="text-2xl font-black text-tertiary font-manrope">98.4%</p>
</div>
</section>
</div>
<!-- Log Console (Collapsible Bottom) -->
<footer class="mt-auto border-t border-outline-variant/10 bg-slate-950/80 backdrop-blur-md">
<div class="flex items-center justify-between px-6 py-2">
<div class="flex items-center gap-3">
<span class="material-symbols-outlined text-xs text-primary" data-icon="terminal">terminal</span>
<span class="text-[10px] font-bold font-mono text-on-surface-variant uppercase tracking-tighter">Developer Log</span>
</div>
<div class="flex items-center gap-4">
<span class="text-[10px] font-mono text-primary/60">Live Pipeline: Active</span>
<button class="p-1 hover:bg-white/5 rounded transition-all">
<span class="material-symbols-outlined text-sm text-on-surface-variant">keyboard_arrow_up</span>
</button>
</div>
</div>
<div class="px-6 pb-4 h-24 overflow-y-auto font-mono text-[11px] space-y-1 text-on-surface-variant/70 scrollbar-hide">
<p><span class="text-primary/40">[14:20:01]</span> <span class="text-secondary">Chunk 2 uploaded successfully to Gemini-Pro-Flash...</span></p>
<p><span class="text-primary/40">[14:20:04]</span> Starting parallel processing for 4 sub-segments...</p>
<p><span class="text-primary/40">[14:20:12]</span> <span class="text-tertiary">Warning: High background noise detected in Segment 3. Increasing AI sensitivity.</span></p>
<p><span class="text-primary/40">[14:20:15]</span> Speaker 2 identified as "Interviewer A" via voice profile match.</p>
<p><span class="text-primary/40">[14:20:20]</span> Buffer stream connected. Real-time preview available.</p>
<p><span class="text-primary/40">[14:20:28]</span> Processing 65% complete. Average latency: 142ms.</p>
</div>
</footer>
</main>
</body></html>

<!-- Dashboard — Sonic Architect -->
<!DOCTYPE html>

<html class="dark" lang="en"><head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<link href="https://fonts.googleapis.com" rel="preconnect"/>
<link crossorigin="" href="https://fonts.gstatic.com" rel="preconnect"/>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&amp;family=Manrope:wght@600;700;800&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<script id="tailwind-config">
    tailwind.config = {
      darkMode: "class",
      theme: {
        extend: {
          colors: {
            "secondary": "#b7c8e1",
            "surface-container": "#171f33",
            "surface-container-highest": "#2d3449",
            "on-error-container": "#ffdad6",
            "tertiary": "#ffb869",
            "primary": "#d0bcff",
            "on-secondary-container": "#a9bad3",
            "on-primary-fixed-variant": "#5516be",
            "surface-variant": "#2d3449",
            "surface-tint": "#d0bcff",
            "on-tertiary-container": "#3f2300",
            "error-container": "#93000a",
            "on-primary-container": "#340080",
            "on-primary-fixed": "#23005c",
            "on-primary": "#3c0091",
            "on-tertiary-fixed-variant": "#673d00",
            "surface": "#0b1326",
            "tertiary-fixed-dim": "#ffb869",
            "tertiary-fixed": "#ffdcbb",
            "surface-container-low": "#131b2e",
            "on-surface-variant": "#cbc3d7",
            "inverse-surface": "#dae2fd",
            "background": "#0b1326",
            "on-tertiary-fixed": "#2c1700",
            "on-tertiary": "#482900",
            "primary-fixed": "#e9ddff",
            "on-secondary-fixed-variant": "#38485d",
            "error": "#ffb4ab",
            "surface-container-lowest": "#060e20",
            "tertiary-container": "#ca801e",
            "secondary-container": "#3a4a5f",
            "inverse-primary": "#6d3bd7",
            "on-error": "#690005",
            "on-surface": "#dae2fd",
            "on-secondary": "#213145",
            "primary-container": "#a078ff",
            "surface-bright": "#31394d",
            "secondary-fixed": "#d3e4fe",
            "outline": "#958ea0",
            "on-background": "#dae2fd",
            "inverse-on-surface": "#283044",
            "primary-fixed-dim": "#d0bcff",
            "outline-variant": "#494454",
            "surface-dim": "#0b1326",
            "secondary-fixed-dim": "#b7c8e1",
            "on-secondary-fixed": "#0b1c30",
            "surface-container-high": "#222a3d"
          },
          fontFamily: {
            "headline": ["Manrope"],
            "body": ["Inter"],
            "label": ["Inter"]
          },
          borderRadius: {"DEFAULT": "0.25rem", "lg": "0.5rem", "xl": "0.75rem", "full": "9999px"},
        },
      },
    }
  </script>
<style>
    .material-symbols-outlined {
      font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
    }
    body {
      background-color: #0b1326;
      color: #dae2fd;
      font-family: 'Inter', sans-serif;
    }
    .glass-card {
      background: rgba(34, 42, 61, 0.4);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
    }
    .ai-glow {
      box-shadow: 0 0 20px rgba(208, 188, 255, 0.15);
    }
  </style>
</head>
<body class="overflow-hidden">
<!-- SideNavBar Shell -->
<aside class="fixed left-0 top-0 h-full z-40 bg-slate-950/70 backdrop-blur-xl h-screen w-64 flex flex-col border-none shadow-2xl shadow-violet-900/20 font-manrope text-sm font-medium tracking-tight">
<div class="p-6">
<div class="flex items-center gap-3 mb-10">
<div class="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-primary-container flex items-center justify-center text-on-primary-container shadow-lg">
<span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1;">architecture</span>
</div>
<div>
<h1 class="text-lg font-bold text-violet-100 tracking-tighter">Sonic Architect</h1>
<p class="text-[10px] text-slate-500 uppercase tracking-widest font-bold">AI Audio Studio</p>
</div>
</div>
<nav class="space-y-2">
<a class="flex items-center gap-3 px-4 py-2 text-violet-100 bg-violet-500/10 rounded-lg shadow-inner" href="#">
<span class="material-symbols-outlined text-violet-400">dashboard</span>
<span>Dashboard</span>
</a>
<a class="flex items-center gap-3 px-4 py-2 text-slate-400 hover:text-slate-200 transition-colors hover:bg-slate-800/40 rounded-lg transition-all duration-300 active:scale-95 duration-200" href="#">
<span class="material-symbols-outlined">mic_none</span>
<span>Transcribe</span>
</a>
<a class="flex items-center gap-3 px-4 py-2 text-slate-400 hover:text-slate-200 transition-colors hover:bg-slate-800/40 rounded-lg transition-all duration-300 active:scale-95 duration-200" href="#">
<span class="material-symbols-outlined">history</span>
<span>History</span>
</a>
<a class="flex items-center gap-3 px-4 py-2 text-slate-400 hover:text-slate-200 transition-colors hover:bg-slate-800/40 rounded-lg transition-all duration-300 active:scale-95 duration-200" href="#">
<span class="material-symbols-outlined">groups</span>
<span>Speakers</span>
</a>
<a class="flex items-center gap-3 px-4 py-2 text-slate-400 hover:text-slate-200 transition-colors hover:bg-slate-800/40 rounded-lg transition-all duration-300 active:scale-95 duration-200" href="#">
<span class="material-symbols-outlined">settings</span>
<span>Settings</span>
</a>
</nav>
</div>
<div class="mt-auto p-6 space-y-4">
<div class="bg-slate-900/50 rounded-xl p-4 border border-outline-variant/10">
<div class="flex items-center gap-2 text-violet-300 mb-2">
<span class="material-symbols-outlined text-sm">cloud_queue</span>
<span class="text-xs font-semibold">Quota: 80% used</span>
</div>
<div class="w-full bg-surface-container-highest h-1.5 rounded-full overflow-hidden">
<div class="bg-gradient-to-r from-primary to-primary-container h-full w-[80%] rounded-full shadow-[0_0_8px_rgba(208,188,255,0.5)]"></div>
</div>
<p class="text-[10px] text-slate-500 mt-2">124/300 min used this month</p>
</div>
<button class="w-full py-2.5 bg-primary text-on-primary font-bold rounded-xl text-xs hover:bg-primary-fixed-dim transition-all active:scale-95">
        Upgrade Plan
      </button>
<div class="flex items-center gap-3 pt-4 border-t border-outline-variant/10">
<img alt="User Profile Avatar" class="w-8 h-8 rounded-full bg-surface-container-high" src="https://lh3.googleusercontent.com/aida-public/AB6AXuBRtEbAYIMCZkdabDutlNish40hFPxIYW093lcfoQZPVlBa_zVujAqBl--Ke9-ewUDzIebHuGpfnyLvDPeO32bwQffKYzusXylzXaNQvwd4mxnxuQo88Mw6kF0ZU5pg3NqEkARqsWcnzb_XObctAWUIyqKKg6zUxvW2B02DS-uyWvVhCce8cA-dNwhNsA526SOqJ2oxHgKDPAxQu_00dRk5ZIgbkC7Ibe0qI-zaWDD6CSrUVhI9j3C5XulKA1YMPMposmIZey_GVDQ"/>
<div class="overflow-hidden">
<p class="text-xs font-bold text-slate-200 truncate">Designer Alex</p>
<p class="text-[10px] text-slate-500 truncate">alex@architect.ai</p>
</div>
</div>
</div>
</aside>
<!-- TopNavBar Shell -->
<header class="fixed top-0 right-0 h-16 bg-slate-950/40 backdrop-blur-md flex justify-between items-center px-8 ml-64 max-w-[calc(100%-16rem)] w-full z-30 font-manrope font-semibold tracking-wide">
<div class="flex items-center gap-8">
<div class="flex gap-6 text-sm">
<a class="text-violet-300 border-b-2 border-violet-500 pb-1" href="#">Recent</a>
<a class="text-slate-400 hover:text-violet-200 hover:bg-white/5 rounded-md px-2 py-1 transition-all" href="#">Pinned</a>
<a class="text-slate-400 hover:text-violet-200 hover:bg-white/5 rounded-md px-2 py-1 transition-all" href="#">Shared</a>
</div>
</div>
<div class="flex items-center gap-6">
<div class="relative focus-within:ring-1 focus-within:ring-violet-500/30 rounded-full transition-all">
<span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 text-lg">search</span>
<input class="bg-surface-container-low border-none rounded-full py-1.5 pl-10 pr-4 text-xs w-64 focus:ring-0 text-slate-200 placeholder:text-slate-600" placeholder="Search archives..." type="text"/>
</div>
<div class="flex items-center gap-3">
<button class="p-2 text-slate-400 hover:text-violet-200 transition-colors">
<span class="material-symbols-outlined">notifications</span>
</button>
<button class="p-2 text-slate-400 hover:text-violet-200 transition-colors">
<span class="material-symbols-outlined">help_outline</span>
</button>
<div class="h-8 w-[1px] bg-gradient-to-b from-transparent via-slate-800/40 to-transparent"></div>
<img alt="User Status Active" class="w-8 h-8 rounded-full ring-2 ring-primary/20" src="https://lh3.googleusercontent.com/aida-public/AB6AXuCifIvrHHmmdi-3UGwrWI4Ol33anNQ8iq28gCpZJ4BhQL5liy9lSdRpoyomlOE4KcoIScuTgeoCnfu0Yq_mrONSiLW7NnlHFqlsWZHY4cD7zqxdW661UBjwVHYOx9RPMm6YTwdz_VOd1ExoHVeb3Fxb9Xe18TjEttCrG9yAQ9poTcOuHY1PugaBRaERxVVdCDlWRxrkT6VdrHMEWfR3K35PmQw3Gx1YfhbE8nLdMC8m21qJ2RjWiLWhrsU7r5rjkQU6thapCSX_1pY"/>
</div>
</div>
</header>
<!-- Main Canvas -->
<main class="ml-64 mt-16 p-8 h-[calc(100vh-4rem)] overflow-y-auto bg-background">
<!-- Welcome Banner Section -->
<section class="mb-10">
<div class="relative overflow-hidden rounded-3xl p-8 bg-gradient-to-br from-surface-container-low to-surface-container shadow-xl">
<div class="absolute top-0 right-0 w-64 h-64 bg-primary/10 blur-[80px] -mr-32 -mt-32 rounded-full"></div>
<div class="relative z-10">
<h2 class="text-3xl font-headline font-extrabold text-slate-100 tracking-tight mb-2">Good morning, Designer.</h2>
<p class="text-lg text-on-surface-variant font-medium">You have <span class="text-primary">3 transcripts</span> ready for review.</p>
</div>
</div>
</section>
<!-- Quick Action Bento Grid -->
<section class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
<!-- New Recording Action -->
<button class="group relative flex flex-col items-start p-6 rounded-3xl bg-surface-container-low hover:bg-surface-container-high transition-all duration-300 text-left">
<div class="mb-8 p-3 rounded-2xl bg-primary/10 text-primary group-hover:bg-primary group-hover:text-on-primary transition-colors">
<span class="material-symbols-outlined text-3xl">mic</span>
</div>
<h3 class="text-xl font-headline font-bold text-slate-100 mb-1">New Recording</h3>
<p class="text-sm text-slate-500">Capture crystal clear audio with AI isolation.</p>
<div class="mt-6 flex gap-1 items-end h-8">
<div class="w-1 bg-primary/20 rounded-full h-1/2 group-hover:animate-pulse"></div>
<div class="w-1 bg-primary/40 rounded-full h-3/4"></div>
<div class="w-1 bg-primary/60 rounded-full h-full"></div>
<div class="w-1 bg-primary/40 rounded-full h-2/3"></div>
<div class="w-1 bg-primary/20 rounded-full h-1/3"></div>
</div>
</button>
<!-- Upload Action -->
<button class="group relative flex flex-col items-start p-6 rounded-3xl bg-surface-container-low hover:bg-surface-container-high transition-all duration-300 text-left">
<div class="mb-8 p-3 rounded-2xl bg-secondary-container text-secondary group-hover:bg-secondary group-hover:text-on-secondary transition-colors">
<span class="material-symbols-outlined text-3xl">upload_file</span>
</div>
<h3 class="text-xl font-headline font-bold text-slate-100 mb-1">Upload Audio</h3>
<p class="text-sm text-slate-500">Import WAV, MP3, or M4A for processing.</p>
<div class="mt-8 text-xs font-bold text-secondary uppercase tracking-widest opacity-0 group-hover:opacity-100 transition-opacity">
            Drag &amp; Drop enabled
        </div>
</button>
<!-- Stats Card -->
<div class="p-6 rounded-3xl bg-gradient-to-br from-tertiary-container/20 to-surface-container-low border border-tertiary-container/10 flex flex-col justify-between">
<div class="flex justify-between items-start">
<span class="material-symbols-outlined text-tertiary text-3xl">insights</span>
<span class="px-2 py-1 rounded-lg bg-tertiary/10 text-tertiary text-[10px] font-bold uppercase tracking-tighter">Live Insight</span>
</div>
<div>
<h4 class="text-sm font-semibold text-slate-400 mb-1">Total Accuracy</h4>
<div class="flex items-baseline gap-2">
<span class="text-4xl font-headline font-black text-slate-100 tracking-tighter">98.4%</span>
<span class="text-xs text-emerald-400 font-bold">+1.2%</span>
</div>
</div>
</div>
</section>
<!-- Recent Transcripts List -->
<section>
<div class="flex items-center justify-between mb-8">
<h3 class="text-xl font-headline font-bold text-slate-100">Recent Transcripts</h3>
<button class="text-sm font-bold text-primary hover:text-primary-fixed-dim transition-colors">View All Archive</button>
</div>
<div class="space-y-4">
<!-- Transcript Item 1 -->
<div class="glass-card p-5 rounded-2xl flex items-center justify-between group cursor-pointer hover:bg-surface-container-high transition-all">
<div class="flex items-center gap-5">
<div class="w-12 h-12 rounded-xl bg-surface-container-highest flex items-center justify-center text-violet-400 group-hover:scale-110 transition-transform">
<span class="material-symbols-outlined">description</span>
</div>
<div>
<h4 class="font-headline font-bold text-slate-100 text-base">Keynote_Interview_Final.wav</h4>
<div class="flex items-center gap-4 mt-1">
<span class="label-sm text-slate-500 flex items-center gap-1">
<span class="material-symbols-outlined text-xs">schedule</span> 42:15
                </span>
<span class="label-sm text-slate-500 flex items-center gap-1">
<span class="material-symbols-outlined text-xs">calendar_today</span> Oct 24, 2023
                </span>
</div>
</div>
</div>
<div class="flex items-center gap-6">
<div class="flex -space-x-2">
<img alt="Speaker 1" class="w-7 h-7 rounded-full border-2 border-surface bg-surface-container-high" data-alt="User avatar placeholder" src="https://lh3.googleusercontent.com/aida-public/AB6AXuDjqYacYpj5GOxn4Pu8j64YBHMLEZE5qBMW5A43phskhMG5ZrnQWmI550swU0_R2-Ar13BGBQFG5IafyHKu30H2wh9Yq4KuGwtOvgtKhOeNs3LQTZa-NlDTbm98vtAi_oE9FWYQvQrMsqcaZ1sg2jOuetYzIYDMXbBvAQ4JxDHR4y5GEePGIEPshD3uQ4uc0SCtLkhUH233_LbuRoD-0iNpweZTB94SY8cibVX2tx6y_Z8X5s-fOBfcN7mxtMFUCWNoVBrql17MuaM"/>
<img alt="Speaker 2" class="w-7 h-7 rounded-full border-2 border-surface bg-surface-container-high" data-alt="User avatar placeholder" src="https://lh3.googleusercontent.com/aida-public/AB6AXuBeUn3WbItM-liQmg9P4R1HMs1TJyTlXE0jJF2gYkBhiQCLC_HFzosIf0JIHcpFddoH-D2oaO0--LqCBmX3_81VdzFnlLYpEqD1xgnkgP6YwirDRqqGZcLaiuN36gJXPu-StMv1UffWxg6ZytjJtKtXyrEHCJFgJU2FEDw828kWaXQCz9IoeSm4cn90sDJAR_CLK9Z85oJRJY2ozhyCbv06j1NcOTbSJPoa5F3oxXHBMqilfRo5v5rO8_eMLXU7DFZHuFSwWNSqtEg"/>
<img alt="Speaker 3" class="w-7 h-7 rounded-full border-2 border-surface bg-surface-container-high" data-alt="User avatar placeholder" src="https://lh3.googleusercontent.com/aida-public/AB6AXuBWgY4-kYIE06d4lz1yIC7qw6Jwr5BnWzGukGU79j-1plk5RqQPsoAfepZHIpwx90DncuSK_9he0aFtQWKLWy3BNXJatDH_H000XGnYVA9nap-wgI_uQlPRdxhlsyZNklKyAtkmiL8vURs9otbEAJ3Kwa_nYqCaeLgdi98ykeu1qMm3qxU1yhQimyJ2jEctwFumSuYTwqX3o1XXYfpBRLsVCdBmLgIKiTscb7td9lQNCY-HYIvYm0LUXO4R3tTzyxC206l6HfoDEDM"/>
</div>
<span class="px-3 py-1 rounded-full bg-violet-500/10 text-violet-300 text-[10px] font-bold uppercase tracking-widest border border-violet-500/20">3 Speakers</span>
<button class="p-2 rounded-full hover:bg-white/5 text-slate-500 hover:text-slate-200 transition-all">
<span class="material-symbols-outlined">more_vert</span>
</button>
</div>
</div>
<!-- Transcript Item 2 -->
<div class="glass-card p-5 rounded-2xl flex items-center justify-between group cursor-pointer hover:bg-surface-container-high transition-all">
<div class="flex items-center gap-5">
<div class="w-12 h-12 rounded-xl bg-surface-container-highest flex items-center justify-center text-violet-400 group-hover:scale-110 transition-transform">
<span class="material-symbols-outlined">music_note</span>
</div>
<div>
<h4 class="font-headline font-bold text-slate-100 text-base">Studio_Jam_Session_004.mp3</h4>
<div class="flex items-center gap-4 mt-1">
<span class="label-sm text-slate-500 flex items-center gap-1">
<span class="material-symbols-outlined text-xs">schedule</span> 15:30
                </span>
<span class="label-sm text-slate-500 flex items-center gap-1">
<span class="material-symbols-outlined text-xs">calendar_today</span> Oct 23, 2023
                </span>
</div>
</div>
</div>
<div class="flex items-center gap-6">
<div class="flex -space-x-2">
<img alt="Speaker 4" class="w-7 h-7 rounded-full border-2 border-surface bg-surface-container-high" data-alt="User avatar placeholder" src="https://lh3.googleusercontent.com/aida-public/AB6AXuBE6p6as_QhcGkxCSkO3y8V-W6Y6UC8Jhpp28h0JLU1J7xsMi7Yx1vWE447vtgassXLDQk1CsL332BZrABCqeZBHwqxrqau8Zl4JqxMD1exn2O96vJqyyQJZwvLkNQgZhgPoYbIg0ymVhbPYQ3m3MHxvfkgVu_tiB7-IWTlq3vP6PFt-oobcFxIV8w0oZ6Rku3zZa_EoTxRph-e4jlfK7fNDtIkAeyPbuPp8iX4FGq5cuzjfHl2ccISzUDhLI-C_JPOZP2Iq4lIpOc"/>
</div>
<span class="px-3 py-1 rounded-full bg-slate-800 text-slate-400 text-[10px] font-bold uppercase tracking-widest border border-outline-variant/10">Solo Session</span>
<button class="p-2 rounded-full hover:bg-white/5 text-slate-500 hover:text-slate-200 transition-all">
<span class="material-symbols-outlined">more_vert</span>
</button>
</div>
</div>
<!-- Transcript Item 3 -->
<div class="glass-card p-5 rounded-2xl flex items-center justify-between group cursor-pointer hover:bg-surface-container-high transition-all">
<div class="flex items-center gap-5">
<div class="w-12 h-12 rounded-xl bg-surface-container-highest flex items-center justify-center text-violet-400 group-hover:scale-110 transition-transform">
<span class="material-symbols-outlined">mic_external_on</span>
</div>
<div>
<h4 class="font-headline font-bold text-slate-100 text-base">Brainstorming_Workshop.m4a</h4>
<div class="flex items-center gap-4 mt-1">
<span class="label-sm text-slate-500 flex items-center gap-1">
<span class="material-symbols-outlined text-xs">schedule</span> 128:05
                </span>
<span class="label-sm text-slate-500 flex items-center gap-1">
<span class="material-symbols-outlined text-xs">calendar_today</span> Oct 21, 2023
                </span>
</div>
</div>
</div>
<div class="flex items-center gap-6">
<div class="flex -space-x-2">
<img alt="Avatar A" class="w-7 h-7 rounded-full border-2 border-surface bg-surface-container-high" data-alt="User avatar placeholder" src="https://lh3.googleusercontent.com/aida-public/AB6AXuBi6CSqhsIj5VjQmBGy2Nqw_fKXsSvu9bOCzYbAhcYR_w9zcorQAJRNBgSFXdD3y8jVs9heXDEOZZ-AZB4UXnCfUyCV2-bq6upnqqPkgrTa6B0Et5pPvJmK7biPmuqS2m8hNIX-0nB4xSdiwkcdT4L4GDA8j8eRMXnZfyW-XPYfT6OMMZEsr9m1KfUof0xJT_-t3XJdsyu1Dy9nhZQ15yJDYJTX2ZYrwgzPOhUG4DSJBXrJCGSYi_tM0WMEdz7jmLRyQfoE8QTMe2I"/>
<img alt="Avatar B" class="w-7 h-7 rounded-full border-2 border-surface bg-surface-container-high" data-alt="User avatar placeholder" src="https://lh3.googleusercontent.com/aida-public/AB6AXuBErTaT187NwnVRN9eQ0_lo3JFTZNMen4wsvfLDSzmASrdArvibG4miLiw0OthjTJd8gdQc89wLXFP5IIFqpQlPkQF15Dm1Yn7r2dH41owxHsQzvyzM0KfXL0VbcEouy-rHZGulr3Ttg69wnZiCzMFI3-Dmnkq04_zYqfr2c8Of9-8g91pZ51I28tqA7hAnTEI2TIgTTuDrUa3_Fa762LayU8ohvDG_TkO5TC94ReUlT5smA55AhlZN6AP2iDEVJrCy3TET9M8-7EI"/>
<img alt="Avatar C" class="w-7 h-7 rounded-full border-2 border-surface bg-surface-container-high" data-alt="User avatar placeholder" src="https://lh3.googleusercontent.com/aida-public/AB6AXuDy1eyVC52N801UD2rjsyYFpHvXL24etdwUhaGJvn6RkTKV8GebMvL_J2WTv3dG8FxYb9SD-6LvJRygZX9orSyMCauhgpcz8wFZG9K1GPnYdzx-AqrTVYziSHAWaCzhQyGjqeLbyMkTJv3G75skUZtuBCUycEF1r_nydO2ZHcTG7zVtwow2kBJbNaT3hfWw6_suDMrKaDsffiXI-oSiYxhunVZUQ5aqGEv3CZqTUPNyT00538xozgumdYOjR9mzYVD_wcRz6kCu1pI"/>
<img alt="Avatar D" class="w-7 h-7 rounded-full border-2 border-surface bg-surface-container-high" data-alt="User avatar placeholder" src="https://lh3.googleusercontent.com/aida-public/AB6AXuCrfr0oT2cFTlfSf9OD9fLNpsVl7zSgON7CsWJFZZ-WmHpAR2tRyiVOjOaOGK97J-00ZlifhwzuGlC9FeyRmcJ8jA_-vYW2lkdJznqI1ngDzrpRch2ztsf4pxvuTWLSQ_6R1RJKY2uSXPel39JRn79KgkcvLZuAPs2pEoLsGbCNMMjLBAL-ZFH4rNetl21Y2uDbC_XJBmkSQF_9le7XCm_sxm5k00rpVKjm9r2KsWdkou89jAnfw9jLUIndKLfJak6I1K9yTVzw7vY"/>
</div>
<span class="px-3 py-1 rounded-full bg-violet-500/10 text-violet-300 text-[10px] font-bold uppercase tracking-widest border border-violet-500/20">5+ Speakers</span>
<button class="p-2 rounded-full hover:bg-white/5 text-slate-500 hover:text-slate-200 transition-all">
<span class="material-symbols-outlined">more_vert</span>
</button>
</div>
</div>
</div>
</section>
</main>
<!-- Contextual FAB (Hidden on Dashboard as per rules, but included if primary action is needed) -->
<!-- Note: FAB suppressed on dashboard to prioritize the Bento Grid actions -->
</body></html>