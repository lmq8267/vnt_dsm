<div align="center">
  <a href="https://rustvnt.com">
<img src="https://socialify.git.ci/vnt-dev/vnt/image?description=1&logo=https%3A%2F%2Fraw.githubusercontent.com%2Fvnt-dev%2FVntApp%2Fmaster%2Fandroid%2Fapp%2Fsrc%2Fmain%2Fres%2Fmipmap-xxxhdpi%2Fic_launcher.png&name=1&pattern=Plus&theme=Auto" alt="" width="640" height="320" /></a>
<div>
  <img src="https://hits.5670567.xyz/api/count/incr/badge.svg?url=https%3A%2F%2Fgithub.com%2Flmq8267%2Fvnt_dsm&count_bg=%2379C83D&title_bg=%23555555&icon=github.svg&icon_color=%23F6F6F6&title=%E8%AE%BF%E9%97%AE%E7%BB%9F%E8%AE%A1&edge_flat=false"/>
	<h1>VNT - 群晖spk安装包</h1>
</div>
</div>

- 支持 `x86_64` `arm64` `arm` `armv7`  `i386`等架构，下载后在套件中心 手动上传安装即可，7.0测试可行，6.0暂未设备测试，可反馈
- 飞牛的在[lmq8267/vnt_fpk](https://github.com/lmq8267/vnt_fpk) ,在线配置文件[生成](https://lmq8267.github.io/VNT-Magisk/)

**如果你需要在外面通过手机端来访问群晖局域网内的其他设备（如：电脑、路由器等）无法访问时：**

- 确保你的群晖里配置文件填写了 `out_ips:` 参数，对应群晖的局域网网段 例如`192.168.1.0/24` 并且关闭了 内置IP代理参数 `no_proxy: true`
- 确保你的手机app端配置了 `in-ip` 群晖的局域网网段,群晖的虚拟ip，例如 `192.168.1.0/24,10.26.0.2`
- 去掉[vnt-dsm/scripts/real-start-stop-status](https://github.com/lmq8267/vnt_dsm/blob/aa0128987a90059f3dcae16bf1c6dc64e32b09e3/vnt-dsm/scripts/real-start-stop-status#L136)中的 # 使其生效，已经安装的话对应目录里`/var/packages/VNT/scripts/real-start-stop-status` 修改即可  
  <img width="922" height="178" alt="image" src="https://github.com/user-attachments/assets/da0a0dda-e476-43bd-8f0e-073484fe1c1f" />

  其中`10.26.0.0/24`对应你组网的虚拟网段，我没有添加是因为如果你自建服务器的话 改变了虚拟网段不是10.26.0.0/24就无效了

- 如还是无法访问 考虑 在上方命令后追加一行 `sysctl -w net.ipv4.ip_forward=1`

## UI预览

###  VNT客户端

**1. 上传spk安装**

<img width="1326" height="726" alt="image" src="https://github.com/user-attachments/assets/e9af3db6-b77a-4ebd-a9e0-66221166576a" />

**2. 需要赋予权限 `sudo sed -i 's/package/root/g' /var/packages/VNT/conf/privilege`**

<img width="895" height="635" alt="image" src="https://github.com/user-attachments/assets/b78a86f6-996c-4b49-bc2e-c9cf58229002" />

**3. 先打开 填写一个配置文件，再关闭窗口 停用插件 再重新启动**

<img width="1395" height="811" alt="image" src="https://github.com/user-attachments/assets/b2d1650f-dda3-44c8-91e7-3e53b09b743e" />
<img width="807" height="475" alt="image" src="https://github.com/user-attachments/assets/22bc75d2-6ec4-48fc-855e-aaf8c21ef4fe" />

**4. 再打开APP 可以看到信息了 也可以将 vnt客户端添加到桌面快捷**

<img width="1397" height="756" alt="image" src="https://github.com/user-attachments/assets/fcb5cb66-4a2d-4ea5-8827-fd19ad544c33" />


###  VNTS服务端

**1. 上传spk安装**

<img width="1074" height="649" alt="image" src="https://github.com/user-attachments/assets/8da65e67-ec36-4162-8882-48d086262d1a" />

**2. 打开配置**

<img width="965" height="559" alt="image" src="https://github.com/user-attachments/assets/4623bd8e-bad6-4611-8d51-a724e9ef74ce" />

<img width="1364" height="860" alt="image" src="https://github.com/user-attachments/assets/bb8fe6c6-39cf-443c-847f-a85fe9033800" />

<img width="1366" height="873" alt="image" src="https://github.com/user-attachments/assets/ae86f13f-8dca-4086-b2c2-d3849ac83c29" />




