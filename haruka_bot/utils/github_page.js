function removeExtraDoms() {
    const doms = [
        '.js-header-wrapper',
        '.gh-header-actions',
        'nav.js-repo-nav',
        '.Layout-sidebar',
        '.discussion-timeline-actions',
        '.footer'
    ];

    doms.forEach(domTag => {
        const domDel = document.querySelector(domTag);
        domDel && domDel.remove()
    })

    // 让主讨论区覆盖整个宽度
    let layout = document.querySelector('div.Layout');
    layout && (layout.style.display = 'block');

    /**
     * 底部加一些空白
     * desc: playwright的bounding_box不会计算 border,margin, 因此需要多放一个
     */
    for(let i = 0; i < 2; i++)
    {
        let eleBottom =  document.createElement('div');
        eleBottom.style.clear = 'both';
        eleBottom.style.marginBottom = '30px';
        document.body.append(eleBottom);
    }

    // pull/01/files#diff-... 页面会被滚动到选中行，需要给它复位
    document.documentElement.scrollTop = 0;
}