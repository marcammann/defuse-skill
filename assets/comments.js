/* Local annotations. Anchors refer to document text, never injected user HTML. */
(() => {
  const docId = document.querySelector('meta[name="defuse-document-id"]').content;
  const storageKey = `defuse-comments-v1:${docId}`;
  const rail = document.querySelector('#comment-rail');
  const toggle = document.querySelector('#comments-toggle');
  const cards = document.querySelector('#comment-list');
  const editor = document.querySelector('#comment-editor');
  const input = document.querySelector('#comment-input');
  const quote = document.querySelector('#comment-draft-quote');
  const status = document.querySelector('#comment-storage');
  const selectionButton = document.querySelector('#selection-comment');
  let comments = [], draft = null, pending = null, activeId = null, saved = false;
  const excluded = 'button,input,textarea,select,script,style,nav,.controls,.source-tools';
  const containers = new Map();
  document.querySelectorAll('.original-block').forEach(block => {
    for (const mode of ['rendered', 'raw']) {
      const node = block.querySelector(mode === 'raw' ? '.source-raw' : '.source-rendered');
      containers.set(`${block.id}:${mode}`, {node, side:'original', mode, label:'Original document'});
    }
  });
  document.querySelectorAll('#overview,.reading-section,#closing,.summary-pane footer').forEach((node, i) => {
    containers.set(`reading:${node.id || 'footer'}`, {node, side:'reading', label:node.querySelector('h1,h2')?.textContent || 'About this reading edition'});
  });
  function textMap(container) {
    const walker = document.createTreeWalker(container.node, NodeFilter.SHOW_TEXT, {acceptNode(node) {
      const parent = node.parentElement;
      if (!parent || parent.closest(excluded)) return NodeFilter.FILTER_REJECT;
      if (container.side === 'reading' && parent.closest('#original-document')) return NodeFilter.FILTER_REJECT;
      return NodeFilter.FILTER_ACCEPT;
    }});
    const nodes = [];
    let text = '', node;
    while ((node = walker.nextNode())) { nodes.push({node, start:text.length}); text += node.data; }
    return {text, nodes};
  }
  function resolve(anchor) {
    const container = containers.get(anchor.key);
    if (!container) return null;
    const map = textMap(container);
    let start = anchor.start;
    if (map.text.slice(start, anchor.end) !== anchor.quote) {
      const matches = [];
      let at = -1;
      while ((at = map.text.indexOf(anchor.quote, at + 1)) !== -1) {
        const score = (anchor.prefix && map.text.slice(Math.max(0, at - anchor.prefix.length), at) === anchor.prefix ? 1 : 0)
          + (anchor.suffix && map.text.slice(at + anchor.quote.length, at + anchor.quote.length + anchor.suffix.length) === anchor.suffix ? 1 : 0);
        matches.push({at,score});
      }
      matches.sort((a,b) => b.score - a.score);
      if (!matches.length || (matches.length > 1 && matches[0].score <= matches[1].score)) return null;
      start = matches[0].at;
    }
    return {...map, container, start, end:start + anchor.quote.length};
  }
  function selectionAnchor() {
    const selection = window.getSelection();
    if (!selection || selection.isCollapsed || !selection.rangeCount) return null;
    const range = selection.getRangeAt(0), anchors = [];
    for (const [key, container] of containers) {
      if (!range.intersectsNode(container.node) || !container.node.getClientRects().length) continue;
      const {text, nodes} = textMap(container);
      const spans = [];
      for (const {node,start} of nodes) {
        if (!node.parentElement.getClientRects().length || !range.intersectsNode(node)) continue;
        let a = node === range.startContainer ? range.startOffset : 0;
        let b = node === range.endContainer ? range.endOffset : node.length;
        if (a >= b) continue;
        const left = start + a, right = start + b;
        const previous = spans[spans.length - 1];
        if (previous && !text.slice(previous.end,left).trim()) previous.end = right;
        else spans.push({start:left,end:right});
      }
      for (const span of spans) {
        const exact = text.slice(span.start,span.end);
        if (exact.trim()) anchors.push({key,...span,quote:exact,prefix:text.slice(Math.max(0,span.start-40),span.start),suffix:text.slice(span.end,span.end+40)});
      }
    }
    if (!anchors.length) return null;
    const sides = new Set(anchors.map(a => containers.get(a.key).side));
    if (sides.size !== 1) return null;
    // Keep anchor order in the document, including selections spanning paragraphs.
    return {anchors, quote:anchors.map(a => a.quote).join('\n'), side:[...sides][0], rect:range.getBoundingClientRect()};
  }
  function showRail(open) {
    rail.hidden = !open;
    layout.classList.toggle('comments-open',open);
    toggle.setAttribute('aria-expanded',String(open));
  }
  function message(text, error=false) { status.textContent=text; status.classList.toggle('error',error); }
  function persist() {
    try { localStorage.setItem(storageKey,JSON.stringify({version:1,documentId:docId,comments})); saved=true; message('Saved in this browser · Export to keep a copy.'); }
    catch (_) { saved=false; message('Browser storage is unavailable. Export comments to keep them.',true); }
  }
  function validComment(item) {
    return item && typeof item.id === 'string' && /^[a-zA-Z0-9_-]{1,100}$/.test(item.id)
      && typeof item.text === 'string' && item.text.trim().length > 0
      && typeof item.createdAt === 'string' && Array.isArray(item.anchors) && item.anchors.length > 0
      && item.anchors.every(a => a && typeof a.key === 'string' && typeof a.quote === 'string' && a.quote.length > 0
        && Number.isInteger(a.start) && a.start >= 0 && Number.isInteger(a.end) && a.end > a.start
        && typeof a.prefix === 'string' && typeof a.suffix === 'string');
  }
  function unwrapMarks() {
    document.querySelectorAll('.annotation-mark').forEach(mark => { const parent=mark.parentNode; mark.replaceWith(...mark.childNodes); parent.normalize(); });
  }
  function paint() {
    unwrapMarks();
    const work = new Map();
    for (const comment of comments) {
      for (const anchor of comment.anchors) {
        const match = resolve(anchor);
        if (!match) continue;
        for (const {node,start} of match.nodes) {
          const a=Math.max(0,match.start-start), b=Math.min(node.length,match.end-start);
          if (a>=b) continue;
          if (!work.has(node)) work.set(node,[]);
          work.get(node).push({a,b,id:comment.id});
        }
      }
    }
    for (const [node,spans] of work) {
      const points=[...new Set([0,node.length,...spans.flatMap(s=>[s.a,s.b])])].sort((a,b)=>a-b);
      const fragment=document.createDocumentFragment();
      for(let i=0;i<points.length-1;i++) {
        const a=points[i],b=points[i+1], ids=[...new Set(spans.filter(s=>s.a<b && s.b>a).map(s=>s.id))];
        if (!ids.length) {fragment.append(document.createTextNode(node.data.slice(a,b)));continue;}
        const mark=document.createElement('span');mark.className='annotation-mark';mark.dataset.commentIds=ids.join(' ');
        mark.textContent=node.data.slice(a,b);mark.tabIndex=0;mark.setAttribute('role','button');
        mark.setAttribute('aria-label',`Open ${ids.length>1 ? ids.length+' comments' : 'comment'} on ${mark.textContent.slice(0,80)}`);
        if(ids.includes(activeId))mark.classList.add('active');fragment.append(mark);
      }
      node.replaceWith(fragment);
    }
  }
  function make(tag,cls,text) {const node=document.createElement(tag);if(cls)node.className=cls;if(text!==undefined)node.textContent=text;return node;}
  function button(label,action,cls='') {const b=make('button',cls,label);b.type='button';b.addEventListener('click',action);return b;}
  function updateActive() {
    document.querySelectorAll('.comment-card').forEach(card=>card.classList.toggle('active',card.dataset.commentId===activeId));
    document.querySelectorAll('.annotation-mark').forEach(mark=>mark.classList.toggle('active',mark.dataset.commentIds.split(' ').includes(activeId)));
  }
  function navigate(comment) {
    activeId=comment.id;showRail(true);updateActive();
    const first=comment.anchors.map(resolve).find(Boolean);
    if(!first){message('This passage changed. The original quote is preserved in the comment.',true);return;}
    const {container}=first;
    if(narrow.matches)showRail(false);
    if(container.side==='original') {
      original.open=true;original.classList.toggle('show-source-text',container.mode==='raw');
      sourceView.setAttribute('aria-pressed',String(container.mode==='raw'));sourceView.textContent=container.mode==='raw'?'Formatted':'Source text';
    }
    let ancestor=container.node;
    while(ancestor && ancestor!==document.body){if(ancestor.tagName==='DETAILS')ancestor.open=true;ancestor=ancestor.parentElement;}
    container.node.querySelectorAll('details').forEach(node=>node.open=true);
    requestAnimationFrame(()=>{
      const marks=[...container.node.querySelectorAll('.annotation-mark')].filter(node=>node.dataset.commentIds.split(' ').includes(comment.id));
      const target=marks[0] || container.node;
      if(container.side==='original') {
        quietScroll(sourcePane,sourcePane.scrollTop+target.getBoundingClientRect().top-sourcePane.getBoundingClientRect().top-32);
        if(narrow.matches)original.scrollIntoView({block:'start'});
      } else if(narrow.matches)target.scrollIntoView({block:'center'});
      else quietScroll(summaryPane,summaryPane.scrollTop+target.getBoundingClientRect().top-summaryPane.getBoundingClientRect().top-32);
      target.focus?.({preventScroll:true});
    });
  }
  function renderCards() {
    cards.replaceChildren();
    document.querySelector('#comments-count').textContent=comments.length || '';
    document.querySelector('#comment-heading-count').textContent=comments.length ? ` · ${comments.length}` : '';
    if(!comments.length)cards.append(make('p','comment-empty','Select text in either document and start typing. Your notes will appear here.'));
    comments.forEach(comment=>{
      const card=make('article','comment-card');card.dataset.commentId=comment.id;
      const c=containers.get(comment.anchors[0].key);
      card.append(make('p','comment-meta',c ? (c.side==='original' ? 'Original'+(c.mode==='raw'?' · Source text':'') : 'Reading edition') : 'Saved passage'));
      const excerpt=comment.anchors.map(a=>a.quote).join('\n');
      const jump=button(excerpt,()=>navigate(comment),'comment-quote');jump.setAttribute('aria-label','Go to highlighted passage: '+excerpt.slice(0,120));card.append(jump);
      card.append(make('p','comment-copy',comment.text));
      if(comment.anchors.some(a=>!resolve(a)))card.append(make('p','comment-orphan','Passage changed · quote retained'));
      const actions=make('div','comment-actions');
      actions.append(button('Edit',()=>begin({anchors:comment.anchors,quote:excerpt},comment)),button('Delete',()=>{
        comments=comments.filter(item=>item.id!==comment.id);if(activeId===comment.id)activeId=null;
        if(draft?.id===comment.id)cancel();persist();paint();renderCards();
      }));card.append(actions);cards.append(card);
    });updateActive();
  }
  function begin(selection,existing=null) {
    if(!selection?.anchors?.length)return;
    draft={anchors:selection.anchors,id:existing?.id || null};
    document.querySelector('#comment-editor-title').textContent=existing?'Edit comment':'New comment';
    quote.textContent=selection.quote;input.value=existing?.text || '';editor.hidden=false;selectionButton.hidden=true;
    showRail(true);window.getSelection()?.removeAllRanges();
    rail.querySelector('.comment-body').scrollTop=0;input.focus();
  }
  function cancel() {draft=null;if(document.activeElement===input)input.blur();editor.hidden=true;input.value='';pending=null;selectionButton.hidden=true;}
  editor.addEventListener('submit',event=>{
    event.preventDefault();const text=input.value.trim();if(!draft || !text){input.focus();return;}
    const existing=comments.find(c=>c.id===draft.id);
    if(existing){existing.text=text;existing.updatedAt=new Date().toISOString();activeId=existing.id;}
    else {const id=globalThis.crypto?.randomUUID?.() || `note-${Date.now()}-${Math.random().toString(36).slice(2)}`;
      comments.push({id,text,anchors:draft.anchors,createdAt:new Date().toISOString()});activeId=id;}
    cancel();persist();paint();renderCards();
    cards.querySelector(`[data-comment-id="${activeId}"]`)?.scrollIntoView({block:'nearest'});
  });
  document.querySelector('#comment-cancel').addEventListener('click',cancel);
  document.querySelector('#comment-close').addEventListener('click',()=>showRail(false));
  toggle.hidden=false;toggle.addEventListener('click',()=>showRail(rail.hidden));
  selectionButton.addEventListener('pointerdown',event=>event.preventDefault());
  selectionButton.addEventListener('click',()=>begin(pending));
  let selectionTimer;
  function refreshSelection() {
    if(draft)return;
    pending=selectionAnchor();selectionButton.hidden=!pending;
    if(!pending)return;
    const rect=pending.rect;
    selectionButton.style.left=Math.max(8,Math.min(innerWidth-150,rect.left+rect.width/2-65))+'px';
    selectionButton.style.top=Math.max(8,Math.min(innerHeight-50,rect.top>50?rect.top-44:rect.bottom+8))+'px';
  }
  document.addEventListener('selectionchange',()=>{clearTimeout(selectionTimer);selectionTimer=setTimeout(refreshSelection,80);});
  document.addEventListener('pointerup',()=>setTimeout(refreshSelection,0));
  document.addEventListener('keydown',event=>{
    // Enter confirms an IME candidate while composition is active; it must not save.
    if(event.defaultPrevented || event.isComposing || event.keyCode===229)return;
    if(event.target===input) {
      if(event.key==='Enter'&&!event.shiftKey) {
        event.preventDefault();editor.requestSubmit();
      }
      return;
    }
    const editable=event.target.closest('input,textarea,select,[role="textbox"]') || event.target.isContentEditable;
    if(editable)return;
    if((event.metaKey||event.ctrlKey)&&event.shiftKey&&event.key.toLowerCase()==='m') {
      const selection=selectionAnchor();if(selection){event.preventDefault();begin(selection);}
      return;
    }
    if(event.key==='Escape') {selectionButton.hidden=true;pending=null;return;}
    // Resolve the live selection, not the debounced popup, so fast typing keeps its first character.
    if(!draft && !event.metaKey && !event.ctrlKey && !event.altKey && Array.from(event.key).length===1) {
      const selection=selectionAnchor();
      if(selection) {
        event.preventDefault();event.stopImmediatePropagation();begin(selection);
        input.value=event.key;input.setSelectionRange(input.value.length,input.value.length);
      }
    }
  });
  function activateMark(mark) {
    const ids=mark.dataset.commentIds.split(' ');activeId=ids.includes(activeId)?ids[(ids.indexOf(activeId)+1)%ids.length]:ids[0];
    showRail(true);updateActive();cards.querySelector(`[data-comment-id="${activeId}"]`)?.scrollIntoView({block:'nearest'});
  }
  document.addEventListener('click',event=>{
    const mark=event.target.closest('.annotation-mark');
    if(!mark || !window.getSelection()?.isCollapsed)return;
    event.preventDefault();event.stopImmediatePropagation();activateMark(mark);
  },true);
  document.addEventListener('keydown',event=>{
    const mark=event.target.closest('.annotation-mark');
    if(mark&&(event.key==='Enter'||event.key===' ')){event.preventDefault();activateMark(mark);}
  });
  document.querySelector('#comments-export').addEventListener('click',()=>{
    const blob=new Blob([JSON.stringify({version:1,documentId:docId,title:document.title,comments},null,2)],{type:'application/json'});
    const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='defuse-comments.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  });
  const importInput=document.querySelector('#comments-import-file');
  document.querySelector('#comments-import').addEventListener('click',()=>importInput.click());
  importInput.addEventListener('change',async()=>{
    try{
      const file=importInput.files[0];if(!file)return;if(file.size>5*1024*1024)throw Error('Comment file is too large.');
      const data=JSON.parse(await file.text());
      if(data.version!==1||data.documentId!==docId||!Array.isArray(data.comments)||!data.comments.every(validComment))throw Error('Choose a comment export for this document.');
      const merged=new Map(comments.map(c=>[c.id,c]));
      for(const item of data.comments){const current=merged.get(item.id);if(!current || String(item.updatedAt||item.createdAt)>String(current.updatedAt||current.createdAt))merged.set(item.id,item);}
      comments=[...merged.values()];persist();paint();renderCards();showRail(true);
    }catch(error){message(error.message || 'Could not import comments.',true);}finally{importInput.value='';}
  });
  try {
    const stored=localStorage.getItem(storageKey);
    if(stored){const data=JSON.parse(stored);if(data.version!==1||data.documentId!==docId||!Array.isArray(data.comments)||!data.comments.every(validComment))throw Error('Invalid saved comments');comments=data.comments;saved=true;}
    message(saved?'Saved in this browser · Export to keep a copy.':'Comments stay in this browser. Export to keep a copy.');
  }catch(_){message('Saved comments could not be loaded. New notes can be exported.',true);}
  paint();renderCards();showRail(innerWidth>1200);
})();
