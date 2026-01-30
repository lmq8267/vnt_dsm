#!/bin/bash    
  
VNTS_config="/var/packages/VNTS/var/config.yaml"
VNTS_bin="/var/packages/VNTS/target/bin/vnts"
VNTS_log="/var/packages/VNTS/var/VNTS.log"

LOG_TEXT=""    
if [[ -f "/var/packages/VNTS/var/VNTS.log" ]]; then    
    LOG_TEXT=$(cat "/var/packages/VNTS/var/VNTS.log" | sed 's/</\&lt;/g;s/>/\&gt;/g')    
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
    WEB_ENABLED="false"  
    WEB_PORT=""
      
    if pidof "vnts" >/dev/null 2>&1; then
        RUNNING="true"
        PID=$(pidof "vnts" | head -n 1)
        # 读取Web配置  
        if [[ -f "$VNTS_config" ]]; then  
            WEB_ENABLED=$(grep -A 10 "web:" "$VNTS_config" | grep "enabled:" | awk '{print $2}' | tr -d '"' | head -n 1)  
            WEB_PORT=$(grep -A 10 "web:" "$VNTS_config" | grep "port:" | awk '{print $2}' | tr -d '"')  
        fi
          
        # 从文件读取启动时间  
        if [[ -f "/var/packages/VNTS/var/vnts_time" ]]; then  
            start_time=$(cat /var/packages/VNTS/var/vnts_time)  
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
    echo "{\"running\": $RUNNING, \"pid\": \"$PID\", \"uptime\": \"$UPTIME\", \"web_enabled\": \"$WEB_ENABLED\", \"web_port\": \"$WEB_PORT\"}"      
    exit 0      
fi
  
if [[ "$ACTION" == "api_log" ]] || [[ "$ACTION" == "api_raw_log" ]]; then
    LOG_TEXT=""
    if [[ -f "/var/packages/VNTS/var/VNTS.log" ]]; then
        LOG_TEXT=$(cat "/var/packages/VNTS/var/VNTS.log")
    fi
    echo "Content-Type: text/plain; charset=UTF-8"
    echo ""
    echo "$LOG_TEXT"
    exit 0
fi

if [[ "$ACTION" == "clear_log" ]]; then
    if echo "" > "/var/packages/VNTS/var/VNTS.log" 2>/dev/null; then
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
    # 解析表单数据并生成配置文件  
    tokens=$(echo "$POST_DATA" | grep -o 'token[^&]*' | sed 's/token=//g' | tr '\n' ',' | sed 's/,$//')
    [ -z "$tokens" ] || tokens=$(url_decode "$tokens" | xargs)
    service_port=$(echo "$POST_DATA" | sed -n 's/.*service_port=\([^&]*\).*/\1/p')
    [ -z "$service_port" ] || service_port=$(url_decode "$service_port" | xargs)
    gateway_ip=$(echo "$POST_DATA" | sed -n 's/.*gateway_ip=\([^&]*\).*/\1/p')
    [ -z "$gateway_ip" ] || gateway_ip=$(url_decode "$gateway_ip" | xargs)
    finger_check=$(echo "$POST_DATA" | sed -n 's/.*finger_check=\([^&]*\).*/\1/p') 
    [ -z "$finger_check" ] || finger_check=$(url_decode "$finger_check" | xargs)
    web_enabled=$(echo "$POST_DATA" | sed -n 's/.*web_enabled=\([^&]*\).*/\1/p')
    [ -z "$web_enabled" ] || web_enabled=$(url_decode "$web_enabled" | xargs)
    web_port=$(echo "$POST_DATA" | sed -n 's/.*web_port=\([^&]*\).*/\1/p')
    [ -z "$web_port" ] || web_port=$(url_decode "$web_port" | xargs)
    web_username=$(echo "$POST_DATA" | sed -n 's/.*web_username=\([^&]*\).*/\1/p')
    [ -z "$web_username" ] || web_username=$(url_decode "$web_username" | xargs)
    web_password=$(echo "$POST_DATA" | sed -n 's/.*web_password=\([^&]*\).*/\1/p')
    [ -z "$web_password" ] || web_password=$(url_decode "$web_password" | xargs)
    netmask_ip=$(echo "$POST_DATA" | sed -n 's/.*netmask_ip=\([^&]*\).*/\1/p')
    [ -z "$netmask_ip" ] || netmask_ip=$(url_decode "$netmask_ip" | xargs)
    log_enabled=$(echo "$POST_DATA" | sed -n 's/.*log_enabled=\([^&]*\).*/\1/p')
    [ -z "$log_enabled" ] || log_enabled=$(url_decode "$log_enabled" | xargs)
    VNTS_CMD=""
    
    # 处理空值，填充默认值  
    [[ -z "$service_port" ]] && service_port="29872"
    [[ -z "$gateway_ip" ]] && gateway_ip="10.26.0.1"
    [[ -z "$finger_check" ]] && finger_check="false"
    [[ -z "$netmask_ip" ]] && netmask_ip="255.255.255.0"
    [[ -z "$log_enabled" ]] && log_enabled="true"
    VNTS_CMD="-p ${service_port} -g ${gateway_ip} -m ${netmask_ip}"
    
    # 处理WEB配置的默认值  
    if [[ "$web_enabled" == "true" ]]; then
        [[ -z "$web_port" ]] && web_port="29870"
        [[ -z "$web_username" ]] && web_username="admin"
        [[ -z "$web_password" ]] && web_password="admin"
        VNTS_CMD="${VNTS_CMD} -P ${web_port} -U ${web_username} -W ${web_password}"
    else
    	VNTS_CMD="${VNTS_CMD} -P 0"
    fi
    # 生成配置文件内容  
    cat > "$VNTS_config" << EOF
port: $service_port
gateway: $gateway_ip
token_whitelist: [$tokens]
finger_check: $finger_check
EOF
    # 添加WEB配置  
    if [[ "$web_enabled" == "true" ]]; then
        cat >> "$VNTS_config" << EOF
web:
  enabled: true
  port: $web_port
  username: "$web_username"
  password: "$web_password"
EOF
    fi
  
    # 添加子网掩码配置  
    if [[ -n "$netmask_ip" ]]; then
        echo "netmask: $netmask_ip" >> "$VNTS_config"
    fi
  
    # 添加日志配置  
    if [[ "$log_enabled" == "true" ]]; then
        echo "log_enabled: true" >> "$VNTS_config"
        VNTS_CMD="${VNTS_CMD} -l console"
    else  
        echo "log_enabled: false" >> "$VNTS_config"
        VNTS_CMD="${VNTS_CMD} -l /dev/null"
    fi
    
    [[ "$finger_check" == "true" ]] && VNTS_CMD="${VNTS_CMD} -f"
    echo "$VNTS_CMD" >/var/packages/VNTS/var/vnts.cmd
    echo "restart" > /var/packages/VNTS/var/start-stop
fi    
  
if [[ "$ACTION" == "start" ]]; then
    echo "start" > /var/packages/VNTS/var/start-stop
fi    
  
if [[ "$ACTION" == "stop" ]]; then 
    echo "stop" > /var/packages/VNTS/var/start-stop
fi     
  
RUNNING="false"    
pgrep -f "$VNTS_bin" >/dev/null 2>&1 && RUNNING="true"

# 配置读取  
CURRENT_PORT="29872"
CURRENT_GATEWAY="10.26.0.1"
CURRENT_TOKENS=""
CURRENT_FINGER_CHECK="false"
CURRENT_WEB_ENABLED="false"
CURRENT_WEB_PORT="29870"
CURRENT_WEB_USERNAME="admin"
CURRENT_WEB_PASSWORD="admin"
CURRENT_NETMASK="255.255.255.0"
CURRENT_LOG_ENABLED="true"
  
if [[ -s "$VNTS_config" ]]; then
    CURRENT_PORT=$(grep "port:" "$VNTS_config" | sed 's/port: //' | awk '{print $1}' | head -n 1 | xargs)
    CURRENT_GATEWAY=$(grep "gateway:" "$VNTS_config" | sed 's/gateway: //' | xargs)
    CURRENT_TOKENS=$(grep "token_whitelist:" "$VNTS_config" | sed 's/token_whitelist: \[//;s/\]//;s/,/ /g' | xargs)
    CURRENT_FINGER_CHECK=$(grep "finger_check:" "$VNTS_config" | sed 's/finger_check: //' | xargs)
    CURRENT_WEB_ENABLED=$(grep -A 1 "web:" "$VNTS_config" | grep "enabled:" | sed 's/enabled: //' | xargs)
    CURRENT_WEB_PORT=$(grep -A 3 "web:" "$VNTS_config" | grep "port:" | sed 's/port: //' | xargs)
    CURRENT_WEB_USERNAME=$(grep -A 4 "web:" "$VNTS_config" | grep "username:" | sed 's/username: "//;s/"//' | xargs)
    CURRENT_WEB_PASSWORD=$(grep -A 5 "web:" "$VNTS_config" | grep "password:" | sed 's/password: "//;s/"//' | xargs)
    CURRENT_NETMASK=$(grep "netmask:" "$VNTS_config" | sed 's/netmask: //' | xargs)
    CURRENT_LOG_ENABLED=$(grep "log_enabled:" "$VNTS_config" | grep -q "true" && echo "true" || echo "false" | xargs)
fi
  
cat <<EOF
<!DOCTYPE html>  
<html lang="zh">  
<head>  
<meta charset="UTF-8">
<link rel="icon" type="image/png"
        href="data:image/png;base64,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" />
<title>VNTS 服务器配置管理</title>  
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
    margin-bottom: 10px;  
    transition: transform 0.2s,opacity 0.2s;  
}  
button:hover {  
    transform: scale(1.05);  
    opacity: 0.9;  
}  
input[type="text"], input[type="number"], input[type="password"] {  
    width: 100%;  
    padding: 12px;  
    border-radius: 8px;  
    border: 1px solid #ccc;  
    margin-bottom: 5px;  
    box-sizing: border-box;  
    font-size: 14px;  
}  
.dark input {  
    background: #222;  
    color: #eee;  
    border-color: #444;  
}  
label {  
    display: block;  
    margin-bottom: 5px;  
    font-weight: bold;  
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
.list-group {  
    margin-bottom: 10px;  
}  
.list-item {  
    display: flex;  
    margin-bottom: 5px;  
    align-items: center;  
}  
.list-item input {  
    flex: 1;  
    margin-right: 10px;  
}  
.list-item button {  
    margin: 0;  
    background: linear-gradient(135deg,#eb3349,#f45c43);  
}  
.add-btn {  
    background: linear-gradient(135deg,#11998e,#38ef7d);  
}  
.form-line {  
    margin-bottom: 15px;  
}  
.wg-toggle {  
    display: flex;  
    gap: 20px;  
    margin-bottom: 5px;  
}  
.custom-radio {  
    display: flex;  
    align-items: center;  
    cursor: pointer;  
}  
.custom-radio input[type="radio"] {  
    display: none;  
}  
.box-check {  
    width: 20px;  
    height: 20px;  
    border: 2px solid #ccc;  
    border-radius: 50%;  
    margin-right: 8px;  
    position: relative;  
    transition: all 0.3s ease;  
}  
.custom-radio input[type="radio"]:checked + .box-check {  
    border-color: #11998e;  
    background: #11998e;  
}  
.custom-radio input[type="radio"]:checked + .box-check::after {  
    content: '';  
    width: 8px;  
    height: 8px;  
    background: white;  
    border-radius: 50%;  
    position: absolute;  
    top: 50%;  
    left: 50%;  
    transform: translate(-50%, -50%);  
}  
.switch {  
    position: relative;  
    display: inline-block;  
    width: 50px;  
    height: 25px;  
}  
.switch input {  
    opacity: 0;  
    width: 0;  
    height: 0;  
}  
.slider {  
    position: absolute;  
    cursor: pointer;  
    top: 0;  
    left: 0;  
    right: 0;  
    bottom: 0;  
    background-color: #ccc;  
    transition: .4s;  
    border-radius: 25px;  
}  
.slider:before {  
    position: absolute;  
    content: "";  
    height: 18px;  
    width: 18px;  
    left: 4px;  
    bottom: 4px;  
    background-color: white;  
    transition: .4s;  
    border-radius: 50%;  
}  
input:checked + .slider {  
    background-color: #11998e;  
}  
input:checked + .slider:before {  
    transform: translateX(25px);  
}
.divider {  
    height: 1px;  
    background: #ddd; 
    margin: 20px 0;  
    border: none;  
}
/* 红色边框和闪烁动画 */  
.input-error {  
    border-color: red !important;  
    outline: none;  
}  
@keyframes blink-red {  
    0%, 100% {  
        box-shadow: 0 0 5px 2px rgba(255, 0, 0, 0.7);  
    }  
    50% {  
        box-shadow: none;  
    }  
}  
.blink {  
    animation: blink-red 1s infinite;  
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
    .container { padding: 10px; }  
    button { margin-bottom: 5px; }  
}  
</style>
</head>  
<body>  
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
<h1>VNTS 服务端</h1>  
<div class="status">  
    状态: <span id="service-status">检查中...</span>  
</div>  
<br>  
<button id="control-button" onclick="control('$(if [ "$RUNNING" = "true" ]; then echo "stop"; else echo "start"; fi)')" style="background: $(if [ "$RUNNING" = "true" ]; then echo "linear-gradient(135deg,#eb3349,#f45c43)"; else echo "linear-gradient(135deg,#11998e,#38ef7d)"; fi);">  
$(if [ "$RUNNING" = "true" ]; then echo "停止"; else echo "启动"; fi)  
</button>  
<button onclick="window.open('http://'+window.location.hostname+':$CURRENT_WEB_PORT')" style="background: linear-gradient(135deg,#667eea,#764ba2); display: none;">Web页面</button>
<button onclick="showModal('log-modal')" style="background: linear-gradient(135deg,#43cea2,#185a9d);">运行日志</button>  
</div>  
  
<div class="card">  
<h2>服务器配置</h2>  
<form method="post" id="config-form" onsubmit="return validateForm()"> 
<input type="hidden" name="action" value="save_config">

<label>服务监听端口:</label>  
<input type="number" name="service_port" id="service_port" value="$CURRENT_PORT" placeholder="29872" min="1" max="65535">
<p style="font-size: 12px; color: #666; margin-top: 5px;">用于vnt客户端连接的端口</p>
<hr class="divider">

<label>虚拟网关IP:</label>  
<input type="text" name="gateway_ip" id="gateway_ip" value="$CURRENT_GATEWAY" placeholder="10.26.0.1"> 
<p style="font-size: 12px; color: #666; margin-top: 5px;">指定组网的虚拟网关，当客户端未设置IP时，将分配此网段的IP</p>
<hr class="divider">

<label>Token白名单:</label>  
<div id="token_whitelist" class="list-group">  
EOF

# 添加现有的token输入框  
if [[ -n "$CURRENT_TOKENS" ]]; then
    for token in $CURRENT_TOKENS; do
        echo "<div class=\"list-item\"><input type=\"text\" name=\"token\" value=\"$token\" placeholder=\"输入token\" maxlength=\"63\"><button type=\"button\" onclick=\"this.parentElement.remove()\">- 移除</button></div>"  
    done
fi
  
cat <<EOF
</div>  
<button type="button" class="add-btn" onclick="addToken()">+ 添加</button>  
<p style="font-size: 12px; color: #666; margin-top: 5px;">指定后只有这里允许的token才能连接此服务器，留空则不限制，所有token都可以连接</p>
<hr class="divider">

<label>子网掩码:</label>  
<input type="text" name="netmask_ip" id="netmask_ip" value="$CURRENT_NETMASK" placeholder="255.255.255.0">
<p style="font-size: 12px; color: #666; margin-top: 5px;">指定组网的子网掩码</p> 
<hr class="divider">

<div class="form-line">  
<label style="display: flex; align-items: center; justify-content: space-between;">  
<span>启用WEB界面:</span>  
<label class="switch">
<input type="hidden" name="web_enabled" value="false"> 
<input type="checkbox" name="web_enabled" id="web_enabled" value="true" $([ "$CURRENT_WEB_ENABLED" = "true" ] && echo "checked") onchange="toggleWebConfig()">  
<span class="slider"></span>  
</label>  
</label>  
</div>

<div id="web_config" style="display: $([ "$CURRENT_WEB_ENABLED" = "true" ] && echo "block" || echo "none");">
<label>WEB监听端口:</label>
<input type="number" name="web_port" id="web_port" value="$CURRENT_WEB_PORT" placeholder="29870" min="1" max="65535">
<p style="font-size: 12px; color: #666; margin-top: 5px;">WEB管理界面访问端口</p>
<hr class="divider">

<label>WEB用户名:</label>
<input type="text" name="web_username" id="web_username" value="$CURRENT_WEB_USERNAME" placeholder="admin" maxlength="20" autocomplete="off">
<p style="font-size: 12px; color: #666; margin-top: 5px;">WEB页面登录用户名</p>
<hr class="divider">

<label>WEB密码:</label>
<input type="password" name="web_password" id="web_password" value="$CURRENT_WEB_PASSWORD" placeholder="admin" maxlength="24" autocomplete="new-password" onfocus="this.type='text'" onblur="this.type='password'">
<p style="font-size: 12px; color: #666; margin-top: 5px;">WEB页面登录密码</p>
</div>
<hr class="divider">

<div class="form-line">  
<label style="display: flex; align-items: center; justify-content: space-between;">  
<span>指纹校验:</span>  
<label class="switch">
<input type="hidden" name="finger_check" value="false">
<input type="checkbox" name="finger_check" value="true" $([ "$CURRENT_FINGER_CHECK" = "true" ] && echo "checked")>  
<span class="slider"></span>  
</label>  
</label>  
<p style="font-size: 12px; color: #666; margin-top: 5px;">开启后只会转发指纹正确的客户端数据包，增强安全性，这会损失一部分性能</p>  
</div>
<hr class="divider">

<div class="form-line">  
<label style="display: flex; align-items: center; justify-content: space-between;">  
<span>启用日志:</span>  
<label class="switch">
<input type="hidden" name="log_enabled" value="false">
<input type="checkbox" name="log_enabled" value="true" $([ "$CURRENT_LOG_ENABLED" = "true" ] && echo "checked")>  
<span class="slider"></span>  
</label>  
</label>  
<p style="font-size: 12px; color: #666; margin-top: 5px;">记录详细运行日志</p>  
</div>
<hr class="divider">

<br>  
<button type="submit" onclick="return validateForm()">保存配置</button>
</form>  
</div>  
</div>  
  
<div id="log-modal" class="modal" style="display: none;" onclick="if(event.target===this) hideModal('log-modal')">  
<div class="modal-content">  
<div style="display: flex; justify-content: space-between; align-items: center;">  
    <h2 style="margin: 0;">VNTS 运行日志</h2>  
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
    }, 4000);      
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
  
// Token管理函数
function addToken() {
    const group = document.getElementById("token_whitelist");
    const div = document.createElement("div");
    div.className = "list-item";
    const input = document.createElement("input");
    input.type = "text";
    input.name = "token";
    input.placeholder = "输入token";
    input.maxLength = 63;
    input.addEventListener('input', validateTokenInput);
    const removeBtn = document.createElement("button");
    removeBtn.type = "button";
    removeBtn.textContent = "- 移除";
    removeBtn.onclick = () => div.remove();
    div.appendChild(input);
    div.appendChild(removeBtn);
    group.appendChild(div);
}

// WEB配置显示/隐藏
function toggleWebConfig() {
    const webEnabled = document.getElementById('web_enabled');
    const webConfig = document.getElementById('web_config');
    webConfig.style.display = webEnabled.checked ? 'block' : 'none';
}

// 显示错误提示函数
function showError(inputId, message) {
    const input = document.getElementById(inputId);
    input.classList.add('input-error');
    input.focus();
      
    // 移除旧的错误提示
    const oldError = document.getElementById(inputId + '-error');
    if (oldError) oldError.remove();
      
    // 创建新的错误提示
    const error = document.createElement('div');
    error.id = inputId + '-error';
    error.style.color = 'red';
    error.style.fontSize = '13px';
    error.style.marginTop = '4px';
    error.textContent = message;
    input.insertAdjacentElement('afterend', error);
      
    // 添加闪烁动画  
    input.classList.add('blink');
}

// 清除错误提示  
function clearError(inputId) {
    const input = document.getElementById(inputId);
    if (input) {
        input.classList.remove('input-error', 'blink');
        const error = document.getElementById(inputId + '-error');
        if (error) error.remove();
    }
}

// Token输入验证
function validateTokenInput(e) {
    const input = e.target;
    const value = input.value;  
    const inputId = input.id || 'token-' + Math.random().toString(36).substr(2, 9);
      
    // 为动态创建的input设置ID
    if (!input.id) {
        input.id = inputId;
    }
      
    // 检查非法字符
    const illegalChars = /[\`|\/,;"'}\]\[)\(&^$#\s]/;
    if (illegalChars.test(value)) {
        showError(input.id, '含有非法字符');
        return false;
    }
      
    // 检查长度
    if (value.length > 63) {
        showError(input.id, '长度不能超过63个字符');
        return false;
    }
      
    clearError(input.id);
    return true;
}
  
// WEB用户名验证
function validateWebUsername(e) {
    const input = e.target;
    const value = input.value;
      
    // 检查非法字符
    const illegalChars = /[\`|\/,;"'}\]\[)\(&^$#\s]/;
    if (illegalChars.test(value)) {
        showError('web_username', '含有非法字符');
        return false;
    }
      
    // 检查长度
    if (value.length > 20) {
        showError('web_username', '长度不能超过20个字符');
        return false;
    }
      
    clearError('web_username');
    return true;
}
  
// WEB密码验证
function validateWebPassword(e) {
    const input = e.target;
    const value = input.value;
  
    // 检查非法字符  
    const illegalChars = /[\`|\/,;"'}\]\[)\(&^$#\s]/;
    if (illegalChars.test(value)) {
        showError('web_password', '含有非法字符');
        return false;
    }
     
    // 检查长度 
    if (value.length > 24) {
        showError('web_password', '长度不能超过24个字符');
        return false;
    }
      
    clearError('web_password');
    return true;
}
  
// IP地址验证
function isValidIPv4(ip) {
    const parts = ip.split('.');
    if (parts.length !== 4) return false;
    for (let part of parts) {
        if (!/^\d+$/.test(part)) return false;
        const num = Number(part);
        if (num < 0 || num > 255) return false;
    }
    return true;
}
  
// 网关IP验证
function validateGatewayIp(e) {  
    const input = e.target;  
    const value = input.value;  
      
    // 网关IP必须以1结尾  
    const gatewayPattern = /^(?:(?:25[0-5]|2[0-4][0-9]|1?[0-9]{1,2})\.){3}1$/;  
      
    if (value && !gatewayPattern.test(value)) {  
        showError('gateway_ip', '网关IP格式错误，必须以1结尾（如：10.26.0.1）');  
        return false;  
    }  
      
    clearError('gateway_ip');  
    return true;  
}
  
// 子网掩码验证  
function validateNetmaskIp(e) {  
    const input = e.target;  
    const value = input.value;  
      
    // 子网掩码必须以0结尾  
    const netmaskPattern = /^(?:(?:25[0-5]|2[0-4][0-9]|1?[0-9]{1,2})\.){3}0$/;  
      
    if (value && !netmaskPattern.test(value)) {  
        showError('netmask_ip', '子网掩码格式错误，必须以0结尾（如：255.255.255.0）');  
        return false;  
    }  
      
    clearError('netmask_ip');  
    return true;  
}

// 表单提交验证
function validateForm() {
    let isValid = true;
      
    // 验证所有token输入框
    const tokenInputs = document.querySelectorAll('input[name="token"]');
    tokenInputs.forEach(input => {
        if (!validateTokenInput({ target: input })) {
            isValid = false;  
        }
    });
      
    // 验证WEB用户名（如果启用WEB）
    if (document.getElementById('web_enabled').checked) {
        const webUsername = document.getElementById('web_username');
        if (!validateWebUsername({ target: webUsername })) {
            isValid = false;
        }
          
        const webPassword = document.getElementById('web_password');
        if (!validateWebPassword({ target: webPassword })) {
            isValid = false;
        }
    }
      
    // 验证网关IP
    const gatewayIp = document.getElementById('gateway_ip');
    if (!validateGatewayIp({ target: gatewayIp })) {
        isValid = false;
    }
      
    // 验证子网掩码
    const netmaskIp = document.getElementById('netmask_ip');
    if (!validateNetmaskIp({ target: netmaskIp })) {
        isValid = false;
    }
      
    if (!isValid) {
        showMessage('⚠️ 请修正错误的参数值后再提交吧', 'error');
        return false; // 阻止表单提交
    }
    
    return true; // 允许提交
}
  
// 控制函数  
let pendingAction = null;  
function control(action) {    
    pendingAction = action;        
    const title = document.getElementById('confirm-title');    
    const message = document.getElementById('confirm-message');        
    if (action === 'start') {    
        title.textContent = '确认启动';    
        message.textContent = '您确定要启动 VNTS 服务吗？';    
    } else {    
        title.textContent = '确认停止';    
        message.textContent = '您确定要停止 VNTS 服务吗？';    
    }        
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
    document.body.style.overflow = 'hidden';  
    if (modalId === 'log-modal') {  
        updateLog();  
        startLogUpdate();      
    }      
}    
  
function hideModal(modalId) {      
    document.getElementById(modalId).style.display = 'none';  
    document.body.style.overflow = '';  
    if (modalId === 'log-modal' && updateIntervals.log) {      
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
let countdownIntervals = {};  
  
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
        // 处理Web页面按钮的显示/隐藏  
        const webButton = document.querySelector('button[onclick*="window.open"]');  
        if (data.running && data.web_enabled === "true" && data.web_port && data.web_port !== "0") {  
            if (webButton) {  
                webButton.style.display = 'inline-block';  
                webButton.onclick = () => window.open('http://' + window.location.hostname + ':' + data.web_port);  
            }  
        } else {  
            if (webButton) {  
                webButton.style.display = 'none';  
            }  
        }
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
  
// 实时更新日志      
function startLogUpdate() {    
    updateLog();    
    let countdown = 10;    
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
        data = data.replace(/INFO/g, '<span style="color: green;">信息</span>')    
                  .replace(/ERROR/g, '<span style="color: red;">错误</span>')    
                  .replace(/WARN/g, '<span style="color: #ff9800;">警告</span>');  
        const logPre = document.querySelector('#log-modal pre');      
        if (logPre) {      
            logPre.innerHTML = data;      
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
        const blob = new Blob([data], { type: 'text/plain;charset=utf-8' });    
        const url = window.URL.createObjectURL(blob);    
        const a = document.createElement('a');    
        a.href = url;    
        a.download = 'vnts_log_' + new Date().toISOString().slice(0, 19).replace(/:/g, '-') + '.log';    
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
        await navigator.clipboard.writeText(data);    
        showMessage('日志已复制到剪贴板', 'success');    
    } catch (error) {    
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
    // 为所有输入框添加实时验证事件监听器  
    // Token 输入框验证  
    const tokenInputs = document.querySelectorAll('input[name="token"]');  
    tokenInputs.forEach(input => {  
        input.addEventListener('input', validateTokenInput);  
        input.addEventListener('focus', validateTokenInput);  
    });  
      
    // WEB用户名验证  
    const webUsername = document.getElementById('web_username');  
    if (webUsername) {  
        webUsername.addEventListener('input', validateWebUsername);  
        webUsername.addEventListener('focus', validateWebUsername);  
    }  
      
    // WEB密码验证  
    const webPassword = document.getElementById('web_password');  
    if (webPassword) {  
        webPassword.addEventListener('input', validateWebPassword);  
        webPassword.addEventListener('focus', validateWebPassword);  
    }  
      
    // 网关IP验证  
    const gatewayIp = document.getElementById('gateway_ip');  
    if (gatewayIp) {  
        gatewayIp.addEventListener('input', validateGatewayIp);  
        gatewayIp.addEventListener('focus', validateGatewayIp);  
    }  
      
    // 子网掩码验证  
    const netmaskIp = document.getElementById('netmask_ip');  
    if (netmaskIp) {  
        netmaskIp.addEventListener('input', validateNetmaskIp);  
        netmaskIp.addEventListener('focus', validateNetmaskIp);  
    }
    // 启动状态实时更新      
    startStatusUpdate();
});
</script>

</body>
</html>
EOF

