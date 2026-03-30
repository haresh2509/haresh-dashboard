import fs from 'fs';
import path from 'path';

const MD_PATH = path.join(process.cwd(), 'memory/application-tracker.md');
const OUT_PATH = path.join(process.cwd(), 'jobs-sync.json');

function parseMarkdownTable(md) {
  const lines = md.trim().split('\n');
  // Find header row
  let headerIdx = lines.findIndex(l => l.includes('|') && l.includes('Date'));
  if (headerIdx === -1) return [];
  const headers = lines[headerIdx].split('|').slice(1, -1).map(h => h.trim().toLowerCase());
  // Data rows start after header and separator
  const dataStart = headerIdx + 2;
  const rows = [];
  for (let i = dataStart; i < lines.length; i++) {
    const line = lines[i];
    if (!line.includes('|')) break;
    const cells = line.split('|').slice(1, -1).map(c => c.trim());
    if (cells.length < headers.length) continue;
    const obj = {};
    headers.forEach((h, idx) => {
      obj[h] = cells[idx] || '';
    });
    rows.push(obj);
  }
  return rows;
}

try {
  const md = fs.readFileSync(MD_PATH, 'utf8');
  const rows = parseMarkdownTable(md);
  const jobs = rows.map(r => ({
    date: r.date || '',
    company: r.company || '',
    role: r.role || '',
    status: r.status || 'Applied',
    method: r.method || '',
    followup: r.followup || '',
    notes: r.notes || '',
    synced: true
  }));
  fs.writeFileSync(OUT_PATH, JSON.stringify({ jobs, lastSync: new Date().toISOString() }, null, 2));
  console.log(`✅ Synced ${jobs.length} jobs to ${OUT_PATH}`);
} catch (e) {
  console.error('❌ Sync failed:', e.message);
  process.exit(1);
}
