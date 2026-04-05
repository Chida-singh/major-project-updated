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

function clearCanvas(ctx, w, h) {
  ctx.clearRect(0, 0, w, h);
  ctx.fillStyle = '#0b1020';
  ctx.fillRect(0, 0, w, h);
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
    ctx.arc(px, py, 1.2, 0, Math.PI * 2);
    ctx.fill();
  }
}

async function main() {
  const ytUrl = document.getElementById('ytUrl');
  const fetchTranscript = document.getElementById('fetchTranscript');
  const transcriptStatus = document.getElementById('transcriptStatus');
  const transcriptText = document.getElementById('transcriptText');

  const gloss = document.getElementById('gloss');
  const renderPose = document.getElementById('renderPose');
  const poseStatus = document.getElementById('poseStatus');

  const canvas = document.getElementById('canvas');
  const ctx = canvas.getContext('2d');

  clearCanvas(ctx, canvas.width, canvas.height);

  fetchTranscript.addEventListener('click', async () => {
    setStatus(transcriptStatus, 'Fetching...');
    transcriptText.value = '';

    try {
      const data = await postJson('/api/transcript/youtube', { url: ytUrl.value });
      transcriptText.value = data.text || '';
      setStatus(transcriptStatus, `OK (video_id=${data.video_id})`);
    } catch (e) {
      setStatus(transcriptStatus, `Error: ${e.message}`);
    }
  });

  renderPose.addEventListener('click', async () => {
    setStatus(poseStatus, 'Loading...');
    clearCanvas(ctx, canvas.width, canvas.height);

    try {
      const data = await postJson('/api/pose/lookup', { gloss: gloss.value });
      setStatus(poseStatus, `OK (${data.gloss})`);

      const frames = data.frames_xy;
      let i = 0;

      function tick() {
        clearCanvas(ctx, canvas.width, canvas.height);
        drawFramePoints(ctx, frames[i], canvas.width, canvas.height);
        i = (i + 1) % frames.length;
        requestAnimationFrame(tick);
      }

      requestAnimationFrame(tick);
    } catch (e) {
      setStatus(poseStatus, `Error: ${e.message}`);
    }
  });
}

main();
