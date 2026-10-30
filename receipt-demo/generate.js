const puppeteer = require('puppeteer');
const path = require('path');

(async () => {
    try {
        console.log('Launching browser...');
        const browser = await puppeteer.launch({ executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe' });
        const page = await browser.newPage();
        
        const htmlPath = path.join(__dirname, 'template.html');
        console.log(`Loading HTML from ${htmlPath}...`);
        
        await page.goto(`file://${htmlPath}`, { waitUntil: 'networkidle0' });
        
        const pdfPath = path.join(__dirname, 'POS_Receipt_Demo.pdf');
        
        // Typical receipt printer width is 80mm
        await page.pdf({
            path: pdfPath,
            width: '80mm',
            height: '200mm', // Approximate height for these items
            printBackground: true,
            margin: { top: '0', right: '0', bottom: '0', left: '0' }
        });
        
        console.log(`PDF successfully generated at ${pdfPath}`);
        await browser.close();
    } catch (error) {
        console.error('Error generating PDF:', error);
    }
})();
