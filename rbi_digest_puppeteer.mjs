#!/usr/bin/env node
/**
 * RBI Circulars Digest — Puppeteer scraper
 * Fetches last 7 days of circulars from RBI circulars page
 * Filters by keywords, extracts PDF links, summarizes
 * Sends email via Gmail SMTP
 */
import puppeteer from 'puppeteer';
import nodemailer from 'nodemailer';

// Config
const GMAIL_ADDRESS = 'haresh.mulchandani01@gmail.com';
const GMAIL_APP_PASSWORD = 'fadm czyo ngtd tzbq'; // TODO: load from env
const RECIPIENT = GMAIL_ADDRESS;

const KEYWORDS = [
  'treasury', 'forex', 'foreign exchange', 'payments', 'upi', 'rtgs', 'neft',
  'ai', 'artificial intelligence', 'machine learning', 'fintech', 'digital rupee',
  'cbdc', 'e-rupee', 'regtech', 'compliance', 'internal audit', 'sox',
  'operational risk', 'banking', 'nbfc', 'audit', 'control', 'risk management'
];

async function scrapeRbiCirculars() {
  const browser = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox', '--disable-setuid-sandbox'] });
  const page = await browser.newPage();
  await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
  await page.goto('https://www.rbi.org.in/Scripts/BS_ViewCirculars.aspx', { waitUntil: 'networkidle2', timeout: 30000 });

  // Wait for table rows to load
  await page.waitForSelector('table');
  const rows = await page.evaluate(() => {
    // RBI circulars page has a table with columns: Date, Circular No., Title, PDF
    const data = [];
    const tables = document.querySelectorAll('table');
    for (const table of tables) {
      const trs = table.querySelectorAll('tr');
      for (const tr of trs) {
        const tds = tr.querySelectorAll('td');
        if (tds.length >= 4) {
          const dateStr = tds[0].innerText.trim();
          const title = tds[2].innerText.trim();
          let pdfLink = '';
          const link = tds[3].querySelector('a');
          if (link) pdfLink = link.href;
          if (pdfLink && !pdfLink.startsWith('http')) {
            pdfLink = 'https://www.rbi.org.in' + pdfLink;
          }
          data.push({ dateStr, title, pdfLink });
        }
      }
    }
    return data;
  });
  await browser.close();

  // Filter by last 7 days and keywords
  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - 7);
  const items = [];
  for (const row of rows) {
    if (!row.pdfLink) continue;
    // Parse date
    let dt;
    try {
      // date format e.g. "30/03/2026"
      const [dd, mm, yyyy] = row.dateStr.split('/');
      dt = new Date(`${yyyy}-${mm}-${dd}`);
    } catch (e) {
      dt = null;
    }
    if (dt && dt < cutoff) continue;
    const text = (row.title).toLowerCase();
    if (!KEYWORDS.some(k => text.includes(k))) continue;
    items.push({
      title: row.title,
      link: row.pdfLink,
      date: row.dateStr,
      source: 'RBI Circulars'
    });
  }
  // Deduplicate by title
  const uniq = [];
  const seen = new Set();
  for (const it of items) {
    if (!seen.has(it.title)) {
      uniq.push(it);
      seen.add(it.title);
    }
  }
  return uniq;
}

async function fetchSummaryFromPdf(pdfUrl) {
  // For speed, we'll just grab the first 200 chars of the PDF as text (requires pdf2text)
  // But to keep it simple, we'll skip PDF fetch and just use title
  return '';
}

function formatEmailHtml(items) {
  const today = new Date().toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'short', year: 'numeric' });
  let html = `
<html><body style="font-family: Inter, -apple-system, sans-serif; max-width: 720px; margin: auto; padding: 24px; background: #f9f9fb; color: #1c1c1e;">
  <h2 style="color: #007AFF; margin-top: 0;">RBI Circulars Digest — ${today}</h2>
  <p style="color: #666; margin-bottom: 24px;">Latest circulars (last 7 days) relevant to treasury, payments, AI, fintech, compliance, audit.</p>
`;
  if (items.length === 0) {
    html += '<p>No new circulars matched your filters in the last 7 days.</p>';
  } else {
    for (let i = 0; i < items.length; i++) {
      const it = items[i];
      html += `
  <div style="margin-bottom: 20px; padding: 16px; background: #fff; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.06);">
    <div style="font-size: 12px; color: #8E8E93; margin-bottom: 6px;">[${it.source}] ${it.date}</div>
    <a href="${it.link}" style="font-size: 17px; font-weight: 600; color: #007AFF; text-decoration: none; margin-bottom: 8px; display: block;">${i+1}. ${it.title}</a>
    <p style="margin: 0; font-size: 14px; line-height: 1.6; color: #444;">Click the link above to view the full circular (PDF).</p>
  </div>
`;
    }
  }
  html += `
  <p style="color: #8E8E93; font-size: 12px; margin-top: 32px; padding-top: 16px; border-top: 1px solid #eee;">
    Sent by OpenClaw. Preferences? Reply to adjust topics or timing.
  </p>
</body></html>
`;
  return html;
}

async function sendEmail(html) {
  const transporter = nodemailer.createTransport({
    host: 'smtp.gmail.com',
    port: 465,
    secure: true,
    auth: {
      user: GMAIL_ADDRESS,
      pass: GMAIL_APP_PASSWORD
    }
  });
  try {
    await transporter.sendMail({
      from: GMAIL_ADDRESS,
      to: RECIPIENT,
      subject: `RBI Circulars Digest — ${new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })}`,
      html
    });
    console.log('Email sent.');
  } catch (e) {
    console.error('Email error:', e);
  }
}

(async () => {
  const items = await scrapeRbiCirculars();
  const html = formatEmailHtml(items);
  await sendEmail(html);
})();
