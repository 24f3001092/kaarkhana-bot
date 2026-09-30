
/* KaarkhanaBot — AI Work Agent frontend
   Real execution happens server-side through POST /api/tasks.
   Sarvam API keys never enter this browser code. */
const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
const STORAGE={history:"kb_history_v2",artifacts:"kb_artifacts_v2",usage:"kb_usage_v2",memory:"kb_memory_v2",conversation:"kb_conversation_v2"};
const TOOLS=[
 ["📄","Document reader","PDF, DOCX, TXT and document understanding","Document"],
 ["🌐","Web research","Multi-source research and citations","Research"],
 ["📊","Data analyzer","CSV/XLSX inspection, statistics and charts","Data"],
 ["</>","Code executor","Debugging, review and tests in a sandbox","Coding"],
 ["🧮","Calculator","Reliable arithmetic and transformations","Utility"],
 ["🖼","Image analyzer","Screenshots and visual inputs","Vision"],
 ["🗂","Artifact generator","PDF and document outputs","Output"],
 ["🗃","Database query","Structured application data operations","Data"]
];
let files=[],running=false,currentView="workspace";
const read=(k,f)=>{try{return JSON.parse(localStorage.getItem(k))??f}catch{return f}};
const write=(k,v)=>localStorage.setItem(k,JSON.stringify(v));
let history=read(STORAGE.history,[]),artifacts=read(STORAGE.artifacts,[]),usage=Number(localStorage.getItem(STORAGE.usage)||0);
let conversationId=localStorage.getItem(STORAGE.conversation)||("conv_"+crypto.randomUUID());
localStorage.setItem(STORAGE.conversation,conversationId);

function toast(msg){const e=$("#toast");e.textContent=msg;e.classList.add("show");clearTimeout(window._toast);window._toast=setTimeout(()=>e.classList.remove("show"),3000)}
function esc(v){return String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]))}
function formatBytes(n){if(n<1024)return n+" B";if(n<1048576)return(n/1024).toFixed(1)+" KB";return(n/1048576).toFixed(1)+" MB"}
function formatTime(ts){return new Date(ts).toLocaleString([],{month:"short",day:"numeric",hour:"2-digit",minute:"2-digit"})}
function updateUsage(){$("#usage-count").textContent=`${usage} / 20`,$("#usage-bar").style.width=Math.min(100,usage/20*100)+"%"}
function renderRecent(){const e=$("#recent-list");e.innerHTML="";history.slice(0,5).forEach(t=>{const b=document.createElement("button");b.className="recent-item";b.textContent=t.prompt;b.title=t.prompt;b.onclick=()=>{switchView("workspace");renderTask(t)};e.appendChild(b)});if(!history.length)e.innerHTML='<div class="recent-item" style="color:#9aa4af">No tasks yet</div>'}
function switchView(view){currentView=view;$$(".view").forEach(v=>v.classList.remove("active-view"));$(`#${view}-view`).classList.add("active-view");$$(".nav-item").forEach(n=>n.classList.toggle("active",n.dataset.view===view));$("#breadcrumbs").textContent=view[0].toUpperCase()+view.slice(1);if(view==="history")renderHistory();if(view==="artifacts")renderArtifacts();$("#sidebar").classList.remove("open")}
function renderTools(){$("#tool-grid").innerHTML=TOOLS.map(t=>`<div class="tool-card"><div class="tool-icon">${t[0]}</div><h3>${t[1]}</h3><p>${t[2]}</p><span class="tool-tag">${t[3]}</span></div>`).join("");$("#modal-tools").innerHTML=TOOLS.map(t=>`<div class="modal-tool">${t[0]} <b>${t[1]}</b> <span style="color:#8994a2">— ${t[2]}</span></div>`).join("")}
function attach(list){list.forEach(f=>{if(files.some(x=>x.name===f.name&&x.size===f.size))return;if(f.size>20*1024*1024){toast(`${f.name} is larger than 20 MB.`);return}files.push(f)});renderAttachments()}
function renderAttachments(){$("#attachment-list").innerHTML=files.map((f,i)=>`<div class="attachment">📎 ${esc(f.name)} <span>${formatBytes(f.size)}</span><button onclick="removeFile(${i})">×</button></div>`).join("")}
function removeFile(i){files.splice(i,1);renderAttachments()}
function planHTML(plan){return `<ol>${(plan||[]).map(s=>`<li><b>${esc(s.action||s)}</b>${s.tool?` <span class="plan-tool">${esc(s.tool)}</span>`:""}</li>`).join("")}</ol>`}
function analysisHTML(a){if(!a)return"";const chips=(a.recommended_tools||[]).map(x=>`<span class="analysis-chip">${esc(x)}</span>`).join("");return `<div class="analysis-panel"><div class="analysis-title">Task understanding</div><div class="analysis-grid">
<div><span>Goal</span><b>${esc(a.user_goal)}</b></div><div><span>Intent</span><b>${esc(a.intent)}</b></div><div><span>Language</span><b>${esc(a.language)}</b></div><div><span>Complexity</span><b>${esc(a.complexity)}</b></div>
<div class="wide"><span>Expected output</span><b>${esc(a.expected_output||"—")}</b></div><div class="wide"><span>Recommended tools</span><div>${chips||"—"}</div></div>
${a.missing_inputs?.length?`<div class="wide"><span>Missing inputs</span><b>${a.missing_inputs.map(esc).join(", ")}</b></div>`:""}</div></div>`}
function answerHTML(answer){if(!answer)return"";let body=esc(answer.body||"").replace(/\n\n/g,"</p><p>").replace(/\n/g,"<br>");return `<div class="result"><strong>${esc(answer.title||"Result")}</strong><div class="answer-body"><p>${body}</p></div>`}
function renderTask(task){switchView("workspace");const area=$("#task-area"),done=task.status==="complete",need=task.status==="needs_clarification",failed=task.status==="failed";area.innerHTML=`<div class="task-card">
<div class="task-head"><div><h3>${esc(task.prompt)}</h3><p>${task.files?.length?task.files.length+" input file(s) · ":""}${formatTime(task.createdAt||Date.now())}</p></div><span class="task-badge ${failed?"failed":need?"review":""}">${done?"VERIFIED":need?"CLARIFICATION":failed?"FAILED":"RUNNING"}</span></div>
<div class="activity"><div class="activity-title">Agent activity</div>${(task.activity||[]).map(x=>`<div class="activity-row"><i>✓</i> ${esc(x)}</div>`).join("")}</div>
${task.analysis?analysisHTML(task.analysis):""}
${task.plan?.length?`<div class="plan"><h4>Execution plan</h4>${planHTML(task.plan)}</div>`:""}
${need?`<div class="clarification"><b>${esc(task.answer?.title||"One detail needed")}</b><p>${esc(task.answer?.body||"Please provide the missing information.")}</p></div>`:""}
${failed?`<div class="error-box"><b>Task could not be completed</b><p>${esc(task.error||"The server reported an error.")}</p><p>Check the backend configuration and try again.</p></div>`:""}
${done?answerHTML(task.answer):""}
${task.artifact?`<div class="artifact-actions"><a class="download-btn" href="${esc(task.artifact.url)}" download>Download PDF</a><button class="secondary-btn" onclick="copyResult('${esc(task.id)}')">Copy summary</button></div>`:""}
</div>`;area.scrollIntoView({behavior:"smooth",block:"start"})}
async function runTask(){if(running)return;const prompt=$("#prompt").value.trim();if(!prompt&&!files.length){toast("Describe a task or attach a file first.");return}if(usage>=20){toast("Daily local usage limit reached.");return}
running=true;$("#send-btn").disabled=true;usage++;localStorage.setItem(STORAGE.usage,usage);updateUsage();
const started=Date.now(),task={id:"task_"+Date.now(),prompt:prompt||"Analyze attached files",files:files.map(f=>({name:f.name,size:f.size,type:f.type})),status:"running",createdAt:started,activity:["Received the request and inputs","Sending the task to the backend input analyzer"]};
history.unshift(task);history=history.slice(0,30);write(STORAGE.history,history);renderRecent();renderTask(task);
try{
 const fd=new FormData();fd.append("prompt",prompt);fd.append("conversation_id",conversationId);files.forEach(f=>fd.append("files",f,f.name));
 const r=await fetch("/api/tasks",{method:"POST",body:fd});const data=await r.json();
 if(!r.ok)throw new Error(data.detail||data.error||`HTTP ${r.status}`);
 Object.assign(task,data,{createdAt:started,prompt:prompt||"Analyze attached files",files:task.files});task.status=data.status;write(STORAGE.history,history);renderRecent();renderTask(task);
 if(data.status==="complete")toast("Task completed and verified.");else if(data.status==="needs_clarification")toast("One detail is needed before I continue.");else toast("Task failed safely — no result was fabricated.");
 if(data.status==="complete"||data.status==="needs_clarification")$("#prompt").value="";
 files=[];renderAttachments();
}catch(e){task.status="failed";task.error=e.message||"Backend request failed.";task.activity=["Received the request","Could not reach the AI backend"];write(STORAGE.history,history);renderTask(task);toast("Backend connection failed.");}
finally{running=false;$("#send-btn").disabled=false}}
function copyResult(id){const t=history.find(x=>x.id===id);if(!t?.answer)return;navigator.clipboard?.writeText(t.answer.body||"");toast("Result copied.")}
function renderHistory(){const e=$("#history-list");if(!history.length){e.innerHTML='<div class="empty">No tasks yet. Start from Workspace.</div>';return}e.innerHTML=history.map(t=>`<div class="history-row"><div class="history-main"><b>${esc(t.prompt)}</b><small>${formatTime(t.createdAt)} · ${t.status==="complete"?"Verified":t.status==="failed"?"Failed":"Needs input"}</small></div><span class="task-badge">${t.status==="complete"?"VERIFIED":t.status==="failed"?"FAILED":"REVIEW"}</span><button class="secondary-btn" onclick="renderTask(history.find(x=>x.id==='${esc(t.id)}'))">Open</button></div>`).join("")}
function renderArtifacts(){const e=$("#artifact-list");if(!artifacts.length){e.innerHTML='<div class="empty" style="grid-column:1/-1">Generated artifacts will appear here.</div>';return}e.innerHTML=artifacts.map(a=>`<div class="artifact-card"><h3>▣ ${esc(a.name)}</h3><p>Verified output generated by KaarkhanaBot.</p><div class="artifact-meta">${formatTime(a.createdAt)} · ${esc(a.type||"PDF")}</div>${a.url?`<a class="secondary-btn" href="${esc(a.url)}" download>Download</a>`:""}</div>`).join("")}
async function refreshHealth(){try{const r=await fetch("/api/health");const d=await r.json();const s=$(".status");s.innerHTML=`<i></i> ${d.sarvam_configured?"Sarvam AI connected":"Backend · key not configured"}`;s.title=`Model: ${d.model||"unknown"}`}catch{$(".status").innerHTML="<i></i> Backend offline"}}
$("#file-input").addEventListener("change",e=>{attach([...e.target.files]);e.target.value=""});
$("#send-btn").addEventListener("click",runTask);$("#prompt").addEventListener("keydown",e=>{if((e.ctrlKey||e.metaKey)&&e.key==="Enter")runTask()});
$$(".suggestion").forEach(b=>b.addEventListener("click",()=>{$("#prompt").value=b.dataset.prompt;$("#prompt").focus()}));
$$(".nav-item").forEach(b=>b.addEventListener("click",()=>switchView(b.dataset.view)));
$("#new-chat").onclick=()=>{$("#prompt").value="";files=[];conversationId="conv_"+crypto.randomUUID();localStorage.setItem(STORAGE.conversation,conversationId);renderAttachments();$("#task-area").innerHTML="";switchView("workspace");$("#prompt").focus()};
$("#menu-btn").onclick=()=>$("#sidebar").classList.toggle("open");$("#tools-btn").onclick=()=>$("#tools-modal").classList.remove("hidden");$("#voice-btn").onclick=()=>toast("Voice input can be connected to Sarvam speech-to-text next.");
$$("[data-close]").forEach(b=>b.onclick=()=>$("#tools-modal").classList.add("hidden"));$("#tools-modal").addEventListener("click",e=>{if(e.target.id==="tools-modal")e.currentTarget.classList.add("hidden")});
$("#clear-history").onclick=()=>{history=[];write(STORAGE.history,history);renderRecent();renderHistory();toast("Browser task history cleared.")};
$("#reset-data").onclick=()=>{if(confirm("Reset local browser history, artifacts and usage?")){Object.values(STORAGE).forEach(k=>localStorage.removeItem(k));history=[];artifacts=[];usage=0;conversationId="conv_"+crypto.randomUUID();localStorage.setItem(STORAGE.conversation,conversationId);renderRecent();updateUsage();renderHistory();renderArtifacts();toast("Local data reset.")}};
$("#memory-toggle").onchange=e=>localStorage.setItem(STORAGE.memory,e.target.checked?"1":"0");$("#lang-select").onchange=e=>toast(`Language preference: ${e.target.value}. Sarvam will receive the detected/requested language context.`);$("#language-btn").onclick=()=>switchView("settings");
// Drag and drop
const composer=$("#composer");["dragenter","dragover"].forEach(ev=>composer.addEventListener(ev,e=>{e.preventDefault();composer.classList.add("dragging")}));["dragleave","drop"].forEach(ev=>composer.addEventListener(ev,e=>{e.preventDefault();composer.classList.remove("dragging")}));composer.addEventListener("drop",e=>attach([...e.dataTransfer.files]));
renderTools();renderRecent();renderHistory();renderArtifacts();updateUsage();refreshHealth();
