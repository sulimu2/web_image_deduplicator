#!/usr/bin/env python3
"""
Docker启动脚本
"""

import os
import sys
from web_image_deduplicator.app import app

if __name__ == '__main__':
    # 获取端口，默认为5010
    port = int(os.environ.get('PORT', 5010))
    
    # 启动Flask应用
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False
    )