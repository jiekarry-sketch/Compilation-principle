// static/js/app.js
document.addEventListener('DOMContentLoaded', function() {
    // DOM元素引用
    const analyzeBtn = document.getElementById('analyzeBtn');
    const resetBtn = document.getElementById('resetBtn');
    const grammarInput = document.getElementById('grammarInput');
    const testInputs = document.getElementById('testInputs');
    const testCount = document.getElementById('testCount');
    const loading = document.getElementById('loading');
    const resultsArea = document.getElementById('resultsArea');
    const grammarResult = document.getElementById('grammarResult');
    const resultsContainer = document.getElementById('resultsContainer');
    const downloadImageBtn = document.getElementById('downloadImageBtn');

    // 更新测试用例计数
    function updateTestCount() {
        const inputs = testInputs.value.split('\n').filter(line => line.trim());
        testCount.textContent = inputs.length;
        if (inputs.length > 0) {
            testCount.className = 'badge bg-primary ms-2';
        } else {
            testCount.className = 'badge bg-secondary ms-2';
        }
    }

    // 初始化计数
    updateTestCount();

    // 监听测试输入变化
    testInputs.addEventListener('input', updateTestCount);

    // 示例文法按钮点击事件
    document.querySelectorAll('.example-btn').forEach(button => {
        button.addEventListener('click', function() {
            const grammar = this.getAttribute('data-grammar').replace(/&#10;/g, '\n');
            grammarInput.value = grammar;
            // 清空测试输入
            testInputs.value = '';
            updateTestCount();
        });
    });

    // 分析按钮点击事件
    analyzeBtn.addEventListener('click', async function() {
        const grammarText = grammarInput.value.trim();
        if (!grammarText) {
            showError('请输入文法规则！');
            return;
        }

        // 获取测试输入 - 只获取非空行
        const inputs = testInputs.value.split('\n')
            .map(line => line.trim())
            .filter(line => line);

        // 显示加载动画
        loading.style.display = 'block';
        analyzeBtn.disabled = true;
        analyzeBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>分析中...';

        try {
            const response = await fetch('/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    grammar: grammarText,
                    inputs: inputs
                })
            });

            const data = await response.json();

            if (response.ok) {
                // 检查是否有文法错误
                if (data.has_grammar_errors && data.grammar_errors) {
                    showGrammarErrors(data.grammar_errors);
                } else {
                    displayResults(data);
                }
            } else {
                // 检查是否是文法解析错误
                if (data.grammar_errors) {
                    showGrammarErrors(data.grammar_errors);
                } else {
                    showError(data.error || '分析失败');
                }
            }
        } catch (error) {
            showError('网络错误: ' + error.message);
            console.error('分析错误:', error);
        } finally {
            loading.style.display = 'none';
            analyzeBtn.disabled = false;
            analyzeBtn.innerHTML = '<i class="fas fa-play me-2"></i>开始分析';
        }
    });

    // 重置按钮 - 修正语法错误
    resetBtn.addEventListener('click', function() {
        grammarInput.value = '';
        testInputs.value = '';
        updateTestCount();
        resultsArea.style.display = 'flex';
        grammarResult.style.display = 'none';
        resultsContainer.style.display = 'none';
        document.getElementById('parsingTable').innerHTML = '';
        document.getElementById('testResults').innerHTML = '';
    });

    // 图片下载按钮
    downloadImageBtn.addEventListener('click', function() {
        const dfaImage = document.getElementById('modalDfaImage');
        if (dfaImage && dfaImage.src) {
            const link = document.createElement('a');
            link.href = dfaImage.src;
            link.download = 'lr0-dfa-graph.png';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    });

    // 显示错误
    function showError(message) {
        resultsArea.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <strong>错误:</strong> ${message}
            </div>
        `;
        resultsArea.style.display = 'flex';
        grammarResult.style.display = 'none';
        resultsContainer.style.display = 'none';
    }

    // 显示文法错误
    function showGrammarErrors(errors) {
        // 构建错误信息HTML
        let errorsHtml = `
            <div class="alert alert-warning">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <strong>文法解析错误：</strong>
                <ul class="mb-0 mt-2">
        `;

        errors.forEach(error => {
            errorsHtml += `<li>${error}</li>`;
        });

        errorsHtml += `
                </ul>
                <div class="mt-3">
                    <strong>使用说明：</strong>
                    <ul class="mb-0">
                        <li>空串必须使用 <code>@</code> 表示，例如：<code>A -> @</code></li>
                        <li>不要使用空的右部，例如：<code>A -> </code>（错误）</li>
                    </ul>
                </div>
            </div>
        `;

        // 显示在结果区域
        resultsArea.innerHTML = errorsHtml;
        resultsArea.style.display = 'flex';
        grammarResult.style.display = 'none';
        resultsContainer.style.display = 'none';
    }

    // 渲染分析表
    function renderParsingTable(tableData, conflictStateIds = []) {
        const table = document.getElementById('parsingTable');
        table.innerHTML = '';

        // 如果没有数据，显示提示
        if (!tableData || !tableData.headers || !tableData.rows) {
            table.innerHTML = '<tr><td colspan="100" class="text-center text-muted py-5">暂无分析表数据</td></tr>';
            return;
        }

        // 获取表头
        const headers = tableData.headers;
        const rows = tableData.rows;

        // 查找 Action 和 Goto 的分界点
        // 假设前几列是终结符（包括 #），后面是非终结符
        const hasHash = headers.includes('#');

        let actionCount = hasHash ? headers.indexOf('#') + 1 : headers.length;

        // 如果找不到 #，则假设所有符号列都是 Action
        if (!hasHash) {
            // 找到第一个非终结符（大写字母）的位置
            for (let i = 1; i < headers.length; i++) {
                if (headers[i] && headers[i].length === 1 && headers[i] === headers[i].toUpperCase()) {
                    actionCount = i;
                    break;
                }
            }
        }

        // 创建表头
        const thead = document.createElement('thead');

        // 第一行表头：分组标题
        const groupRow = document.createElement('tr');

        // State 列
        const stateGroup = document.createElement('th');
        stateGroup.textContent = 'State';
        stateGroup.className = 'state-header table-header';
        stateGroup.rowSpan = 2;
        groupRow.appendChild(stateGroup);

        // Action 分组
        const actionGroup = document.createElement('th');
        actionGroup.textContent = 'ACTION';
        actionGroup.className = 'action-header table-header';
        actionGroup.colSpan = actionCount - 1; // 减去 State 列
        groupRow.appendChild(actionGroup);

        // Goto 分组
        const gotoGroup = document.createElement('th');
        gotoGroup.textContent = 'GOTO';
        gotoGroup.className = 'goto-header table-header';
        gotoGroup.colSpan = headers.length - actionCount;
        groupRow.appendChild(gotoGroup);

        thead.appendChild(groupRow);

        // 第二行表头：具体符号
        const symbolRow = document.createElement('tr');

        // 添加终结符列（从第二个开始，跳过 State）
        for (let i = 1; i < actionCount; i++) {
            const th = document.createElement('th');
            th.textContent = headers[i];
            th.className = 'table-header';
            symbolRow.appendChild(th);
        }

        // 添加非终结符列
        for (let i = actionCount; i < headers.length; i++) {
            const th = document.createElement('th');
            th.textContent = headers[i];
            th.className = 'table-header';
            symbolRow.appendChild(th);
        }

        thead.appendChild(symbolRow);
        table.appendChild(thead);

        // 创建表格主体
        const tbody = document.createElement('tbody');

        rows.forEach((row, rowIndex) => {
            const tr = document.createElement('tr');

            // 标记冲突状态
            const isConflict = conflictStateIds && conflictStateIds.includes(rowIndex);
            if (isConflict) {
                tr.style.backgroundColor = 'rgba(230, 57, 70, 0.1)';
            }

            // 添加每一列数据
            row.forEach((cell, cellIndex) => {
                const td = document.createElement('td');

                // State 列特殊处理
                if (cellIndex === 0) {
                    td.className = 'state-cell';
                    td.textContent = cell;
                } else {
                    // 格式化单元格内容
                    formatTableCell(td, cell);
                }

                tr.appendChild(td);
            });

            tbody.appendChild(tr);
        });

        table.appendChild(tbody);
    }

    // 格式化表格单元格内容
    function formatTableCell(td, cellText) {
        const text = cellText || '';

        if (!text.trim()) {
            td.innerHTML = '<span class="table-action action-empty">-</span>';
            return;
        }

        if (text === 'acc') {
            td.innerHTML = '<span class="table-action action-accept">acc</span>';
        } else if (text.startsWith('s')) {
            td.innerHTML = `<span class="table-action action-shift">${text}</span>`;
        } else if (text.startsWith('r')) {
            td.innerHTML = `<span class="table-action action-reduce">${text}</span>`;
        } else if (text.includes('/')) {
            // 冲突情况，如 s3/r1
            const parts = text.split('/');
            const badges = parts.map(part => {
                if (part.startsWith('s')) {
                    return `<span class="table-action action-shift me-1">${part}</span>`;
                } else if (part.startsWith('r')) {
                    return `<span class="table-action action-reduce me-1">${part}</span>`;
                } else if (part === 'acc') {
                    return `<span class="table-action action-accept me-1">${part}</span>`;
                } else {
                    return `<span class="badge bg-secondary me-1">${part}</span>`;
                }
            }).join('');
            td.innerHTML = `<div class="d-flex justify-content-center">${badges}</div>`;
        } else if (text === 'ERROR') {
            td.innerHTML = '<span class="table-action action-error">ERROR</span>';
        } else {
            td.textContent = text;
        }
    }

    // 渲染测试结果 - 不循环，只显示给出的测试串
    function renderTestResults(testResults) {
        const container = document.getElementById('testResults');
        container.innerHTML = '';

        if (!testResults || testResults.length === 0) {
            container.innerHTML = `
                <div class="alert alert-info">
                    <i class="fas fa-info-circle me-2"></i>
                    没有测试输入或文法存在冲突，无法进行测试
                </div>
            `;
            return;
        }

        // 只处理实际给出的测试串
        testResults.forEach((result, index) => {
            const statusClass = result.success ? 'status-success' : 'status-error';
            const statusIcon = result.success ? '✅' : '❌';
            const statusText = result.success ? '接受' : '拒绝';

            // 构建Trace表格行
            let traceRows = '';
            if (result.trace && result.trace.length > 0) {
                result.trace.forEach(step => {
                    // 确定动作徽章样式
                    let actionBadge = 'action-shift';
                    let actionText = step.action || '';

                    if (actionText.startsWith('s') && actionText !== 'acc') {
                        actionBadge = 'action-shift';
                    } else if (actionText.startsWith('r')) {
                        actionBadge = 'action-reduce';
                    } else if (actionText === 'acc') {
                        actionBadge = 'action-accept';
                    } else if (actionText.includes('ERROR')) {
                        actionBadge = 'action-error';
                        actionText = 'ERROR';
                    }

                    traceRows += `
                    <tr>
                        <td class="text-center">${step.step || ''}</td>
                        <td class="font-monospace">${step.state_stack || ''}</td>
                        <td class="font-monospace">${step.symbol_stack || ''}</td>
                        <td class="font-monospace text-end">${step.input || ''}</td>
                        <td class="text-center"><span class="table-action ${actionBadge}">${actionText}</span></td>
                        <td class="text-center font-monospace">${step.goto || ''}</td>
                    </tr>`;
                });
            }

            const testCard = document.createElement('div');
            testCard.className = 'test-result-card';
            testCard.innerHTML = `
                <div class="test-result-header" data-bs-toggle="collapse" data-bs-target="#trace${index}">
                    <div>
                        <span class="status-badge ${statusClass}">
                            ${statusIcon} ${statusText}
                        </span>
                        <span class="ms-3"><strong>输入:</strong> <code>${result.input}</code></span>
                    </div>
                    <div>
                        <i class="fas fa-chevron-down"></i>
                    </div>
                </div>

                <div id="trace${index}" class="collapse">
                    <div class="test-result-content">
                        <div class="table-responsive">
                            <table class="trace-table">
                                <thead>
                                    <tr>
                                        <th>步骤</th>
                                        <th>状态栈</th>
                                        <th>符号栈</th>
                                        <th class="text-end">输入串</th>
                                        <th>ACTION</th>
                                        <th style="width: 80px;">GOTO</th>
                                    </tr>
                                </thead>
                                <tbody>${traceRows}</tbody>
                            </table>
                        </div>
                        <div class="p-3">
                            <div class="alert ${result.success ? 'alert-success' : 'alert-danger'} mb-0" role="alert">
                                <strong>分析结果:</strong> 输入串 <code>${result.input}</code>
                                ${result.success ? '是该文法的句子' : '不是该文法的句子'}。
                            </div>
                        </div>
                    </div>
                </div>
            `;

            container.appendChild(testCard);
        });
    }

    // 显示分析结果
    function displayResults(data) {
        console.log('收到分析结果:', data); // 调试信息

        // 隐藏初始提示，显示结果区域
        resultsArea.style.display = 'none';
        grammarResult.style.display = 'block';
        resultsContainer.style.display = 'block';

        // 文法判定结果
        if (data.is_lr0) {
            grammarResult.innerHTML = `
                <div class="result-indicator result-success">
                    <i class="fas fa-check-circle me-2"></i>
                    <strong>✅ 是 LR(0) 文法</strong> - 文法适合使用LR(0)分析器
                </div>
            `;
        } else {
            let conflictsHtml = '';
            if (data.conflicts && data.conflicts.length > 0) {
                conflictsHtml = `<div class="mt-3">
                    <h6 class="mb-2">检测到冲突:</h6>
                    <ul class="list-group list-group-flush">`;
                data.conflicts.forEach(conflict => {
                    conflictsHtml += `<li class="list-group-item border-0 py-1"><i class="fas fa-exclamation-triangle text-danger me-2"></i>${conflict}</li>`;
                });
                conflictsHtml += `</ul></div>`;
            }

            grammarResult.innerHTML = `
                <div class="result-indicator result-warning">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    <strong>❌ 不是 LR(0) 文法</strong>
                    ${conflictsHtml}
                </div>
            `;
        }

        // 文法内容
        let grammarHtml = '';
        if (data.grammar_info && data.grammar_info.productions) {
            data.grammar_info.productions.forEach((prod, index) => {
                // 处理右部显示
                let rightDisplay = prod.right;
                if (rightDisplay === '@' || rightDisplay === '') {
                    rightDisplay = 'ε';
                }

                // 特殊处理第0条产生式（拓广文法）
                let itemClass = 'grammar-item';
                if (index === 0) {
                    itemClass += ' augmented';
                }

                grammarHtml += `
                <div class="${itemClass}">
                    <span class="index">${index}.</span>
                    <span>${prod.left} → ${rightDisplay}</span>
                    ${index === 0 ? '<span class="badge bg-warning text-dark float-end">拓广文法</span>' : ''}
                </div>`;
            });
        }
        document.getElementById('grammarContent').innerHTML = grammarHtml;

        // DFA图
        if (data.dfa_image) {
            const dfaImage = document.getElementById('dfaImage');
            const modalDfaImage = document.getElementById('modalDfaImage');
            dfaImage.src = data.dfa_image;
            modalDfaImage.src = data.dfa_image;
        } else {
            document.getElementById('dfaContent').innerHTML =
                '<div class="alert alert-warning">DFA图生成失败，请检查文法是否正确</div>';
        }

        // 分析表
        if (data.table_data) {
            renderParsingTable(data.table_data, data.conflict_state_ids || []);
        } else {
            document.getElementById('tabTable').innerHTML =
                '<div class="alert alert-warning">分析表数据生成失败</div>';
        }

        // 测试结果 - 只显示给出的测试串
        if (data.test_results && data.test_results.length > 0) {
            renderTestResults(data.test_results);
        } else {
            document.getElementById('testResults').innerHTML = `
                <div class="alert alert-info">
                    <i class="fas fa-info-circle me-2"></i>
                    没有测试输入或文法存在冲突，无法进行测试
                </div>
            `;
        }

        // 默认激活第一个标签
        setTimeout(() => {
            const firstTab = document.querySelector('#resultsTab .nav-link');
            if (firstTab) {
                const tabTrigger = new bootstrap.Tab(firstTab);
                tabTrigger.show();
            }
        }, 100);
    }
});