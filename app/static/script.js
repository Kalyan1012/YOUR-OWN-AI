// ─── State ───────────────────────────────────────────
let indexedPoints = [];
let activeQuery = null;
let selectedAlgo = 'hnsw';
let queryCount = 0;

// ─── Canvas Setup ────────────────────────────────────
const canvas = document.getElementById('vectorCanvas');
const ctx = canvas.getContext('2d');

function resizeCanvas() {
    const wrap = canvas.parentElement;
    canvas.width = wrap.clientWidth;
    canvas.height = wrap.clientHeight;
    drawCanvas();
}

window.addEventListener('resize', resizeCanvas);

// ─── Safe DOM Helper ──────────────────────────────────
function setEl(id, value, isHTML = false) {
    const el = document.getElementById(id);
    if (!el) {
        console.warn(`Element #${id} not found`);
        return;
    }
    if (isHTML) {
        el.innerHTML = value;
    } else {
        el.textContent = value;
    }
}

// ─── Drawing ─────────────────────────────────────────
function toCanvasCoords(x, y) {
    const pad = 60;
    return {
        cx: pad + x * (canvas.width - 2 * pad),
        cy: pad + y * (canvas.height - 2 * pad)
    };
}

function drawCanvas() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    drawGrid();
    drawPoints();
    drawQuery();
}

function drawGrid() {
    ctx.fillStyle = '#070b18';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.strokeStyle = 'rgba(30, 45, 74, 0.4)';
    ctx.lineWidth = 1;

    const step = 60;
    for (let x = 0; x < canvas.width; x += step) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, canvas.height);
        ctx.stroke();
    }
    for (let y = 0; y < canvas.height; y += step) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(canvas.width, y);
        ctx.stroke();
    }

    ctx.strokeStyle = 'rgba(59, 130, 246, 0.2)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(0, canvas.height / 2);
    ctx.lineTo(canvas.width, canvas.height / 2);
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(canvas.width / 2, 0);
    ctx.lineTo(canvas.width / 2, canvas.height);
    ctx.stroke();
}

function drawPoints() {
    indexedPoints.forEach((pt) => {
        const { cx, cy } = toCanvasCoords(pt.x, pt.y);

        // Glow
        const grd = ctx.createRadialGradient(cx, cy, 0, cx, cy, 20);
        grd.addColorStop(0, 'rgba(16, 185, 129, 0.3)');
        grd.addColorStop(1, 'rgba(16, 185, 129, 0)');
        ctx.fillStyle = grd;
        ctx.beginPath();
        ctx.arc(cx, cy, 20, 0, Math.PI * 2);
        ctx.fill();

        // Point
        ctx.fillStyle = '#10b981';
        ctx.beginPath();
        ctx.arc(cx, cy, 7, 0, Math.PI * 2);
        ctx.fill();

        // Inner highlight
        ctx.fillStyle = 'rgba(255,255,255,0.4)';
        ctx.beginPath();
        ctx.arc(cx - 2, cy - 2, 2, 0, Math.PI * 2);
        ctx.fill();

        // Label
        const label = pt.name.length > 18
            ? pt.name.substring(0, 18) + '...'
            : pt.name;

        ctx.font = 'bold 11px monospace';
        const textWidth = ctx.measureText(label).width;

        ctx.fillStyle = 'rgba(7, 11, 24, 0.8)';
        ctx.fillRect(cx + 12, cy - 10, textWidth + 8, 18);

        ctx.fillStyle = '#94a3b8';
        ctx.fillText(label, cx + 16, cy + 2);
    });
}

function drawQuery() {
    if (!activeQuery) return;

    const { cx, cy } = toCanvasCoords(activeQuery.x, activeQuery.y);

    // Connection line to matched node
    if (activeQuery.target) {
        const { cx: tx, cy: ty } = toCanvasCoords(
            activeQuery.target.x,
            activeQuery.target.y
        );

        ctx.strokeStyle = 'rgba(245, 158, 11, 0.6)';
        ctx.lineWidth = 2;
        ctx.setLineDash([8, 4]);
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.lineTo(tx, ty);
        ctx.stroke();
        ctx.setLineDash([]);

        // Distance label on line
        const midX = (cx + tx) / 2;
        const midY = (cy + ty) / 2;
        ctx.fillStyle = 'rgba(245, 158, 11, 0.9)';
        ctx.font = 'bold 11px monospace';
        ctx.fillText(
            `d=${activeQuery.distance.toFixed(3)}`,
            midX + 6,
            midY - 4
        );

        // Highlight matched point ring
        ctx.strokeStyle = '#f59e0b';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.arc(tx, ty, 12, 0, Math.PI * 2);
        ctx.stroke();
    }

    // Query glow
    const grd = ctx.createRadialGradient(cx, cy, 0, cx, cy, 25);
    grd.addColorStop(0, 'rgba(59, 130, 246, 0.4)');
    grd.addColorStop(1, 'rgba(59, 130, 246, 0)');
    ctx.fillStyle = grd;
    ctx.beginPath();
    ctx.arc(cx, cy, 25, 0, Math.PI * 2);
    ctx.fill();

    // Star shape
    drawStar(cx, cy, 5, 10, 5, '#3b82f6');

    // Query label
    ctx.font = 'bold 12px monospace';
    ctx.fillStyle = 'rgba(7, 11, 24, 0.8)';
    ctx.fillRect(cx + 14, cy - 10, 80, 18);
    ctx.fillStyle = '#60a5fa';
    ctx.fillText('★ QUERY', cx + 18, cy + 2);
}

function drawStar(cx, cy, spikes, outerRadius, innerRadius, color) {
    let rot = (Math.PI / 2) * 3;
    const step = Math.PI / spikes;

    ctx.beginPath();
    ctx.moveTo(cx, cy - outerRadius);

    for (let i = 0; i < spikes; i++) {
        ctx.lineTo(
            cx + Math.cos(rot) * outerRadius,
            cy + Math.sin(rot) * outerRadius
        );
        rot += step;
        ctx.lineTo(
            cx + Math.cos(rot) * innerRadius,
            cy + Math.sin(rot) * innerRadius
        );
        rot += step;
    }

    ctx.lineTo(cx, cy - outerRadius);
    ctx.closePath();
    ctx.fillStyle = color;
    ctx.fill();
}

// ─── Algorithm Toggle ─────────────────────────────────
function setAlgo(algo) {
    selectedAlgo = algo;

    const btnHnsw = document.getElementById('btnHnsw');
    const btnBrute = document.getElementById('btnBrute');
    const algoDisplay = document.getElementById('algoDisplay');

    if (btnHnsw) btnHnsw.classList.toggle('active', algo === 'hnsw');
    if (btnBrute) btnBrute.classList.toggle('active', algo === 'brute_force');
    if (algoDisplay) {
        algoDisplay.innerHTML = `Algorithm: <strong>${
            algo === 'hnsw' ? 'HNSW' : 'Brute Force'
        }</strong>`;
    }
}

// ─── Embed Document ───────────────────────────────────
async function embedDocument() {
    const nameEl = document.getElementById('docName');
    const contentEl = document.getElementById('docContent');
    const btn = document.getElementById('embedBtn');
    const btnText = document.getElementById('embedBtnText');

    if (!nameEl || !contentEl) {
        console.error('Form elements not found');
        return;
    }

    const name = nameEl.value.trim();
    const content = contentEl.value.trim();

    if (!name || !content) {
        alert('Please fill in document name and content');
        return;
    }

    if (btn) btn.disabled = true;
    if (btnText) btnText.textContent = '⏳ Embedding...';

    updateSteps([
        { text: 'Chunking document text...', state: 'done' },
        { text: 'Generating 768D embeddings with nomic-embed-text...', state: 'active' },
        { text: 'Inserting into FAISS indexes...', state: 'idle' }
    ], 'Embedding');

    try {
        const res = await fetch('/embed', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, content })
        });

        if (!res.ok) {
            throw new Error(`Server error: ${res.status}`);
        }

        const data = await res.json();

        // Add points
        data.chunks.forEach(chunk => {
            indexedPoints.push({
                name: chunk.name,
                x: chunk.vector_2d[0],
                y: chunk.vector_2d[1],
                content: chunk.content
            });
        });

        // Update UI safely
        setEl('statDocs', indexedPoints.length);
        setEl('docCount', `${indexedPoints.length} documents`);

        // Hide empty state
        const emptyEl = document.getElementById('canvasEmpty');
        if (emptyEl) emptyEl.style.display = 'none';

        drawCanvas();

        updateSteps([
            { text: `Document chunked into ${data.chunks_inserted} piece(s)`, state: 'done' },
            { text: `768D embeddings generated successfully`, state: 'done' },
            { text: `Inserted into BruteForce & HNSW FAISS indexes`, state: 'done' },
            { text: `Total vectors in memory: ${data.total_chunks}`, state: 'done' }
        ], 'Done ✅');

        // Clear form
        nameEl.value = '';
        contentEl.value = '';

        console.log(`✅ Indexed "${name}" → ${data.chunks_inserted} chunk(s)`);

    } catch (err) {
        console.error('Embed error:', err);
        updateSteps([
            { text: `❌ Error: ${err.message}`, state: 'active' }
        ], 'Error');
        alert(`Error: ${err.message}`);
    }

    if (btn) btn.disabled = false;
    if (btnText) btnText.textContent = '⚡ Embed & Index';
}

// ─── Submit Query ─────────────────────────────────────
async function submitQuery() {
    const queryEl = document.getElementById('queryText');
    const btn = document.getElementById('queryBtn');
    const btnText = document.getElementById('queryBtnText');

    if (!queryEl) {
        console.error('Query input not found');
        return;
    }

    const text = queryEl.value.trim();

    if (!text) {
        alert('Please enter a question');
        return;
    }

    if (btn) btn.disabled = true;
    if (btnText) btnText.textContent = '⏳ Searching...';

    setEl('responseArea', '<div class="response-placeholder">⏳ Generating response...</div>', true);
    setEl('matchInfo', '<div class="match-placeholder">🔍 Searching vector space...</div>', true);

    updateSteps([
        { text: 'Embedding query with nomic-embed-text...', state: 'active' },
        { text: `Running ${selectedAlgo.toUpperCase()} search...`, state: 'idle' },
        { text: 'Retrieving matched context...', state: 'idle' },
        { text: 'Generating LLM response...', state: 'idle' }
    ], 'Searching');

    try {
        const res = await fetch('/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, algorithm: selectedAlgo })
        });

        if (!res.ok) {
            throw new Error(`Server error: ${res.status}`);
        }

        const data = await res.json();

        queryCount++;

        // Update stats safely
        setEl('statQueries', queryCount);
        setEl('statTime', `${data.search_time}ms`);
        setEl('queryCount', `${queryCount} queries`);
        setEl('searchTime', `${data.search_time}ms`);

        // Update canvas
        const targetNode = indexedPoints.find(p => p.name === data.closest_node);
        activeQuery = {
            x: data.query_vector[0],
            y: data.query_vector[1],
            target: targetNode,
            distance: data.distance
        };

        drawCanvas();

        // Update steps
        if (data.steps && data.steps.length > 0) {
            updateSteps(
                data.steps.map(s => ({ text: s, state: 'done' })),
                'Complete ✅'
            );
        }

        // Show response
        setEl('responseArea', `
            <div class="response-text">${data.response}</div>
            ${data.context
                ? `<div class="context-box">📄 Context used: ${data.context}</div>`
                : ''
            }
        `, true);

        setEl('responseBadge', data.algorithm_used);

        // Match details
        const distPercent = Math.min(100, (data.distance / 2) * 100);

        if (data.closest_node !== 'None') {
            setEl('matchInfo', `
                <div class="match-row">
                    <span class="match-key">Matched Node</span>
                    <span class="match-val green">${data.closest_node}</span>
                </div>
                <div class="match-row">
                    <span class="match-key">Distance Score</span>
                    <span class="match-val orange">${data.distance.toFixed(4)}</span>
                    <div class="distance-bar">
                        <div class="distance-fill" style="width: ${100 - distPercent}%"></div>
                    </div>
                </div>
                <div class="match-row">
                    <span class="match-key">Search Time</span>
                    <span class="match-val blue">${data.search_time}ms</span>
                </div>
                <div class="match-row">
                    <span class="match-key">Algorithm</span>
                    <span class="match-val">${data.algorithm_used}</span>
                </div>
            `, true);
            setEl('matchBadge', '✅ Match Found');
        } else {
            setEl('matchInfo', '<div class="match-placeholder">⚠️ No match found within threshold</div>', true);
            setEl('matchBadge', '❌ No Match');
        }

    } catch (err) {
        console.error('Query error:', err);
        setEl('responseArea', `
            <div class="response-text" style="color: var(--red)">
                ❌ Error: ${err.message}
            </div>
        `, true);
        updateSteps([
            { text: `❌ Error: ${err.message}`, state: 'active' }
        ], 'Error');
    }

    if (btn) btn.disabled = false;
    if (btnText) btnText.textContent = '🚀 Execute Query';
}

// ─── Clear All ────────────────────────────────────────
async function clearAll() {
    if (!confirm('Clear all indexed documents and reset the vector space?')) return;

    try {
        await fetch('/documents', { method: 'DELETE' });

        indexedPoints = [];
        activeQuery = null;
        queryCount = 0;

        setEl('statDocs', '0');
        setEl('statQueries', '0');
        setEl('statTime', '0ms');
        setEl('docCount', '0 documents');
        setEl('queryCount', '0 queries');
        setEl('matchBadge', '—');
        setEl('responseBadge', 'Ready');
        setEl('stepsBadge', 'Idle');

        setEl('responseArea', '<div class="response-placeholder">Response will appear here after querying...</div>', true);
        setEl('matchInfo', '<div class="match-placeholder">Similarity match details will appear here...</div>', true);

        const emptyEl = document.getElementById('canvasEmpty');
        if (emptyEl) emptyEl.style.display = 'flex';

        drawCanvas();

        updateSteps([
            { text: 'All data cleared', state: 'done' },
            { text: 'FAISS indexes reset', state: 'done' },
            { text: 'Ready for new documents', state: 'done' }
        ], 'Reset');

        console.log('🗑️ All data cleared');

    } catch (err) {
        console.error('Clear error:', err);
        alert(`Error: ${err.message}`);
    }
}

// ─── Update Steps ─────────────────────────────────────
function updateSteps(steps, badge) {
    const list = document.getElementById('stepsList');
    if (list) {
        list.innerHTML = steps.map(s => `
            <div class="step-item ${s.state}">
                <span class="step-dot"></span>
                ${s.text}
            </div>
        `).join('');
    }

    setEl('stepsBadge', badge);
}

// ─── Enter Key Handler ────────────────────────────────
function handleEnter(event) {
    if (event.key === 'Enter') submitQuery();
}

// ─── Init ─────────────────────────────────────────────
window.addEventListener('load', () => {
    resizeCanvas();
    drawCanvas();
    console.log('✅ VectorRAG system initialized');
});