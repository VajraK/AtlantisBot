const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const fs = require('fs');
const path = require('path');

puppeteer.use(StealthPlugin());

function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function downloadFilings(filingUrls, saveFolder) {
  // Get today's date in YYYY-MM-DD format
  const today = new Date();
  const dateString = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
  
  // Create the dated subfolder
  const datedFolder = path.join(saveFolder, dateString);
  fs.mkdirSync(datedFolder, { recursive: true });

  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();

  // Set User-Agent or any headers if needed
  await page.setUserAgent("VajraKantor vkantor@hopecapitaladvisors.com");

  for (let i = 0; i < filingUrls.length; i++) {
    const url = filingUrls[i];
    try {
      console.log(`⬇️ Downloading filing ${i + 1}/${filingUrls.length}: ${url}`);

      await delay(2000 + Math.random() * 3000); // Random delay 2-5 seconds before navigating

      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });

      await delay(1000 + Math.random() * 2000); // Random delay 1-3 seconds after load

      const content = await page.content();

      const filename = path.join(datedFolder, `filing_${i + 1}.html`);
      fs.writeFileSync(filename, content, { encoding: 'utf-8' });

      console.log(`✅ Saved ${filename}`);

    } catch (err) {
      console.error(`⚠️ Failed to download ${url}: ${err}`);

      await delay(10000); // Longer delay on failure
    }
  }

  await browser.close();
}

async function main() {
  const filingUrls = process.argv.slice(2);
  if (filingUrls.length === 0) {
    console.error("Please provide filing URLs as command-line arguments.");
    process.exit(1);
  }

  await downloadFilings(filingUrls, './filings');
}

if (require.main === module) {
  main();
}

module.exports = {
  downloadFilings,
};