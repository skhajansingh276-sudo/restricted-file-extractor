const express = require('express');
const path = require('path');
const chromium = require('@sparticuz/chromium');
const puppeteer = require('puppeteer-core');
const axios = require('axios');

const app = express();
app.use(express.urlencoded({ extended: true }));
app.use(express.json());

// In-memory job store (Note: Vercel serverless functions are stateless, 
// so for a robust app, we'd use Redis, but for a single-file "Success" response, 
// we will adapt the logic to return the data directly or use a simplified approach).

app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, '../public/index.html'));
});

app.post('/extract', async (req, res) => {
    const { url } = req.body;
    if (!url) return res.status(400).json({ error: 'URL required' });

    let browser = null;
    try {
        browser = await puppeteer.launch({
            args: [...chromium.args, "--hide-scrollbars", "--disable-web-security"],
            defaultViewport: chromium.defaultViewport,
            executablePath: await chromium.executablePath(),
            headless: chromium.headless,
        });

        const page = await browser.newPage();
        // Google Drive documents often require a higher timeout
        await page.goto(url, { waitUntil: 'networkidle2', timeout: 60000 });

        // Scroll to trigger lazy loading of images
        for (let i = 0; i < 12; i++) {
            await page.evaluate((y) => window.scrollTo(0, y), i * 1200);
            await new Promise(r => setTimeout(r, 1000));
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

        // To make it work seamlessly on Vercel (which has a 10s-60s timeout),
        // we return the images to the client and let the client build the PDF.
        // This is the "Best" way for serverless because it avoids heavy PDF processing on the server.
        res.status(200).json({ 
            status: 'Completed', 
            progress: 100,
            pages: uniqueImages.length, 
            images: uniqueImages 
        });

    } catch (error) {
        console.error(error);
        res.status(500).json({ error: error.message });
    } finally {
        if (browser) await browser.close();
    }
});

// Mock status for compatibility with the frontend's polling
app.get('/status/:id', (req, res) => {
    res.json({ status: 'Completed', progress: 100 });
});

module.exports = app;
