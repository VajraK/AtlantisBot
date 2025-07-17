const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

puppeteer.use(StealthPlugin());

function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function sanitizeFilename(url) {
  return encodeURIComponent(url) + '.html';
}

async function downloadFilings(filingUrls, datetimeFolder) {
  const saveFolder = path.join('./filings', datetimeFolder);
  fs.mkdirSync(saveFolder, { recursive: true });

  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  await page.setUserAgent("VajraKantor vkantor@hopecapitaladvisors.com");

  for (let i = 0; i < filingUrls.length; i++) {
    const url = filingUrls[i];
    try {
      console.log(`⬇️ Downloading filing ${i + 1}/${filingUrls.length}: ${url}`);

      await delay(2000 + Math.random() * 3000);

      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });

      await delay(1000 + Math.random() * 2000);

      const content = await page.content();

      const safeFilename = sanitizeFilename(url);
      const filepath = path.join(saveFolder, safeFilename);
      fs.writeFileSync(filepath, content, { encoding: 'utf-8' });

      console.log(`✅ Saved ${filepath}`);
    } catch (err) {
      console.error(`⚠️ Failed to download ${url}: ${err}`);
      await delay(10000);
    }
  }

  await browser.close();
}

async function main() {
  const args = process.argv.slice(2);
  if (args.length < 2) {
    console.error("Usage: node puppeteer_downloader.js <datetime-folder> <url1> <url2> ...");
    process.exit(1);
  }

  const datetimeFolder = args[0];
  const filingUrls = args.slice(1);

  await downloadFilings(filingUrls, datetimeFolder);
}

if (require.main === module) {
  main();
}


module.exports = {
  downloadFilings,
};