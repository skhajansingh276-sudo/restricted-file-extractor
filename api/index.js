const express = require('express');
const path = require('path');
const puppeteer = require('puppeteer-core');
const chromium = require('@sparticuz/chromium');

const app = express();
app.use(express.urlencoded({ extended: true }));
app.use(express.json());

// Browserless.io Token (Recommended for Vercel)
const BROWSERLESS_TOKEN = process.env.BROWSERLESS_TOKEN;

app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, '../public/index.html'));
});

app.post('/extract', async (req, res) => {
    const { url } = req.body;
    if (!url) return res.status(400).json({ error: 'URL required' });

    let browser = null;
    try {
        if (BROWSERLESS_TOKEN) {
            // THE PRO WAY: Use Browserless (Guaranteed to work on Vercel)
            browser = await puppeteer.connect({
                browserWSEndpoint: `wss://chrome.browserless.io?token=${BROWSERLESS_TOKEN}`,
            });
        } else {
            // THE LOCAL WAY: (May fail on some Vercel regions due to missing libs)
            browser = await puppeteer.launch({
                args: [...chromium.args, "--hide-scrollbars", "--disable-web-security"],
                defaultViewport: chromium.defaultViewport,
                executablePath: await chromium.executablePath(),
                headless: chromium.headless,
            });
        }

        const page = await browser.newPage();
        await page.goto(url, { waitUntil: 'networkidle2', timeout: 60000 });

        // Scroll to trigger lazy loading
        for (let i = 0; i < 15; i++) {
            await page.evaluate((y) => window.scrollTo(0, y), i * 1200);
            await new Promise(r => setTimeout(r, 800));
        }

        const images = await page.evaluate(() => {
            const imgs = Array.from(document.querySelectorAll('img'));
            return imgs.map(img => img.src || img.dataset.src)
                .filter(src => src && (src.includes('viewer/img') || src.includes('drive-viewer')))
                .map(src => src.replace(/&[whs]=\d+/g, "").replace(/=s\d+/g, "=s4000"));
        });

        const uniqueImages = [...new Set(images)];

        if (uniqueImages.length === 0) {
            return res.status(400).json({ error: 'No images found. Ensure the link is valid and public.' });
        }

        res.status(200).json({ 
            status: 'Completed', 
            progress: 100,
            pages: uniqueImages.length, 
            images: uniqueImages 
        });

    } catch (error) {
        console.error(error);
        res.status(500).json({ error: `Browser Error: ${error.message}. Tip: Add a BROWSERLESS_TOKEN to Vercel for 100% reliability.` });
    } finally {
        if (browser) await browser.close();
    }
});

module.exports = app;
