const chromium = require('@sparticuz/chromium');
const puppeteer = require('puppeteer-core');

module.exports = async (req, res) => {
    if (req.method !== 'POST') {
        return res.status(405).json({ error: 'Method not allowed' });
    }

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
        await page.goto(url, { waitUntil: 'networkidle2', timeout: 30000 });

        // Scroll logic
        for (let i = 0; i < 8; i++) {
            await page.evaluate((y) => window.scrollTo(0, y), i * 1500);
            await new Promise(r => setTimeout(r, 800));
        }

        const images = await page.evaluate(() => {
            const imgs = Array.from(document.querySelectorAll('img'));
            return imgs.map(img => img.src || img.dataset.src)
                .filter(src => src && (src.includes('viewer/img') || src.includes('drive-viewer')))
                .map(src => src.replace(/&[whs]=\d+/g, "").replace(/=s\d+/g, "=s4000"));
        });

        const uniqueImages = [...new Set(images)];
        
        res.status(200).json({ 
            status: 'Success', 
            pages: uniqueImages.length, 
            images: uniqueImages 
        });

    } catch (error) {
        res.status(500).json({ error: error.message });
    } finally {
        if (browser) await browser.close();
    }
};
