import time
import math
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright, BrowserContext, Page
from ..core.config import settings
from ..core.logger import logger
from .storage import ReadLaterStorage

ACTIVITY_TRACKER_SCRIPT = """
(function() {
    if (window.__activityTrackerInstalled) return;
    window.__activityTrackerInstalled = true;
    
    // HPCE Data Vector
    window.__hpce = {
        clicks: 0,
        keys: 0,
        scrolls: 0,
        mouseDistance: 0,
        startTime: Date.now(),
        lastActive: Date.now()
    };
    
    const update = (evt) => { 
        window.__hpce.lastActive = Date.now();
        if (evt.type === 'click') window.__hpce.clicks++;
        if (evt.type === 'keydown') window.__hpce.keys++;
        if (evt.type === 'scroll') window.__hpce.scrolls++;
        if (evt.type === 'mousemove') window.__hpce.mouseDistance++;
    };
    
    ['click', 'keydown', 'scroll'].forEach(e => window.addEventListener(e, update, {passive: true}));
    
    // Throttle mousemove to avoid perf impact
    let lastMove = 0;
    window.addEventListener('mousemove', (e) => {
        const now = Date.now();
        if(now - lastMove > 500) { update(e); lastMove = now; }
    }, {passive: true});
})();
"""

class TabPurger:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.storage = ReadLaterStorage()
        self._monitoring_start = time.time()

    def start_session(self, headless=False):
        """Starts a Playwright session, either connecting to existing or launching new."""
        self.playwright = sync_playwright().start()
        try:
            # Try connecting to standard remote debugging port
            self.browser = self.playwright.chromium.connect_over_cdp("http://localhost:9222")
            self.context = self.browser.contexts[0]
            logger.info("Connected to existing browser session via CDP.")
        except Exception:
            logger.warning("Could not connect to existing browser (Port 9222). Launching new instance.")
            self.browser = self.playwright.chromium.launch(headless=headless)
            self.context = self.browser.new_context()

    def stop_session(self):
        try:
            if self.browser:
                self.browser.close()
        except Exception:
            pass  # Browser already closed
        try:
            if self.playwright:
                self.playwright.stop()
        except Exception:
            pass  # Playwright already stopped

    def inject_tracker(self):
        """Injects activity tracking script into all pages."""
        if not self.context:
            return
        
        for page in self.context.pages:
            try:
                page.evaluate(ACTIVITY_TRACKER_SCRIPT)
            except Exception as e:
                # Page might be closed or navigating
                pass

    def run_hpce_analysis(self, hpce_data, idle_seconds):
        """
        Human Presence Confidence Engine (HPCE)
        Calculates a confidence score (0.0-1.0) that user needs this tab.
        """
        clicks = hpce_data.get('clicks', 0)
        keys = hpce_data.get('keys', 0)
        scrolls = hpce_data.get('scrolls', 0)
        
        # 1. Behavior Fingerprinting
        fingerprint = "Ghost"
        base_decay_mins = settings.INACTIVE_THRESHOLD_MINUTES
        
        if keys > 20 or clicks > 10:
            fingerprint = "Creator" # High value
            base_decay_mins *= 2.0 
        elif scrolls > 50:
            fingerprint = "Reader" # Medium value
            base_decay_mins *= 1.5
        elif clicks > 0:
            fingerprint = "Browser" # Low value
        
        # 2. Idle Decay Curve (Sigmoidal)
        # P = 1 / (1 + e^(k * (t - t0)))
        # k = steepness, t0 = inflection point
        
        idle_mins = idle_seconds / 60
        k = 0.8
        t0 = base_decay_mins
        
        # Avoid math overflow
        try:
            confidence = 1 / (1 + math.exp(k * (idle_mins - t0)))
        except OverflowError:
            confidence = 0.0
            
        return confidence, fingerprint

    def scan_and_purge(self, dry_run=False):
        """Scans tabs using HPCE logic."""
        if not self.context:
            return

        self.inject_tracker()
        time.sleep(1) # Allow script to run
        
        purged_tabs = []
        keep_tabs = []
        
        now = time.time()
        
        for page in self.context.pages:
            try:
                # Handle both CDP (property) and Playwright (method) access
                title = page.title if isinstance(page.title, str) else page.title()
                url = page.url if isinstance(page.url, str) else page.url()
                
                # Retrieve HPCE Vector
                hpce_raw = page.evaluate("window.__hpce || {}")
                last_active_js = hpce_raw.get('lastActive', 0)
                
                # If script wasn't running (new tab), assume active now
                if last_active_js == 0:
                    last_active_js = now * 1000
                
                last_active_sec = last_active_js / 1000
                idle_seconds = now - last_active_sec
                
                # Run HPCE Analysis
                confidence, fingerprint = self.run_hpce_analysis(hpce_raw, idle_seconds)
                
                logger.debug(f"HPCE: {title[:20]}... | [{fingerprint}] | Conf: {confidence*100:.1f}%")

                # Purge Threshold: < 5% Confidence
                if confidence < 0.05:
                    if not dry_run:
                        # Capture data before closing
                        purged_tabs.append({
                            "title": title,
                            "url": url,
                            "timestamp": datetime.now().isoformat(),
                            "fingerprint": fingerprint
                        })
                        page.close()
                        logger.info(f"Purged [{fingerprint}]: {title}")
                    else:
                        logger.info(f"[Dry Run] HPCE would purge: {title}")
                else:
                    keep_tabs.append(title)
                    
            except Exception as e:
                logger.error(f"Error scanning page: {e}")

        if purged_tabs and not dry_run:
            self.storage.save_tabs(purged_tabs)
            
        logger.info(f"Scan complete. Purged: {len(purged_tabs)}. Active: {len(keep_tabs)}")

