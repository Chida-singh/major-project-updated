async function postJson(url, body) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  let data;
  try {
    data = await res.json();
  } catch {
    data = null;
  }

  if (!res.ok) {
    const msg = data && data.detail ? data.detail : `HTTP ${res.status}`;
    throw new Error(msg);
  }

  return data;
}

function setStatus(el, text) {
  el.textContent = text;
}

function setStatusOk(el, text) {
  el.textContent = text;
  el.classList.remove('error');
}

function setStatusError(el, text) {
  el.textContent = text;
  el.classList.add('error');
}

function clearCanvas(ctx, w, h) {
  ctx.clearRect(0, 0, w, h);
  ctx.fillStyle = '#0b1020';
  ctx.fillRect(0, 0, w, h);
}

function resizeCanvasToDisplaySize(canvas, ctx) {
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  const cssWidth = Math.max(1, Math.round(rect.width));
  const cssHeight = Math.max(1, Math.round(rect.height));

  const targetWidth = Math.max(1, Math.round(cssWidth * dpr));
  const targetHeight = Math.max(1, Math.round(cssHeight * dpr));

  if (canvas.width !== targetWidth || canvas.height !== targetHeight) {
    canvas.width = targetWidth;
    canvas.height = targetHeight;
  }

  // Draw in CSS pixels.
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  return { cssWidth, cssHeight };
}

function drawFramePoints(ctx, frameXY, w, h) {
  // frameXY: [ [x,y], ... ] with values in image space as extracted.
  // For the demo we auto-normalize to canvas bounds based on min/max.
  let minX = Infinity,
    minY = Infinity,
    maxX = -Infinity,
    maxY = -Infinity;

  for (const [x, y] of frameXY) {
    if (x < minX) minX = x;
    if (y < minY) minY = y;
    if (x > maxX) maxX = x;
    if (y > maxY) maxY = y;
  }

  const pad = 0.05;
  const rangeX = Math.max(1e-6, maxX - minX);
  const rangeY = Math.max(1e-6, maxY - minY);

  ctx.fillStyle = '#e5e7eb';

  for (const [x, y] of frameXY) {
    const nx = (x - minX) / rangeX;
    const ny = (y - minY) / rangeY;

    const px = (pad + nx * (1 - 2 * pad)) * w;
    const py = (pad + ny * (1 - 2 * pad)) * h;

    ctx.beginPath();
    ctx.arc(px, py, 1.4, 0, Math.PI * 2);
    ctx.fill();
  }
}

async function main() {
  const ytUrl = document.getElementById('ytUrl');
  const fetchTranscript = document.getElementById('fetchTranscript');
  const transcriptStatus = document.getElementById('transcriptStatus');
  const transcriptText = document.getElementById('transcriptText');

  const backendStatus = document.getElementById('backendStatus');

  const gloss = document.getElementById('gloss');
  const renderPose = document.getElementById('renderPose');
  const poseStatus = document.getElementById('poseStatus');

  const canvas = document.getElementById('canvas');

  if (!ytUrl || !fetchTranscript || !transcriptStatus || !transcriptText) {
    console.error('Missing transcript UI elements');
    return;
  }

  if (!gloss || !renderPose || !poseStatus || !canvas) {
    console.error('Missing pose UI elements');
    return;
  }

  const ctx = canvas.getContext('2d');
  if (!ctx) {
    setStatusError(poseStatus, 'Error: Canvas 2D context unavailable');
    return;
  }

  // Ensure initial crisp rendering.
  const initialSize = resizeCanvasToDisplaySize(canvas, ctx);
  clearCanvas(ctx, initialSize.cssWidth, initialSize.cssHeight);

  // Health check: tells you immediately if the backend is reachable.
  if (backendStatus) {
    backendStatus.textContent = 'Backend: checking...';
    backendStatus.classList.remove('error');
    try {
      const res = await fetch('/api/health');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      backendStatus.textContent = 'Backend: OK';
    } catch (e) {
      backendStatus.textContent = `Backend: not reachable (${e.message})`;
      backendStatus.classList.add('error');
    }
  }

  fetchTranscript.addEventListener('click', async () => {
    setStatusOk(transcriptStatus, 'Fetching...');
    transcriptText.value = '';

    try {
      const data = await postJson('/api/transcript/youtube', { url: ytUrl.value });
      transcriptText.value = data.text || '';
      setStatusOk(transcriptStatus, `OK (video_id=${data.video_id})`);
    } catch (e) {
      setStatusError(transcriptStatus, `Error: ${e.message}`);
    }
  });

  renderPose.addEventListener('click', async () => {
    setStatusOk(poseStatus, 'Loading...');
    const size = resizeCanvasToDisplaySize(canvas, ctx);
    clearCanvas(ctx, size.cssWidth, size.cssHeight);

    try {
      const data = await postJson('/api/pose/lookup', { gloss: gloss.value });
      setStatusOk(poseStatus, `OK (${data.gloss})`);

      const frames = data.frames_xy;
      let i = 0;

      function tick() {
        const { cssWidth, cssHeight } = resizeCanvasToDisplaySize(canvas, ctx);
        clearCanvas(ctx, cssWidth, cssHeight);
        drawFramePoints(ctx, frames[i], cssWidth, cssHeight);
        i = (i + 1) % frames.length;
        requestAnimationFrame(tick);
      }

      requestAnimationFrame(tick);
    } catch (e) {
      setStatusError(poseStatus, `Error: ${e.message}`);
    }
  });
}

main();
