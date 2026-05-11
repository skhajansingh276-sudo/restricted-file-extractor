const express = require('express');
const path = require('path');
const axios = require('axios');

const app = express();
app.use(express.urlencoded({ extended: true }));
app.use(express.json());

app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, '../public/index.html'));
});

app.post('/extract', async (req, res) => {
    const { url } = req.body;
    if (!url) return res.status(400).json({ error: 'URL required' });

    try {
        // 1. Transform URL to mobilebasic (This bypasses many protections)
        let targetUrl = url;
        if (url.includes('/file/d/')) {
            targetUrl = url.replace('/view', '').replace('/edit', '') + '/mobilebasic';
        } else if (url.includes('/document/d/')) {
            targetUrl = url.replace('/edit', '') + '/mobilebasic';
        }

        // 2. Fetch the HTML source code
        const response = await axios.get(targetUrl, {
            headers: {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/04.1'
            }
        });

        const html = response.data;

        // 3. Extract high-res images using Regex
        // Patterns for Drive and Docs images
        const imgPattern = /https:\/\/[a-z0-9.-]+\.googleusercontent\.com\/[a-zA-Z0-9\-_/=&?]+/g;
        const matches = html.match(imgPattern) || [];

        // Clean and filter images (Look for viewer/img or drive-viewer)
        const uniqueImages = [...new Set(matches)]
            .filter(src => src.includes('viewer/img') || src.includes('drive-viewer'))
            .map(src => {
                // Remove size limits to get original quality
                return src.replace(/&[whs]=\d+/g, "").replace(/=s\d+/g, "=s4000");
            });

        if (uniqueImages.length === 0) {
            // Fallback: If no images found, it might be a different protection level
            return res.status(400).json({ 
                error: 'Restricted link detected. This specific document requires an authenticated browser session. Try making the link "Anyone with link can view".' 
            });
        }

        res.status(200).json({ 
            status: 'Completed', 
            progress: 100,
            pages: uniqueImages.length, 
            images: uniqueImages 
        });

    } catch (error) {
        console.error(error);
        res.status(500).json({ error: `Extraction Failed: ${error.message}` });
    }
});

module.exports = app;
