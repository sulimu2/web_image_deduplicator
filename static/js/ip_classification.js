// 智能IP表情图片分类系统 - 前端JavaScript
class IPClassificationApp {
    constructor() {
        this.classificationResults = {};
        this.currentImageDetails = {};
        this.init();
    }

    init() {
        this.bindEvents();
        this.updateThresholdDisplay();
    }

    bindEvents() {
        // 相似度阈值滑块事件
        document.getElementById('ipSimilarityThreshold').addEventListener('input', (e) => {
            this.updateThresholdDisplay();
        });

        // 键盘快捷键
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch(e.key) {
                    case 'Enter':
                        e.preventDefault();
                        this.startIPClassification();
                        break;
                }
            }
        });
    }

    updateThresholdDisplay() {
        const threshold = parseFloat(document.getElementById('ipSimilarityThreshold').value).toFixed(2);
        document.getElementById('ipThresholdValue').textContent = threshold;
    }

    async startIPClassification() {
        const targetDir = document.getElementById('targetDir').value.trim();
        const targetIp = document.getElementById('targetIp').value.trim();
        const similarityThreshold = parseFloat(document.getElementById('ipSimilarityThreshold').value);
        const recursive = document.getElementById('recursiveScan').checked;

        if (!targetDir) {
            this.showToast('请输入目标目录路径', 'error');
            return;
        }

        if (!targetIp) {
            this.showToast('请输入目标IP名称', 'error');
            return;
        }

        // 显示进度条
        this.showProgressSection();
        this.updateProgress(0, '初始化分类器...');

        try {
            const response = await fetch('/api/ip-classification/scan', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    target_dir: targetDir,
                    target_ip: targetIp,
                    similarity_threshold: similarityThreshold,
                    recursive: recursive
                })
            });

            const result = await response.json();

            if (result.success) {
                this.updateProgress(100, '分类完成！');
                setTimeout(() => {
                    this.displayClassificationResults(result.report);
                }, 1000);
            } else {
                this.updateProgress(0, `分类失败: ${result.error}`);
                this.showToast(`分类失败: ${result.error}`, 'error');
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

    displayClassificationResults(report) {
        this.classificationResults = report;
        
        // 更新统计信息
        document.getElementById('targetIpCount').textContent = report.summary.target_ip_count;
        document.getElementById('unrelatedCount').textContent = report.summary.unrelated_count;
        document.getElementById('totalImages').textContent = report.summary.total_images;

        // 显示分类结果
        this.renderClassificationDetails();

        // 显示结果区域
        document.getElementById('progressSection').style.display = 'none';
        document.getElementById('resultsSection').style.display = 'block';
    }

    renderClassificationDetails() {
        // 渲染目标IP相关图片
        this.renderTargetIpImages();
        
        // 渲染无关图片
        this.renderUnrelatedImages();
        
        // 渲染其他分类
        this.renderOtherCategories();
    }

    renderTargetIpImages() {
        const container = document.getElementById('targetIpImages');
        container.innerHTML = '';

        const targetIpResults = this.classificationResults.detailed_results[this.getTargetIpName()];
        if (!targetIpResults || targetIpResults.count === 0) {
            container.innerHTML = '<p class="no-images">未发现目标IP相关图片</p>';
            return;
        }

        // 显示前6张图片作为预览
        const previewImages = targetIpResults.images.slice(0, 6);
        
        previewImages.forEach((img, index) => {
            const imageCard = this.createImageCard(img, 'target-ip');
            container.appendChild(imageCard);
        });

        // 如果图片数量超过6张，显示查看更多按钮
        if (targetIpResults.images.length > 6) {
            const moreButton = document.createElement('button');
            moreButton.className = 'btn btn-outline more-images-btn';
            moreButton.innerHTML = `<i class="fas fa-eye"></i> 查看全部 ${targetIpResults.images.length} 张图片`;
            moreButton.onclick = () => this.showAllImages(this.getTargetIpName());
            container.appendChild(moreButton);
        }
    }

    renderUnrelatedImages() {
        const container = document.getElementById('unrelatedImages');
        container.innerHTML = '';

        const unrelatedResults = this.classificationResults.detailed_results['unrelated'];
        if (!unrelatedResults || unrelatedResults.count === 0) {
            container.innerHTML = '<p class="no-images">未发现无关图片</p>';
            return;
        }

        // 显示前6张图片作为预览
        const previewImages = unrelatedResults.images.slice(0, 6);
        
        previewImages.forEach((img, index) => {
            const imageCard = this.createImageCard(img, 'unrelated');
            container.appendChild(imageCard);
        });

        if (unrelatedResults.images.length > 6) {
            const moreButton = document.createElement('button');
            moreButton.className = 'btn btn-outline more-images-btn';
            moreButton.innerHTML = `<i class="fas fa-eye"></i> 查看全部 ${unrelatedResults.images.length} 张图片`;
            moreButton.onclick = () => this.showAllImages('unrelated');
            container.appendChild(moreButton);
        }
    }

    renderOtherCategories() {
        const container = document.getElementById('otherCategories');
        container.innerHTML = '';

        const targetIpName = this.getTargetIpName();
        const otherCategories = Object.entries(this.classificationResults.detailed_results)
            .filter(([category]) => category !== targetIpName && category !== 'unrelated');

        if (otherCategories.length === 0) {
            container.innerHTML = '<p class="no-categories">无其他分类</p>';
            return;
        }

        otherCategories.forEach(([category, results]) => {
            const categoryElement = document.createElement('div');
            categoryElement.className = 'other-category';
            categoryElement.innerHTML = `
                <h4>${category} <span class="count-badge">${results.count}</span></h4>
                <div class="category-preview">
                    ${results.images.slice(0, 3).map(img => 
                        `<img src="/api/ip-classification/image/${encodeURIComponent(img.file_path)}" 
                              alt="${img.file_name}" 
                              class="preview-thumb"
                              onclick="app.showImageDetail('${category}', ${results.images.indexOf(img)})">`
                    ).join('')}
                </div>
                <button class="btn btn-outline btn-sm" onclick="app.showAllImages('${category}')">
                    查看全部
                </button>
            `;
            container.appendChild(categoryElement);
        });
    }

    createImageCard(imageInfo, category) {
        const card = document.createElement('div');
        card.className = 'image-card';
        card.innerHTML = `
            <div class="image-container">
                <img src="/api/ip-classification/image/${encodeURIComponent(imageInfo.file_path)}" 
                     alt="${imageInfo.file_name}" 
                     class="classification-image"
                     onclick="app.showImageDetail('${category}', ${this.getImageIndex(category, imageInfo.file_path)})">
                <div class="image-overlay">
                    <div class="confidence-badge">${(imageInfo.confidence * 100).toFixed(1)}%</div>
                </div>
            </div>
            <div class="image-info">
                <div class="file-name">${imageInfo.file_name}</div>
                <div class="file-size">${this.formatFileSize(imageInfo.file_size)}</div>
                <div class="best-match">匹配: ${imageInfo.best_match || '未知'}</div>
            </div>
        `;
        return card;
    }

    getTargetIpName() {
        return document.getElementById('targetIp').value.trim() || 'default';
    }

    getImageIndex(category, filePath) {
        const results = this.classificationResults.detailed_results[category];
        if (!results) return -1;
        
        return results.images.findIndex(img => img.file_path === filePath);
    }

    async showImageDetail(category, imageIndex) {
        const results = this.classificationResults.detailed_results[category];
        if (!results || !results.images[imageIndex]) {
            this.showToast('图片信息加载失败', 'error');
            return;
        }

        const imageInfo = results.images[imageIndex];
        this.currentImageDetails = imageInfo;

        const modalBody = document.getElementById('imageDetailBody');
        modalBody.innerHTML = this.createImageDetailContent(imageInfo);

        document.getElementById('imageDetailModal').style.display = 'block';
    }

    createImageDetailContent(imageInfo) {
        return `
            <div class="image-detail-container">
                <div class="detail-image-section">
                    <img src="/api/ip-classification/image/${encodeURIComponent(imageInfo.file_path)}" 
                         alt="${imageInfo.file_name}" 
                         class="detail-image">
                </div>
                
                <div class="detail-info-section">
                    <h4>文件信息</h4>
                    <div class="info-grid">
                        <div class="info-item">
                            <label>文件名:</label>
                            <span>${imageInfo.file_name}</span>
                        </div>
                        <div class="info-item">
                            <label>文件大小:</label>
                            <span>${this.formatFileSize(imageInfo.file_size)}</span>
                        </div>
                        <div class="info-item">
                            <label>图片尺寸:</label>
                            <span>${imageInfo.image_size ? imageInfo.image_size.join('×') : '未知'}</span>
                        </div>
                        <div class="info-item">
                            <label>分类置信度:</label>
                            <span class="confidence-value">${(imageInfo.confidence * 100).toFixed(1)}%</span>
                        </div>
                    </div>
                    
                    <h4>分类依据</h4>
                    <div class="classification-reason">
                        <strong>最佳匹配:</strong> ${imageInfo.best_match || '未知'}
                    </div>
                    
                    <h4>检测到的对象</h4>
                    <div class="detected-objects">
                        ${imageInfo.detected_objects && imageInfo.detected_objects.length > 0 
                            ? imageInfo.detected_objects.map(obj => 
                                `<span class="object-tag">${obj.label} (${(obj.confidence * 100).toFixed(1)}%)</span>`
                            ).join('')
                            : '<p>未检测到明显对象</p>'
                        }
                    </div>
                    
                    <div class="detail-actions">
                        <button class="btn btn-outline" onclick="app.reclassifyImage()">
                            <i class="fas fa-redo"></i> 重新分类
                        </button>
                        <button class="btn btn-outline" onclick="app.changeCategory()">
                            <i class="fas fa-exchange-alt"></i> 调整分类
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    closeImageModal() {
        document.getElementById('imageDetailModal').style.display = 'none';
    }

    async organizeResults() {
        document.getElementById('organizeModal').style.display = 'block';
    }

    closeOrganizeModal() {
        document.getElementById('organizeModal').style.display = 'none';
    }

    async confirmOrganize() {
        const baseDir = document.getElementById('organizeBaseDir').value;
        const dryRun = document.getElementById('dryRunMode').checked;

        try {
            const response = await fetch('/api/ip-classification/organize', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    config: { base_dir: baseDir },
                    dry_run: dryRun
                })
            });

            const result = await response.json();

            if (result.success) {
                const action = dryRun ? '模拟整理' : '整理';
                this.showToast(`${action}完成: 处理了 ${result.result.files_moved} 个文件`, 'success');
                this.closeOrganizeModal();
            } else {
                this.showToast(`整理失败: ${result.error}`, 'error');
            }
        } catch (error) {
            this.showToast(`网络错误: ${error.message}`, 'error');
        }
    }

    async exportReport() {
        try {
            // 创建报告数据
            const reportData = {
                summary: this.classificationResults.summary,
                detailed_results: this.classificationResults.detailed_results,
                export_time: new Date().toISOString()
            };

            // 创建下载链接
            const dataStr = JSON.stringify(reportData, null, 2);
            const dataBlob = new Blob([dataStr], {type: 'application/json'});
            const url = URL.createObjectURL(dataBlob);
            
            const link = document.createElement('a');
            link.href = url;
            link.download = `ip_classification_report_${new Date().getTime()}.json`;
            link.click();
            
            URL.revokeObjectURL(url);
            
            this.showToast('报告导出成功', 'success');
        } catch (error) {
            this.showToast(`导出失败: ${error.message}`, 'error');
        }
    }

    manualAdjust() {
        this.showToast('手动调整功能开发中', 'info');
    }

    reclassifyImage() {
        this.showToast('重新分类功能开发中', 'info');
    }

    changeCategory() {
        this.showToast('调整分类功能开发中', 'info');
    }

    showAllImages(category) {
        this.showToast(`查看${category}分类的全部图片`, 'info');
        // 这里可以扩展为显示该分类的所有图片的模态框或新页面
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
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
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.webkitdirectory = true;
    fileInput.multiple = true;
    
    fileInput.addEventListener('change', (event) => {
        if (event.target.files.length > 0) {
            const firstFile = event.target.files[0];
            const directoryPath = firstFile.webkitRelativePath.split('/')[0];
            document.getElementById('targetDir').value = directoryPath;
            app.showToast(`已选择目录: ${directoryPath} (包含 ${event.target.files.length} 个文件)`, 'success');
        }
    });
    
    fileInput.click();
}

function startIPClassification() {
    app.startIPClassification();
}

function organizeResults() {
    app.organizeResults();
}

function closeOrganizeModal() {
    app.closeOrganizeModal();
}

function confirmOrganize() {
    app.confirmOrganize();
}

function exportReport() {
    app.exportReport();
}

function manualAdjust() {
    app.manualAdjust();
}

function closeImageModal() {
    app.closeImageModal();
}

// 初始化应用
const app = new IPClassificationApp();