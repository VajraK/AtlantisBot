const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const readline = require('readline');

puppeteer.use(StealthPlugin());

function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function scrapeSecSearch(query, daysBack) {
  const endDate = new Date();
  const startDate = new Date();
  startDate.setDate(endDate.getDate() - daysBack);
  
  const startStr = startDate.toISOString().split('T')[0];
  const endStr = endDate.toISOString().split('T')[0];
  
  // Double URL-encode the query
  const encodedQuery = encodeURIComponent(encodeURIComponent(query));
  const url = `https://www.sec.gov/edgar/search/#/q=${encodedQuery}&dateRange=custom&startdt=${startStr}&enddt=${endStr}`;
  
  console.error(`🔍 Opening SEC search URL: ${url}`);
  
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const page = await browser.newPage();
  await page.setUserAgent("VajraKantor vkantor@hopecapitaladvisors.com");
  
  let results = [];
  let resultsSet = new Set();
  
  try {
    console.error("🌐 Navigating to SEC page...");
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await delay(3000); // Initial delay for JS to load
    
    let hasNextPage = true;
    let pageCount = 1;
    
    while (hasNextPage) {
      console.error(`📄 Processing page ${pageCount}...`);
      
      // Wait for results table
      try {
        await page.waitForSelector('#hits > table > tbody > tr', { timeout: 15000 });
      } catch (err) {
        console.error("❌ Timed out waiting for results table");
        break;
      }
      
      // Extract filing links
      const links = await page.$$eval('#hits > table > tbody > tr', rows => 
        rows.map(row => {
          const link = row.querySelector('td.filetype > a.preview-file');
          return link ? link.href : null;
        }).filter(Boolean)
      );
      
      // Add new links to results
      for (const href of links) {
        if (href && !resultsSet.has(href)) {
          results.push(href);
          resultsSet.add(href);
        }
      }
      
      console.error(`✅ Found ${links.length} links on this page (Total: ${results.length})`);
      
      // Check for next page
      try {
        const nextDisabled = await page.$eval(
          'li.page-item > a.page-link[data-value="nextPage"]', 
          el => el.parentElement.classList.contains('disabled') || el.style.display === 'none'
        );
        
        if (nextDisabled) {
          console.error("⏹️ No more pages available");
          hasNextPage = false;
        } else {
          console.error("➡️ Clicking next page...");
          await page.click('li.page-item > a.page-link[data-value="nextPage"]');
          await delay(3000); // Wait for next page to load
          pageCount++;
        }
      } catch (err) {
        console.error("⏹️ Next page button not found or not clickable");
        hasNextPage = false;
      }
    }
  } catch (err) {
    console.error(`⚠️ Scraping error: ${err}`);
  } finally {
    await browser.close();
  }
  
  console.error(`🎉 Found ${results.length} total filings`);
  return results;
}

async function main() {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
    terminal: false
  });

  let inputData = '';
  for await (const line of rl) {
    inputData += line;
  }

  const { query, days_back } = JSON.parse(inputData);
  const results = await scrapeSecSearch(query, days_back);
  console.log(JSON.stringify(results));
}

if (require.main === module) {
  main().catch(err => {
    console.error(err);
    process.exit(1);
  });
}

module.exports = { scrapeSecSearch };