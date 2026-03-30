import fs from 'fs';
import path from 'path';

const CSV_PATH = path.join(process.cwd(), 'skills/gmail-inbox-scan/scripts/expenses.csv');
const OUT_PATH = path.join(process.cwd(), 'expenses-sync.json');

// Category mapping heuristics
function categorize(merchant, amount, existingCategory) {
  // Already good
  if (existingCategory === 'EMI') return 'Loan Repayment';

  // Amount-based heuristics (tune these thresholds)
  if (amount >= 20000) return 'Loan Repayment'; // large debits likely EMIs
  if (amount >= 5000) return 'Big Ticket';
  if (amount >= 1000) return 'Utilities/Services';
  if (amount >= 300) return 'Food & Dining';
  if (amount >= 150) return 'Transport';
  if (amount >= 50)  return 'Groceries/Household';
  if (amount >= 20)  return 'Minor Purchase';
  return 'Other';
}

function csvToJSON(csv) {
  const lines = csv.trim().split('\n');
  const headers = lines[0].split(',');
  const rows = lines.slice(1).map(line => {
    const vals = line.split(',');
    const obj = {};
    headers.forEach((h, i) => {
      obj[h.trim()] = vals[i]?.trim() || '';
    });
    const amount = parseFloat(obj.amount) || 0;
    const majorCategory = categorize(obj.merchant, amount, obj.category);
    return {
      date: obj.date,
      category: obj.category || 'Other',
      majorCategory,
      amount,
      payment: 'UPI',
      merchant: obj.merchant || '',
      source: obj.source || '',
      synced: true
    };
  });
  return rows;
}

try {
  const csv = fs.readFileSync(CSV_PATH, 'utf8');
  const data = csvToJSON(csv);
  fs.writeFileSync(OUT_PATH, JSON.stringify({ expenses: data, lastSync: new Date().toISOString() }, null, 2));
  console.log(`✅ Synced ${data.length} expenses to ${OUT_PATH}`);
} catch (e) {
  console.error('❌ Sync failed:', e.message);
  process.exit(1);
}
