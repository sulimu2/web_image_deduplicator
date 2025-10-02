// 高级图片去重工具 - 前端JavaScript
class ImageDeduplicatorApp {
    constructor() {
        this.selectedGroups = new Set();
        this.currentGroups = {};
        this.init();
    }

    init() {
        this.bindEvents();
        this.updateThresholdDisplay();
    }

    bindEvents() {
        // 相似度阈值滑块事件
        document.getElementById('similarityThreshold').addEventListener('input', (e) => {
            this.updateThresholdDisplay();
        });

        // 键盘快捷键
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch(e.key) {
                    case 'a':
                        e.preventDefault();
                        this.selectAllGroups();
                        break;
                    case 'd':
                        e.preventDefault();
                        this.clearSelection();
                        break;
                }
            }
        });
    }

    updateThresholdDisplay() {
        const threshold = document.getElementById('similarityThreshold').value;
        document.getElementById('thresholdValue').textContent = threshold;
    }

    async startScan() {
        const targetDir = document.getElementById('targetDir').value.trim();
        const similarityThreshold = parseFloat(document.getElementById('similarityThreshold').value);
        const hashSize = parseInt(document.getElementById('hashSize').value);
        const recursive = document.getElementById('recursiveScan').checked;

        if (!targetDir) {
            this.showToast('请输入目标目录路径', 'error');
            return;
        }

        // 显示进度条
        this.showProgressSection();
        this.updateProgress(0, '开始扫描目录...');

        try {
            const response = await fetch('/api/scan', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    target_dir: targetDir,
                    similarity_threshold: similarityThreshold,
                    hash_size: hashSize,
                    recursive: recursive
                })
            });

            const result = await response.json();

            if (result.success) {
                this.updateProgress(100, '扫描完成！');
                setTimeout(() => {
                    this.displayResults(result.report, result.groups);
                }, 1000);
            } else {
                this.updateProgress(0, `扫描失败: ${result.error}`);
                this.showToast(`扫描失败: ${result.error}`, 'error');
            }
        } catch (error) {
            this.updateProgress(0, `网络错误: ${error.message}`);
            this.showToast(`网络错误: ${error.message}`, 'error');
        }
    }

    showProgressSection() {
        document.getElementById('progressSection').style.display = 'block';
        document.getElementById('resultsSection').style.display = 'none';
    }

    updateProgress(percent, text) {
        document.getElementById('progressFill').style.width = `${percent}%`;
        document.getElementById('progressText').textContent = text;
    }

    displayResults(report, groups) {
        this.currentGroups = groups;
        
        // 更新统计信息
        document.getElementById('totalGroups').textContent = report.summary.total_groups;
        document.getElementById('totalImages').textContent = report.summary.total_images;
        document.getElementById('spaceSavings').textContent = 
            `${(report.summary.estimated_space_saved / 1024 / 1024).toFixed(2)} MB`;

        // 显示结果区域
        document.getElementById('progressSection').style.display = 'none';
        document.getElementById('resultsSection').style.display = 'block';

        // 生成组列表
        this.renderGroupsList();
    }

    renderGroupsList() {
        const groupsList = document.getElementById('groupsList');
        groupsList.innerHTML = '';

        Object.keys(this.currentGroups).forEach(groupKey => {
            const group = this.currentGroups[groupKey];
            const groupCard = this.createGroupCard(groupKey, group);
            groupsList.appendChild(groupCard);
        });

        this.updateSelectionCount();
    }

    createGroupCard(groupKey, group) {
        const card = document.createElement('div');
        card.className = 'group-card';
        card.innerHTML = `
            <div class="group-header">
                <span class="group-title">${groupKey}</span>
                <input type="checkbox" class="group-checkbox" 
                       onchange="app.toggleGroupSelection('${groupKey}')">
            </div>
            <div class="group-images">
                ${this.createGroupImagesPreview(group)}
            </div>
            <div class="group-stats">
                <span>${group.length} 张图片</span>
                <span>${this.formatFileSize(this.calculateGroupSize(group))}</span>
            </div>
        `;

        // 添加点击事件查看详情
        card.addEventListener('click', (e) => {
            if (!e.target.classList.contains('group-checkbox')) {
                this.showGroupDetail(groupKey, group);
            }
        });

        return card;
    }

    createGroupImagesPreview(group) {
        // 只显示前3张图片作为预览
        const previewImages = group.slice(0, 3);
        return previewImages.map((img, index) => {
            // 处理图片路径：如果路径已经是绝对路径，直接使用；如果是相对路径，确保正确
            let imagePath = img.path;
            
            // 如果路径已经是绝对路径（以/开头），直接使用
            if (imagePath.startsWith('/')) {
                // 确保路径在项目根目录内
                const projectRoot = '/Volumes/T1/VSCODE-Project/douyin333';
                if (imagePath.startsWith(projectRoot)) {
                    // 如果路径包含项目根目录，使用相对路径
                    imagePath = imagePath.substring(projectRoot.length);
                    if (imagePath.startsWith('/')) {
                        imagePath = imagePath.substring(1);
                    }
                }
            }
            
            return `
                <img src="/api/image/${encodeURIComponent(imagePath)}" 
                     alt="预览图 ${index + 1}" 
                     class="group-image"
                     onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iODAiIGhlaWdodD0iODAiIHZpZXdCb3g9IjAgMCA4MCA4MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHJlY3Qgd2lkdGg9IjgwIiBoZWlnaHQ9IjgwIiBmaWxsPSIjRTVFNUU1Ii8+CjxwYXRoIGQ9Ik00MCA0MEM0My4zMTM3IDQwIDQ2IDM3LjMxMzcgNDYgMzRDNDYgMzAuNjg2MyA0My4zMTM3IDI4IDQwIDI4QzM2LjY4NjMgMjggMzQgMzAuNjg2MyAzNCAzNEMzNCAzNy4zMTM3IDM2LjY4NjMgNDAgNDAgNDBaIiBmaWxsPSIjOEE5MEE2Ii8+CjxwYXRoIGQ9Ik00MCA0NEM0Ni42Mjc0IDQ0IDUyIDM4LjYyNzQgNTIgMzJDNTIgMjUuMzcyNiA0Ni42Mjc0IDIwIDQwIDIwQzMzLjM3MjYgMjAgMjggMjUuMzcyNiAyOCAzMkMyOCAzOC42Mjc0IDMzLjM3MjYgNDQgNDAgNDRaIiBmaWxsPSIjNkM3QThEIi8+Cjwvc3ZnPgo='">
            `;
        }).join('');
    }

    calculateGroupSize(group) {
        return group.reduce((total, img) => total + img.file_size, 0);
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    toggleGroupSelection(groupKey) {
        if (this.selectedGroups.has(groupKey)) {
            this.selectedGroups.delete(groupKey);
        } else {
            this.selectedGroups.add(groupKey);
        }
        
        this.updateGroupCardSelection(groupKey);
        this.updateSelectionCount();
    }

    updateGroupCardSelection(groupKey) {
        const cards = document.querySelectorAll('.group-card');
        cards.forEach(card => {
            const title = card.querySelector('.group-title');
            if (title && title.textContent === groupKey) {
                if (this.selectedGroups.has(groupKey)) {
                    card.classList.add('selected');
                } else {
                    card.classList.remove('selected');
                }
            }
        });
    }

    updateSelectionCount() {
        document.getElementById('selectedCount').textContent = 
            `已选择 ${this.selectedGroups.size} 个组`;
    }

    selectAllGroups() {
        this.selectedGroups = new Set(Object.keys(this.currentGroups));
        this.updateAllGroupCardsSelection();
        this.updateSelectionCount();
    }

    clearSelection() {
        this.selectedGroups.clear();
        this.updateAllGroupCardsSelection();
        this.updateSelectionCount();
    }

    updateAllGroupCardsSelection() {
        const cards = document.querySelectorAll('.group-card');
        cards.forEach(card => {
            const title = card.querySelector('.group-title');
            const checkbox = card.querySelector('.group-checkbox');
            
            if (title && checkbox) {
                const isSelected = this.selectedGroups.has(title.textContent);
                card.classList.toggle('selected', isSelected);
                checkbox.checked = isSelected;
            }
        });
    }

    async deleteSelectedGroups() {
        if (this.selectedGroups.size === 0) {
            this.showToast('请先选择要删除的组', 'warning');
            return;
        }

        if (!confirm(`确定要删除选中的 ${this.selectedGroups.size} 个相似图片组吗？此操作不可撤销！`)) {
            return;
        }

        try {
            const response = await fetch('/api/delete/selected', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    group_keys: Array.from(this.selectedGroups)
                })
            });

            const result = await response.json();

            if (result.success) {
                this.showToast(`成功删除 ${result.result.files_deleted} 个文件`, 'success');
                
                // 更新界面
                this.selectedGroups.clear();
                this.displayResults(result.report, this.currentGroups);
                
            } else {
                this.showToast(`删除失败: ${result.error}`, 'error');
            }
        } catch (error) {
            this.showToast(`网络错误: ${error.message}`, 'error');
        }
    }

    async deleteAllGroups() {
        if (Object.keys(this.currentGroups).length === 0) {
            this.showToast('没有可删除的相似组', 'warning');
            return;
        }

        if (!confirm(`确定要删除所有 ${Object.keys(this.currentGroups).length} 个相似图片组吗？此操作不可撤销！`)) {
            return;
        }

        try {
            const response = await fetch('/api/delete/all', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            const result = await response.json();

            if (result.success) {
                this.showToast(`成功删除所有重复文件，释放 ${this.formatFileSize(result.result.space_saved)} 空间`, 'success');
                
                // 清空界面
                this.selectedGroups.clear();
                this.currentGroups = {};
                document.getElementById('resultsSection').style.display = 'none';
                
            } else {
                this.showToast(`删除失败: ${result.error}`, 'error');
            }
        } catch (error) {
            this.showToast(`网络错误: ${error.message}`, 'error');
        }
    }

    async showGroupDetail(groupKey, group) {
        try {
            const response = await fetch(`/api/group/${groupKey}`);
            const groupDetail = await response.json();

            if (groupDetail.error) {
                this.showToast(`加载详情失败: ${groupDetail.error}`, 'error');
                return;
            }

            this.renderGroupModal(groupDetail);
        } catch (error) {
            this.showToast(`网络错误: ${error.message}`, 'error');
        }
    }

    renderGroupModal(groupDetail) {
        const modalBody = document.getElementById('modalBody');
        modalBody.innerHTML = `
            <div class="group-detail">
                <div class="detail-header">
                    <h4>${groupDetail.key} - ${groupDetail.images.length} 张相似图片</h4>
                </div>
                <div class="image-grid">
                    ${groupDetail.images.map((img, index) => {
                        // 处理图片路径：如果路径已经是绝对路径，直接使用；如果是相对路径，确保正确
                        let imagePath = img.path;
                        
                        // 如果路径已经是绝对路径（以/开头），直接使用
                        if (imagePath.startsWith('/')) {
                            // 确保路径在项目根目录内
                            const projectRoot = '/Volumes/T1/VSCODE-Project/douyin333';
                            if (imagePath.startsWith(projectRoot)) {
                                // 如果路径包含项目根目录，使用相对路径
                                imagePath = imagePath.substring(projectRoot.length);
                                if (imagePath.startsWith('/')) {
                                    imagePath = imagePath.substring(1);
                                }
                            }
                        }
                        
                        return `
                            <div class="image-item ${img.is_representative ? 'representative' : ''}">
                                <img src="/api/image/${encodeURIComponent(imagePath)}" 
                                     alt="图片 ${index + 1}" 
                                     class="image-preview"
                                     onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTUwIiBoZWlnaHQ9IjEyMCIgdmlld0JveD0iMCAwIDE1MCAxMjAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIxNTAiIGhlaWdodD0iMTIwIiBmaWxsPSIjRTVFNUU1Ii8+CjxwYXRoIGQ9Ik03NSA2MEM3OC4zMTM3IDYwIDgxIDU3LjMxMzcgODEgNTNDODEgNDkuNjg2MyA3OC4zMTM3IDQ3IDc1IDQ3QzcxLjY4NjMgNDcgNjkgNDkuNjg2MyA2OSA1M0M2OSA1Ny4zMTM3IDcxLjY4NjMgNjAgNzUgNjBaIiBmaWxsPSIjOEE5MEE2Ii8+CjxwYXRoIGQ9Ik03NSA3MEM4NC4zODg4IDcwIDkyIDYyLjM4ODggOTIgNTNDOTIgNDMuNjExMiA4NC4zODg4IDM2IDc1IDM2QzY1LjYxMTIgMzYgNTggNDMuNjExMiA1OCA1M0M1OCA2Mi4zODg4IDY1LjYxMTIgNzAgNzUgNzBaIiBmaWxsPSIjNkM3QThEIi8+Cjwvc3ZnPgo='">
                                <div class="image-info">
                                    <div>${this.formatFileSize(img.file_size)}</div>
                                    <div>${img.is_representative ? '✓ 保留' : '✗ 删除'}</div>
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
        `;

        document.getElementById('groupModal').style.display = 'block';
    }

    closeModal() {
        document.getElementById('groupModal').style.display = 'none';
    }

    showToast(message, type = 'info') {
        const toastContainer = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <i class="fas fa-${this.getToastIcon(type)}"></i>
            ${message}
        `;

        toastContainer.appendChild(toast);

        // 自动移除
        setTimeout(() => {
            toast.remove();
        }, 5000);
    }

    getToastIcon(type) {
        switch(type) {
            case 'success': return 'check-circle';
            case 'error': return 'exclamation-circle';
            case 'warning': return 'exclamation-triangle';
            default: return 'info-circle';
        }
    }
}

// 全局函数供HTML调用
function browseDirectory() {
    // 创建隐藏的文件输入元素
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.webkitdirectory = true; // 允许选择目录
    fileInput.multiple = true;
    
    fileInput.addEventListener('change', (event) => {
        if (event.target.files.length > 0) {
            // 获取选择的目录路径（第一个文件的路径）
            const firstFile = event.target.files[0];
            const directoryPath = firstFile.webkitRelativePath.split('/')[0];
            
            // 设置目录路径到输入框（使用相对路径，不带./前缀）
            document.getElementById('targetDir').value = directoryPath;
            
            // 显示选择结果
            app.showToast(`已选择目录: ${directoryPath} (包含 ${event.target.files.length} 个文件)`, 'success');
        }
    });
    
    fileInput.addEventListener('cancel', () => {
        app.showToast('目录选择已取消', 'info');
    });
    
    // 触发文件选择
    fileInput.click();
}

function startScan() {
    app.startScan();
}

function selectAllGroups() {
    app.selectAllGroups();
}

function clearSelection() {
    app.clearSelection();
}

function deleteSelectedGroups() {
    app.deleteSelectedGroups();
}

function deleteAllGroups() {
    app.deleteAllGroups();
}

function closeModal() {
    app.closeModal();
}

// 初始化应用
const app = new ImageDeduplicatorApp();