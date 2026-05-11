const express = require('express');
const chromium = require('@sparticuz/chromium');
const puppeteer = require('puppeteer-core');
const axios = require('axios');
const path = require('path');

const app = express();
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Serve the index.html from the root
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, '../templates/index.html'));
});

app.post('/api/extract', async (req, res) => {
    const { url } = req.body;
    if (!url) return res.status(400).json({ error: 'URL required' });

    let browser = null;
    try {
        browser = await puppeteer.launch({
            args: chromium.args,
            defaultViewport: chromium.defaultViewport,
            executablePath: await chromium.executablePath(),
            headless: chromium.headless,
        });

        const page = await browser.newPage();
        await page.setViewport({ width: 1920, height: 1080 });
        await page.goto(url, { waitUntil: 'networkidle2' });

        // Scroll to trigger lazy load
        for (let i = 0; i < 10; i++) {
            await page.evaluate((y) => window.scrollTo(0, y), i * 1200);
            await new Promise(r => setTimeout(r, 1000));
        }

        const images = await page.evaluate(() => {
            const imgs = Array.from(document.querySelectorAll('img'));
            return imgs.map(img => img.src || img.dataset.src)
                .filter(src => src && (src.includes('viewer/img') || src.includes('drive-viewer')));
        });

        if (images.length === 0) throw new Error('No images found');

        // Note: Full PDF generation on Vercel is hard due to memory.
        // For now, we return the image list to the frontend to keep it light.
        res.json({ status: 'Success', pages: images.length, images: images });

    } catch (error) {
        res.status(500).json({ error: error.message });
    } finally {
        if (browser) await browser.close();
    }
});

module.exports = app;
