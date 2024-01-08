function removeExtraDoms() {
    const doms = [
        '.js-header-wrapper',
        '.gh-header-actions',
        // '#repos-sticky-header',
        'nav.js-repo-nav',
        '.Layout-sidebar',
        '.discussion-timeline-actions',
        '.footer'
    ];

    doms.forEach(domTag => {
        const domDel = document.querySelector(domTag);
        domDel && domDel.remove()
    });

    // 让主讨论区覆盖整个宽度
    let layout = document.querySelector('div.Layout');
    layout && (layout.style.display = 'block');

    // 移除 file-tree
    let fileTree = document.getElementById('repos-file-tree');
    try {
        fileTree && (fileTree.parentElement.parentElement.parentElement.parentElement.remove());
    } catch(e){}
    
    // 移除搜索框
    let searchBox = document.getElementById('StickyHeader');
    try {
        searchBox && (searchBox.firstChild.firstChild.childNodes[1].remove());
    } catch(e){}

    // 移除 Sponsor 和 Notifications
    let pagehead_actions = document.querySelector('ul.pagehead-actions');
    if (pagehead_actions) {
        let lis = pagehead_actions.querySelectorAll('li');
        for(let i = lis.length - 1; i >= 0; i--) {
            let li = lis[i];
            if(['Sponsor', 'Notifications'].includes(li.innerText.trim())) {
                li.remove();
            }
        }
    }

    /**
     * header 相关的节点都有两套，所以需要查找并移除两次(一个是浮动的，一个是页面内的)
     */


    // 移除 react-tree-toggle-button-with-indicator
    try {
        
        document.querySelector('button.react-tree-toggle-button-with-indicator').parentNode.parentNode.remove();
        document.querySelector('button.react-tree-toggle-button-with-indicator').parentNode.parentNode.remove();
    } catch(e){}

    // 移除 copy path 图标
    try {
        document.querySelector('svg.octicon-copy').parentNode.remove();
        document.querySelector('svg.octicon-copy').parentNode.remove();
    } catch(e){}

    // 移除 history 链接
    let history = document.querySelector('a.react-last-commit-history-group');
    history && history.remove();

    // 移除代码框右上角的控制按钮组
    let code_actions = document.querySelector('div.react-blob-header-edit-and-raw-actions');
    code_actions && code_actions.parentNode.remove();
    

    // 移除右边的 Symbol 面板
    let symbolPane = document.getElementById('symbols-pane');
    if(symbolPane) {
        try {
            let paneParent = symbolPane.parentNode;
            let paneSpliter = paneParent.previousSibling;
            paneParent && paneParent.remove();
            paneSpliter && paneSpliter.remove();
        } catch(e){}
    }

    // 底部加一些空白
    {
        let eleBottom =  document.createElement('div');
        eleBottom.style.clear = 'both';
        eleBottom.style.marginBottom = '30px';
        document.body.append(eleBottom);
    }

    // pull/01/files#diff-... 页面会被滚动到选中行，需要给它复位
    document.documentElement.scrollTop = 0;
    
    // playwright 截长图中间会空白，因此把页面高度返回
    return document.documentElement.scrollHeight;
}