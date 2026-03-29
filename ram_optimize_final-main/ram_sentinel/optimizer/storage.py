import json
import time
from pathlib import Path
from datetime import datetime
from ..core.config import settings
from ..core.logger import logger

class ReadLaterStorage:
    def __init__(self):
        self.base_dir = Path(settings.READ_LATER_DIR)
        self.json_path = self.base_dir / "index.json"
        
    def save_tabs(self, tabs: list):
        """
        Save a list of tabs to storage.
        tabs: List of dicts with 'title', 'url', 'timestamp'
        """
        if not tabs:
            return

        timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        day_str = datetime.now().strftime("%Y-%m-%d")
        dest_dir = self.base_dir / day_str
        dest_dir.mkdir(parents=True, exist_ok=True)

        # 1. Append to JSON index
        all_data = []
        if self.json_path.exists():
            try:
                with open(self.json_path, 'r', encoding='utf-8') as f:
                    all_data = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load existing index: {e}")
        
        # Add batch info
        batch_entry = {
            "batch_id": timestamp_str,
            "count": len(tabs),
            "tabs": tabs
        }
        all_data.append(batch_entry)
        
        with open(self.json_path, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, indent=2)

        # 2. Create Markdown Summary
        md_file = dest_dir / f"purged_{timestamp_str}.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(f"# Purged Tabs - {timestamp_str}\n\n")
            f.write(f"**Total Purged**: {len(tabs)}\n\n")
            for t in tabs:
                f.write(f"- [{t['title'] or 'No Title'}]({t['url']})\n")
        
        logger.info(f"Saved {len(tabs)} tabs to {md_file}")
