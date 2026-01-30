#!/bin/bash    
  
VNT_config="/var/packages/VNT/var/config.yaml"
VNT_bin="/var/packages/VNT/target/bin/vnt-cli"
VNT_log="/var/packages/VNT/var/VNT.log"

if [[ "${REQUEST_URI}" =~ config\.html$ ]]; then
    echo "Content-Type: text/html; charset=UTF-8"
    echo ""
    if [[ -f "config.html" ]]; then
        cat "config.html"
    else    
        echo "<html><body><h1>配置文件生成页面不存在</h1></body></html>"
    fi
    exit 0
fi
  
LOG_TEXT=""    
if [[ -f "/var/packages/VNT/var/VNT.log" ]]; then    
    LOG_TEXT=$(cat "/var/packages/VNT/var/VNT.log" | sed 's/</\&lt;/g;s/>/\&gt;/g')    
fi 

read -n $CONTENT_LENGTH POST_DATA 2>/dev/null    
  
url_decode() { echo -e "$(sed 's/+/ /g;s/%/\\x/g' <<<"$1")"; }    
  
ACTION=""    
CONFIG_CONTENT=""    
  
if [[ -n "$POST_DATA" ]]; then    
    ACTION=$(echo "$POST_DATA" | sed -n 's/.*action=\([^&]*\).*/\1/p')    
    ACTION=$(url_decode "$ACTION")    
    CONFIG_CONTENT=$(echo "$POST_DATA" | sed -n 's/.*config=\(.*\)/\1/p')    
    CONFIG_CONTENT=$(url_decode "$CONFIG_CONTENT")    
fi    
  
# API 端点处理  
if [[ "$ACTION" == "api_status" ]]; then      
    RUNNING="false"      
    PID=""  
    UPTIME=""  
      
    if pidof "vnt-cli" >/dev/null 2>&1; then  
        RUNNING="true"  
        PID=$(pidof "vnt-cli" | head -n 1)  
          
        # 从文件读取启动时间  
        if [[ -f "/var/packages/VNT/var/vntcli_time" ]]; then  
            start_time=$(cat /var/packages/VNT/var/vntcli_time)  
            if [[ -n "$start_time" ]]; then  
                time=$(( $(date +%s) - start_time ))  
                day=$((time / 86400))  
                [[ "$day" = "0" ]] && day='' || day=" $day天"  
                time=$(date -u -d @${time} +%H小时%M分%S秒)  
                UPTIME="${day}${time}"  
            fi  
        fi  
    fi  
      
    echo "Status: 200 OK"      
    echo "Content-Type: application/json"      
    echo ""      
    echo "{\"running\": $RUNNING, \"pid\": \"$PID\", \"uptime\": \"$UPTIME\"}"      
    exit 0      
fi
  
if [[ "$ACTION" == "api_info" ]]; then    
    if pidof "vnt-cli" >/dev/null 2>&1; then  
        INFO_TEXT="$($VNT_bin --info 2>&1)"      
    else  
        INFO_TEXT="vnt-cli未运行，请运行后再试"  
    fi    
    echo "Content-Type: text/plain; charset=UTF-8"  
    echo ""
    echo "$INFO_TEXT"
    exit 0 
fi    
  
if [[ "$ACTION" == "api_all" ]]; then    
    if pidof "vnt-cli" >/dev/null 2>&1; then  
        ALL_TEXT="$($VNT_bin --all 2>&1)"      
    else  
        ALL_TEXT="vnt-cli未运行，请运行后再试"  
    fi    
    echo "Content-Type: text/plain; charset=UTF-8"  
    echo ""
    echo "$ALL_TEXT"
    exit 0 
fi    
  
if [[ "$ACTION" == "api_list" ]]; then    
    if pidof "vnt-cli" >/dev/null 2>&1; then  
        LIST_TEXT="$($VNT_bin --list 2>&1)"      
    else  
        LIST_TEXT="vnt-cli未运行，请运行后再试"  
    fi     
    echo "Content-Type: text/plain; charset=UTF-8"   
    echo ""
    echo "$LIST_TEXT"
    exit 0 
fi    
  
if [[ "$ACTION" == "api_route" ]]; then      
    if pidof "vnt-cli" >/dev/null 2>&1; then  
        ROUTE_TEXT="$($VNT_bin --route 2>&1)"      
    else  
        ROUTE_TEXT="vnt-cli未运行，请运行后再试"  
    fi  
    echo "Content-Type: text/plain; charset=UTF-8"   
    echo ""  
    echo "$ROUTE_TEXT"  
    exit 0   
fi
  
if [[ "$ACTION" == "api_log" ]] || [[ "$ACTION" == "api_raw_log" ]]; then    
    LOG_TEXT=""    
    if [[ -f "/var/packages/VNT/var/VNT.log" ]]; then    
        LOG_TEXT=$(cat "/var/packages/VNT/var/VNT.log")    
    fi    
    echo "Content-Type: text/plain; charset=UTF-8"   
    echo ""
    echo "$LOG_TEXT"
    exit 0 
fi

if [[ "$ACTION" == "clear_log" ]]; then    
    if echo "" > "/var/packages/VNT/var/VNT.log" 2>/dev/null; then    
        echo "Status: 200 OK"    
        echo "Content-Type: application/json"    
        echo ""    
        echo '{"success": true, "message": "日志清空成功"}'
        exit 0 
    else    
        echo "Status: 500 Internal Server Error"    
        echo "Content-Type: application/json"    
        echo ""    
        echo '{"success": false, "message": "日志清空失败"}'
        exit 0 
    fi    
fi

echo "Content-Type: text/html; charset=UTF-8"    
echo ""
  
if [[ "$ACTION" == "save_config" ]]; then    
    OLD_CONFIG=$(cat "$VNT_config" 2>/dev/null)    
    echo "$CONFIG_CONTENT" > "$VNT_config"    
    NEW_CONFIG=$(cat "$VNT_config" 2>/dev/null)    
        
    if [[ "$OLD_CONFIG" != "$NEW_CONFIG" ]]; then
    	echo "restart" > /var/packages/VNT/var/start-stop
    fi    
fi    
  
if [[ "$ACTION" == "start" ]]; then
    echo "start" > /var/packages/VNT/var/start-stop   
fi    
  
if [[ "$ACTION" == "stop" ]]; then 
    echo "stop" > /var/packages/VNT/var/start-stop  
fi     
  
RUNNING="false"    
pgrep -f "$VNT_bin" >/dev/null 2>&1 && RUNNING="true"    
  
CONFIG_TEXT=""    
if [[ -s "$VNT_config" ]]; then    
    CONFIG_TEXT=$(cat "$VNT_config")    
fi    
  
INFO_TEXT="正在获取中..."    
ALL_TEXT="正在获取中..."    
LIST_TEXT="正在获取中..."    
ROUTE_TEXT="正在获取中..."    
  
cat <<EOF    
<!DOCTYPE html>    
<html lang="zh">    
<head>    
<meta charset="UTF-8">
<link rel="icon" type="image/png"
        href="data:image/png;base64,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" />   
<title>VNT 配置管理</title>    
<meta name="viewport" content="width=device-width, initial-scale=1">    
<style>    
body {    
    margin:0;    
    font-family: -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto;    
    background: linear-gradient(135deg,#667eea,#764ba2);    
    transition: background 0.5s;    
}    
.dark body {    
    background: linear-gradient(135deg,#1f1c2c,#928dab);    
}    
.container {    
    max-width: 900px;    
    margin: auto;    
    padding: 20px;    
}    
.card {    
    background: rgba(255,255,255,0.95);    
    border-radius: 16px;    
    padding: 20px;    
    margin-bottom: 20px;    
    box-shadow: 0 20px 40px rgba(0,0,0,0.2);    
    animation: fadeIn 0.6s ease;    
}    
.dark .card {    
    background: rgba(30,30,30,0.95);    
    color: #eee;    
}    
h1,h2 {    
    margin-top: 0;    
}    
button {    
    padding: 10px 16px;    
    border: none;    
    border-radius: 10px;    
    cursor: pointer;    
    background: linear-gradient(135deg,#43cea2,#185a9d);    
    color: white;    
    font-size: 14px;    
    margin-right: 10px;    
    transition: transform 0.2s,opacity 0.2s;    
}    
button:hover {    
    transform: scale(1.05);    
    opacity: 0.9;    
}    
textarea {    
    width: 100%;    
    min-height: 300px;    
    border-radius: 12px;    
    border: 1px solid #ccc;    
    padding: 12px;    
    font-family: monospace;    
    font-size: 14px;    
    box-sizing: border-box;    
}    
.dark textarea {    
    background: #222;    
    color: #eee;    
    border-color: #444;    
}    
.status {    
    font-weight: bold;    
}    
.modal {    
    position: fixed;    
    top:0;left:0;    
    width:100%;height:100%;    
    background: rgba(0,0,0,0.6);    
    display:flex;    
    align-items:center;    
    justify-content:center;    
}    
.modal-content {    
    background:white;    
    max-width:800px;    
    width:90%;    
    border-radius:16px;    
    padding:20px;    
    animation: zoomIn 0.3s;    
}    
.dark .modal-content {    
    background:#1e1e1e;    
    color:#eee;    
}    
pre {    
    white-space: pre;   
    overflow-x: auto;
    word-break: normal;
}    
.toggle {    
    position: fixed;    
    top: 16px;    
    right: 16px;
    z-index: 1000;
}    
.message {    
    position: fixed;    
    top: 20px;    
    right: 20px;    
    padding: 15px 20px;    
    border-radius: 8px;    
    color: white;    
    font-weight: bold;    
    z-index: 1000;    
    animation: fadeInOut 3s ease-in-out;    
}    
.message.success {    
    background: linear-gradient(135deg,#11998e,#38ef7d);    
}    
.message.error {    
    background: linear-gradient(135deg,#eb3349,#f45c43);    
}
.log-pre {  
    background: #f5f5f5;  
    padding: 15px;  
    border-radius: 8px;  
    max-height: 400px;  
    overflow-y: auto;  
}  
.dark .log-pre {  
    background: #2d2d2d;  
    color: #eee;  
}
@keyframes fadeInOut {    
    0% { opacity: 0; transform: translateY(-20px); }    
    20% { opacity: 1; transform: translateY(0); }    
    80% { opacity: 1; transform: translateY(0); }    
    100% { opacity: 0; transform: translateY(-20px); }    
}    
@keyframes fadeIn {    
    from{opacity:0;transform:translateY(20px);}    
    to{opacity:1;transform:none;}    
}    
@keyframes zoomIn {    
    from{transform:scale(0.8);opacity:0;}    
    to{transform:scale(1);opacity:1;}    
}    
@media (max-width:600px) {    
    textarea{min-height:200px;}    
}
/* 平板设备 */  
@media (max-width: 768px) {  
    .toggle {  
        right: 15px;  
        top: 12px;  
    }  
    .toggle button {  
        width: 36px;  
        height: 36px;  
        padding: 6px;  
    }  
}  
  
/* 手机设备 */  
@media (max-width: 480px) {  
    .toggle {  
        right: 10px;  
        top: 10px;  
    }  
    .toggle button {  
        width: 32px;  
        height: 32px;  
        padding: 4px;  
    }  
    .container {  
        padding: 15px;  
    }  
}
</style>    
</head>    
  
<body id="body">    
<div class="toggle">    
<button onclick="toggleTheme()" style="background: linear-gradient(135deg,#43cea2,#185a9d); width: 40px; height: 40px; padding: 8px;">    
    <svg id="sun-icon" width="24" height="24" viewBox="0 0 24 24" fill="white">    
        <circle cx="12" cy="12" r="4" fill="white"/>    
        <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" stroke="white" stroke-width="2" stroke-linecap="round"/>    
    </svg>    
    <svg id="moon-icon" width="24" height="24" viewBox="0 0 24 24" fill="white" style="display: none;">    
        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" fill="white"/>    
    </svg>    
</button>    
</div>    
  
<div class="container">    
<div class="card">    
<h1>VNT 客户端</h1>    
<p class="status">状态：    
<span id="status-indicator" style="color: $(if [ "$RUNNING" = "true" ]; then echo "#38ef7d"; else echo "#f45c43"; fi); font-weight: bold;">    
$(if [ "$RUNNING" = "true" ]; then echo "运行中"; else echo "未运行"; fi)    
</span>    
</p>    
<button id="control-button" onclick="control('$(if [ "$RUNNING" = "true" ]; then echo "stop"; else echo "start"; fi)')" style="background: $(if [ "$RUNNING" = "true" ]; then echo "linear-gradient(135deg,#eb3349,#f45c43)"; else echo "linear-gradient(135deg,#11998e,#38ef7d)"; fi);">    
$(if [ "$RUNNING" = "true" ]; then echo "停止"; else echo "启动"; fi)    
</button>    
<button onclick="showModal('info-modal')" style="background: linear-gradient(135deg,#fa709a,#fee140);">本机信息</button>    
<button onclick="showModal('all-modal')" style="background: linear-gradient(135deg,#f093fb,#f5576c);">所有设备</button>    
<button onclick="showModal('list-modal')" style="background: linear-gradient(135deg,#4facfe,#00f2fe);">设备列表</button>    
<button onclick="showModal('route-modal')" style="background: linear-gradient(135deg,#f6d365,#fda085);">路由信息</button>    
<button onclick="showModal('log-modal')" style="background: linear-gradient(135deg,#43cea2,#185a9d);">运行日志</button>    
</div>    
  
<div class="card">    
<div style="display: flex; justify-content: space-between; align-items: center;">    
    <h2 style="margin: 0;">配置文件</h2>    
    <a href="/webman/3rdparty/VNT/config.html" target="_blank"    
       style="display: inline-block; padding: 10px 16px; border: none; border-radius: 10px;    
              cursor: pointer; background: linear-gradient(135deg,#fa709a,#fee140);    
              color: white; font-size: 14px; text-decoration: none;    
              transition: transform 0.2s, opacity 0.2s;"    
       onmouseover="this.style.transform='scale(1.05)'; this.style.opacity='0.9';"    
       onmouseout="this.style.transform='scale(1)'; this.style.opacity='1';">    
        点此生成配置文件    
    </a>    
</div>    
<form method="post">    
<input type="hidden" name="action" value="save_config">    
<textarea name="config" placeholder="🤣 糟啦,配置文件为空，会无法启动喔，快去生成一个配置文件保存进来吧~">$CONFIG_TEXT</textarea>    
<br><br>    
<button type="submit">保存配置</button>    
</form>    
</div>    
</div>    
  
<div id="info-modal" class="modal" style="display: none;" onclick="if(event.target===this) hideModal('info-modal')">    
<div class="modal-content">    
<div style="display: flex; justify-content: space-between; align-items: center;">  
    <h2 style="margin: 0;">VNT --info</h2>  
    <span id="info-countdown" style="font-size: 14px; color: #999;"> 秒后自动刷新</span>  
</div>   
<pre id="info-content">$INFO_TEXT</pre>    
<br>    
<button onclick="hideModal('info-modal')">关闭</button>    
</div>    
</div>    
  
<div id="all-modal" class="modal" style="display: none;" onclick="if(event.target===this) hideModal('all-modal')">    
<div class="modal-content">    
<div style="display: flex; justify-content: space-between; align-items: center;">  
    <h2 style="margin: 0;">VNT --all</h2>  
    <span id="all-countdown" style="font-size: 14px; color: #999;"> 秒后自动刷新</span>  
</div> 
<pre id="all-content">$ALL_TEXT</pre>    
<br>    
<button onclick="hideModal('all-modal')">关闭</button>    
</div>    
</div>    
  
<div id="list-modal" class="modal" style="display: none;" onclick="if(event.target===this) hideModal('list-modal')">    
<div class="modal-content">    
<div style="display: flex; justify-content: space-between; align-items: center;">  
    <h2 style="margin: 0;">VNT --list</h2>  
    <span id="list-countdown" style="font-size: 14px; color: #999;"> 秒后自动刷新</span>  
</div>   
<pre id="list-content">$LIST_TEXT</pre>    
<br>    
<button onclick="hideModal('list-modal')">关闭</button>    
</div>    
</div>    
  
<div id="route-modal" class="modal" style="display: none;" onclick="if(event.target===this) hideModal('route-modal')">    
<div class="modal-content">    
<div style="display: flex; justify-content: space-between; align-items: center;">  
    <h2 style="margin: 0;">VNT --route</h2>  
    <span id="route-countdown" style="font-size: 14px; color: #999;"> 秒后自动刷新</span>  
</div>  
<pre id="route-content">$ROUTE_TEXT</pre>    
<br>
<button onclick="hideModal('route-modal')">关闭</button>    
</div>    
</div>    
  
<div id="log-modal" class="modal" style="display: none;" onclick="if(event.target===this) hideModal('log-modal')">    
<div class="modal-content">    
<div style="display: flex; justify-content: space-between; align-items: center;">  
    <h2 style="margin: 0;">VNT 运行日志</h2>  
    <span id="log-countdown" style="font-size: 14px; color: #999;"> 秒后自动刷新</span>  
</div>    
<pre id="log-content" class="log-pre">$LOG_TEXT</pre>    
<br>    
<button onclick="confirmClearLog()" style="background: linear-gradient(135deg,#eb3349,#f45c43);">清空日志</button>
<button onclick="downloadLog()" style="background: linear-gradient(135deg,#11998e,#38ef7d);">下载日志</button>      
<button onclick="copyLog()" style="background: linear-gradient(135deg,#667eea,#764ba2);">全部复制</button>
<button onclick="hideModal('log-modal')">关闭</button>    
</div>    
</div>    

<div id="confirm-modal" class="modal" style="display: none;" onclick="if(event.target===this) hideConfirmModal()">
    <div class="modal-content">  
        <h2 id="confirm-title">确认操作</h2>  
        <p id="confirm-message">您确定要执行此操作吗？</p>  
        <p id="confirm-note" style="color: #666; font-size: 14px;">⚠️ 提交后需要2秒才能生效，请勿重复点击，可查看运行日志是否生效</p>  
        <div style="margin-top: 20px;">  
            <button id="confirm-cancel" onclick="hideConfirmModal()" style="background: linear-gradient(135deg,#eb3349,#f45c43);">取消</button>  
            <button id="confirm-ok" onclick="executeControl()" style="background: linear-gradient(135deg,#11998e,#38ef7d);">确认</button>  
        </div>  
    </div>  
</div>

<div id="message" class="message" style="display: none;"></div>    
  
<script>    
// 消息显示函数    
function showMessage(text, type) {    
    const messageEl = document.getElementById('message');    
    messageEl.textContent = text;    
    messageEl.className = 'message ' + type;    
    messageEl.style.display = 'block';    
        
    setTimeout(() => {    
        messageEl.style.display = 'none';    
    }, 3000);    
}    
  
// 主题切换    
function toggleTheme() {    
    const isDark = document.documentElement.classList.toggle('dark');    
    localStorage.setItem('theme', isDark ? 'dark' : 'light');    
        
    const sunIcon = document.getElementById('sun-icon');    
    const moonIcon = document.getElementById('moon-icon');    
        
    if (isDark) {    
        sunIcon.style.display = 'none';    
        moonIcon.style.display = 'block';    
    } else {    
        sunIcon.style.display = 'block';    
        moonIcon.style.display = 'none';    
    }    
}    
  
// 控制函数
let pendingAction = null;
function control(action) {  
    pendingAction = action;  
      
    // 设置确认信息  
    const title = document.getElementById('confirm-title');  
    const message = document.getElementById('confirm-message');  
      
    if (action === 'start') {  
        title.textContent = '确认启动';  
        message.textContent = '您确定要启动 VNT 服务吗？';  
    } else {  
        title.textContent = '确认停止';  
        message.textContent = '您确定要停止 VNT 服务吗？';  
    }  
      
    // 显示确认模态框  
    document.getElementById('confirm-modal').style.display = 'flex';  
    document.body.style.overflow = 'hidden';  
}  
  
function hideConfirmModal() {  
    document.getElementById('confirm-modal').style.display = 'none';  
    document.body.style.overflow = '';  
    pendingAction = null;  
}  
  
function executeControl() {  
    if (!pendingAction) return;  
    
    const action = pendingAction;
    hideConfirmModal();  
     
    const f = document.createElement('form');  
    f.method = 'post';  
    const i = document.createElement('input');  
    i.name = 'action';  
    i.value = action;  
    f.appendChild(i);  
    document.body.appendChild(f);  
    f.submit();  
}   
  
// 模态框控制    
function showModal(modalId) {    
    document.getElementById(modalId).style.display = 'flex';

    // 禁用主页面滚动
    document.body.style.overflow = 'hidden';
      
    // 启动对应的实时更新    
    if (modalId === 'info-modal') {
        updateInfo();
        startInfoUpdate();    
    } else if (modalId === 'all-modal') {
        updateAll();
        startAllUpdate();    
    } else if (modalId === 'list-modal') {
        updateList();
        startListUpdate();    
    } else if (modalId === 'route-modal') {
        updateRoute();
        startRouteUpdate();    
    } else if (modalId === 'log-modal') {
        updateLog();
        startLogUpdate();    
    }    
}    
  
function hideModal(modalId) {    
    document.getElementById(modalId).style.display = 'none';

    // 恢复主页面滚动
    document.body.style.overflow = '';
      
    // 停止对应的实时更新    
    if (modalId === 'info-modal' && updateIntervals.info) {    
        clearInterval(updateIntervals.info);    
    } else if (modalId === 'all-modal' && updateIntervals.all) {    
        clearInterval(updateIntervals.all);    
    } else if (modalId === 'list-modal' && updateIntervals.list) {    
        clearInterval(updateIntervals.list);    
    } else if (modalId === 'route-modal' && updateIntervals.route) {    
        clearInterval(updateIntervals.route);    
    } else if (modalId === 'log-modal' && updateIntervals.log) {    
        clearInterval(updateIntervals.log);    
    }    
}    
  
// 清空日志确认    
async function confirmClearLog() {    
    if (confirm('确定要清空日志吗？此操作不可恢复。')) {    
        try {    
            const response = await fetch('', {    
                method: 'POST',    
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},    
                body: 'action=clear_log'    
            });    
            const result = await response.json();    
            showMessage(result.message, result.success ? 'success' : 'error');    
                
            // 清空成功后刷新日志内容    
            if (result.success) {    
                const logPre = document.querySelector('#log-modal pre');    
                logPre.textContent = '';    
            }    
        } catch (error) {    
            showMessage('操作失败', 'error');    
        }    
    }    
}    
  
// 全局变量存储更新间隔    
let updateIntervals = {};    
  
// 实时更新运行状态    
function startStatusUpdate() {    
    updateStatus();    
    updateIntervals.status = setInterval(updateStatus, 3000);    
}    
  
async function updateStatus() {    
    try {    
        const response = await fetch('', {    
            method: 'POST',    
            headers: {'Content-Type': 'application/x-www-form-urlencoded'},    
            body: 'action=api_status'    
        });    
        const data = await response.json();    
        const statusSpan = document.querySelector('.status span');    
        const statusButton = document.querySelector('button[onclick*="control"]');    
          
        if (data.running) {      
            let statusHtml = '<span style="color: #38ef7d;">运行中</span>';  
            if (data.pid) {  
                statusHtml += ' <span style="color: #999;">PID: <span style="color: #38ef7d;">' + data.pid + '</span></span>';  
            }  
            if (data.uptime) {  
                statusHtml += ' <span style="color: #999;">已运行 <span style="color: #38ef7d;">' + data.uptime + '</span></span>';  
            }  
            statusSpan.innerHTML = statusHtml;  
              
            statusButton.textContent = '停止';      
            statusButton.onclick = () => control('stop');      
            statusButton.style.background = 'linear-gradient(135deg,#eb3349,#f45c43)';      
        } else {      
            statusSpan.innerHTML = '<span style="color: #f45c43;">未运行</span>';  
            statusButton.textContent = '启动';      
            statusButton.onclick = () => control('start');      
            statusButton.style.background = 'linear-gradient(135deg,#11998e,#38ef7d)';      
        }
    } catch (error) {    
        console.error('更新状态失败:', error);    
    }    
}    

let countdownIntervals = {};

// 实时更新本机信息    
function startInfoUpdate() {  
    updateInfo();  
    let countdown = 10;  
    const countdownEl = document.getElementById('info-countdown');  
      
    // 更新倒计时显示  
    const countdownInterval = setInterval(() => {  
        countdown--;  
        if (countdownEl) countdownEl.textContent = countdown + ' 秒后自动刷新';
        if (countdown <= 0) countdown = 10;  
    }, 1000);  
      
    countdownIntervals.info = countdownInterval;  
    updateIntervals.info = setInterval(updateInfo, 10000);  
}
  
async function updateInfo() {      
    try {      
        const response = await fetch('', {      
            method: 'POST',      
            headers: {'Content-Type': 'application/x-www-form-urlencoded'},      
            body: 'action=api_info'      
        });      
        let data = await response.text();  
          
        // 替换英文标签为中文  
        data = data.replace(/Name:/g, '主机名:')  
                  .replace(/Virtual ip:/g, '虚拟IP:')  
                  .replace(/Virtual gateway:/g, '虚拟网关:')  
                  .replace(/Virtual netmask:/g, '虚拟掩码:')  
                  .replace(/Connection status:/g, '连接状态:')
                  .replace(/NAT type:/g, 'NAT类型:')
                  .replace(/Relay server:/g, '中继服务器:')
                  .replace(/Udp listen:/g, 'UDP监听:')
                  .replace(/Tcp listen:/g, 'TCP监听:')
                  .replace(/Public ips:/g, '外网IP:')
                  .replace(/Local addr:/g, '内网IP:')
                  .replace(/IPv6:/g, 'IPv6地址:')
                  .replace(/IP forwarding/g, 'IP转发数量')
                  .replace(/Allows network/g, '子网转发数量')
                  .replace(/Resource temporarily unavailable/g, '资源暂时不可用，请重启插件！')
                  .replace(/None/g, '无');  
          
        // 为连接状态添加颜色  
        data = data.replace(/Connected/g, '<span style="color: green;">已连接</span>')  
                  .replace(/Connecting/g, '<span style="color: red;">连接中</span>');  
          
        const infoPre = document.querySelector('#info-modal pre');      
        if (infoPre) {      
            // 使用 innerHTML 而不是 textContent 以支持 HTML 格式  
            infoPre.innerHTML = data;     
        }      
    } catch (error) {      
        console.error('更新本机信息失败:', error);      
    }      
}    
  
// 实时更新所有设备    
function startAllUpdate() {  
    updateAll();  
    let countdown = 10;  
    const countdownEl = document.getElementById('all-countdown');  
      
    const countdownInterval = setInterval(() => {  
        countdown--;  
        if (countdownEl) countdownEl.textContent = countdown + ' 秒后自动刷新';  
        if (countdown <= 0) countdown = 10;  
    }, 1000);  
      
    countdownIntervals.all = countdownInterval;  
    updateIntervals.all = setInterval(updateAll, 10000);  
}
  
async function updateAll() {    
    try {    
        const response = await fetch('', {    
            method: 'POST',    
            headers: {'Content-Type': 'application/x-www-form-urlencoded'},    
            body: 'action=api_all'    
        });    
        let data = await response.text();
        // 替换英文标签为中文  
        data = data.replace(/Name/g, '主机名')  
                  .replace(/Virtual Ip/g, '虚拟IP')  
                  .replace(/Status/g, '连接状态')  
                  .replace(/P2P/g, '直连')
                  .replace(/Relay/g, '中继')
                  .replace(/Rt/g, '响应时间(ms)')
                  .replace(/NAT Type/g, 'NAT类型')
                  .replace(/Public Ips/g, '外网IP')
                  .replace(/Local Ip/g, '内网IP:')
                  .replace(/IPv6/g, 'IPv6地址')
                  .replace(/No other devices found/g, '没有发现其他客户端设备')
                  .replace(/Resource temporarily unavailable/g, '资源暂时不可用，请重启插件！');

        // 为连接状态添加颜色  
        data = data.replace(/Online/g, '<span style="color: green;">在线</span>')  
                  .replace(/Offline/g, '<span style="color: red;">离线</span>');
        const allPre = document.querySelector('#all-modal pre');    
        if (allPre) {    
            allPre.innerHTML = data;    
        }    
    } catch (error) {    
        console.error('更新所有设备失败:', error);    
    }    
}    
  
// 实时更新设备列表    
function startListUpdate() {  
    updateList();  
    let countdown = 10;  
    const countdownEl = document.getElementById('list-countdown');  
      
    const countdownInterval = setInterval(() => {  
        countdown--;  
        if (countdownEl) countdownEl.textContent = countdown + ' 秒后自动刷新';  
        if (countdown <= 0) countdown = 10;  
    }, 1000);  
      
    countdownIntervals.list = countdownInterval;  
    updateIntervals.list = setInterval(updateList, 10000);  
}  
  
async function updateList() {    
    try {    
        const response = await fetch('', {    
            method: 'POST',    
            headers: {'Content-Type': 'application/x-www-form-urlencoded'},    
            body: 'action=api_list'    
        });    
        let data = await response.text();
        // 替换英文标签为中文  
        data = data.replace(/Name/g, '主机名')
                  .replace(/Virtual Ip/g, '虚拟IP') 
                  .replace(/Status/g, '连接状态')  
                  .replace(/P2P/g, '直连')  
                  .replace(/Relay/g, '中继')
                  .replace(/Resource temporarily unavailable/g, '资源暂时不可用，请重启插件！')
                  .replace(/No other devices found/g, '没有发现其他客户端设备')
                  .replace(/Rt/g, '响应时间(ms)');  
          
        // 为连接状态添加颜色  
        data = data.replace(/Online/g, '<span style="color: green;">在线</span>')  
                  .replace(/Offline/g, '<span style="color: red;">离线</span>')  
                  .replace(/Mismatch/g, '<span style="color: yellow;">密码错误</span>');

        const listPre = document.querySelector('#list-modal pre');    
        if (listPre) {    
            listPre.innerHTML = data;    
        }    
    } catch (error) {    
        console.error('更新设备列表失败:', error);    
    }    
}    
  
// 实时更新路由信息    
function startRouteUpdate() {  
    updateRoute();  
    let countdown = 10;  
    const countdownEl = document.getElementById('route-countdown');  
      
    const countdownInterval = setInterval(() => {  
        countdown--;  
        if (countdownEl) countdownEl.textContent = countdown + ' 秒后自动刷新';  
        if (countdown <= 0) countdown = 10;  
    }, 1000);  
      
    countdownIntervals.route = countdownInterval;  
    updateIntervals.route = setInterval(updateRoute, 10000);  
}
  
async function updateRoute() {    
    try {    
        const response = await fetch('', {    
            method: 'POST',    
            headers: {'Content-Type': 'application/x-www-form-urlencoded'},    
            body: 'action=api_route'    
        });    
        let data = await response.text();
        // 替换英文标签为中文  
        data = data.replace(/Destination/g, '目标地址')  
                  .replace(/Next Hop/g, '下一跳')  
                  .replace(/Metric/g, '跳数') 
                  .replace(/Rt/g, '响应时间(ms)')
                  .replace(/Resource temporarily unavailable/g, '资源暂时不可用，请重启插件！')
                  .replace(/No route found/g, '没有发现路由信息')
                  .replace(/Interface/g, '接口地址');

        const routePre = document.querySelector('#route-modal pre');    
        if (routePre) {    
            routePre.innerHTML = data;    
        }    
    } catch (error) {    
        console.error('更新路由信息失败:', error);    
    }    
}    
  
// 实时更新日志    
function startLogUpdate() {  
    updateLog();  
    let countdown = 10;  // 日志更新间隔是5秒  
    const countdownEl = document.getElementById('log-countdown');  
      
    const countdownInterval = setInterval(() => {  
        countdown--;  
        if (countdownEl) countdownEl.textContent = countdown + ' 秒后自动刷新';  
        if (countdown <= 0) countdown = 10;  
    }, 1000);  
      
    countdownIntervals.log = countdownInterval;  
    updateIntervals.log = setInterval(updateLog, 10000);  
}
  
async function updateLog() {    
    try {    
        const response = await fetch('', {    
            method: 'POST',    
            headers: {'Content-Type': 'application/x-www-form-urlencoded'},    
            body: 'action=api_log'    
        });    
        let data = await response.text();
        // 替换英文标签为中文  
        data = data.replace(/Connect Successfully/g, '连接成功')  
                  .replace(/connect count/g, '重连次数');  
          
        // 为日志等级添加颜色  警告为深橙色
        data = data.replace(/INFO/g, '<span style="color: green;">信息</span>')  
                  .replace(/ERROR/g, '<span style="color: red;">错误</span>')  
                  .replace(/WARN/g, '<span style="color: #ff9800;">警告</span>');

        const logPre = document.querySelector('#log-modal pre');    
        if (logPre) {    
            logPre.innerHTML = data;    
            // 自动滚动到底部    
            logPre.scrollTop = logPre.scrollHeight;    
        }    
    } catch (error) {    
        console.error('更新日志失败:', error);    
    }    
}

// 下载日志  
async function downloadLog() {  
    try {  
        const response = await fetch('', {  
            method: 'POST',  
            headers: {'Content-Type': 'application/x-www-form-urlencoded'},  
            body: 'action=api_raw_log'  
        });  
        const data = await response.text();  
          
        // 创建下载链接  
        const blob = new Blob([data], { type: 'text/plain;charset=utf-8' });  
        const url = window.URL.createObjectURL(blob);  
        const a = document.createElement('a');  
        a.href = url;  
        a.download = 'vnt_log_' + new Date().toISOString().slice(0, 19).replace(/:/g, '-') + '.log';  
        document.body.appendChild(a);  
        a.click();  
        document.body.removeChild(a);  
        window.URL.revokeObjectURL(url);  
          
        showMessage('日志下载成功', 'success');  
    } catch (error) {  
        showMessage('下载失败', 'error');  
        console.error('下载日志失败:', error);  
    }  
}  
  
// 复制日志  
async function copyLog() {  
    try {  
        const response = await fetch('', {  
            method: 'POST',  
            headers: {'Content-Type': 'application/x-www-form-urlencoded'},  
            body: 'action=api_raw_log'  
        });  
        const data = await response.text();  
          
        // 使用现代 Clipboard API  
        await navigator.clipboard.writeText(data);  
        showMessage('日志已复制到剪贴板', 'success');  
    } catch (error) {  
        // 降级方案：使用 textarea  
        try {  
            const response = await fetch('', {  
                method: 'POST',  
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},  
                body: 'action=api_raw_log'  
            });  
            const data = await response.text();  
              
            const textarea = document.createElement('textarea');  
            textarea.value = data;  
            document.body.appendChild(textarea);  
            textarea.select();  
            document.execCommand('copy');  
            document.body.removeChild(textarea);  
              
            showMessage('日志已复制到剪贴板', 'success');  
        } catch (fallbackError) {  
            showMessage('复制失败', 'error');  
            console.error('复制日志失败:', fallbackError);  
        }  
    }  
}
  
// 初始化    
document.addEventListener('DOMContentLoaded', function() {    
    // 恢复主题设置    
    const isDark = localStorage.getItem('theme') === 'dark';    
    document.documentElement.classList.toggle('dark', isDark);    
        
    // 设置主题图标    
    const sunIcon = document.getElementById('sun-icon');    
    const moonIcon = document.getElementById('moon-icon');    
        
    if (isDark) {    
        sunIcon.style.display = 'none';    
        moonIcon.style.display = 'block';    
    } else {    
        sunIcon.style.display = 'block';    
        moonIcon.style.display = 'none';    
    }    
      
    // 启动状态实时更新    
    startStatusUpdate();    
});    
</script>    
  
</body>    
</html>    
EOF
