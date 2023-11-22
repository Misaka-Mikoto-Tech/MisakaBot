function removeExtraDoms() {
    const doms = [
        '.lite-topbar',
        '.ad-wrap',
        '.lite-page-editor',
        '.video-player',
        '.wrap',
    ];

    doms.forEach(domTag => {
        const domDel = document.querySelector(domTag);
        domDel && domDel.remove()
    });

    // 移除评论区及其tab
    let comment = document.querySelector('.comment-content');
    try{
        comment && (comment.parentElement.remove());
    }catch(e){}

    // 清除多余的上边界
    let main = document.querySelector('.main');
    try{
        main && (main.style.marginTop = 0);
    }catch(e){}

    // 返回清除多余节点后的整体区域Rect
    return document.querySelector('.lite-page-wrap').getBoundingClientRect();
}