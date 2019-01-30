# FreeSWITCH Chatbot

FreeSWITCH、ASR、TTS以及文本聊天机器人简易集成

Environment

- Debian 9 Stretch
- FreeSWITCH 1.8
- ASR: UniMRCP (modified by Baidu)
- TTS: Baidu TTS (Web API)
- Robot: echobot (wrapper)
- Python2 (limited by FreeSWITCH): python-dev python-requests

TODO

- Refactor (Plugin Support)

## FreeSWITCH 部署

### 安装

为了简化部署，我们直接为APT (Debian) 添加FreeSWITCH软件源。
```sh
wget -O - https://files.freeswitch.org/repo/deb/freeswitch-1.8/fsstretch-archive-keyring.asc | apt-key add -
echo "deb http://files.freeswitch.org/repo/deb/freeswitch-1.8/ stretch main" > /etc/apt/sources.list.d/freeswitch.list
echo "deb-src http://files.freeswitch.org/repo/deb/freeswitch-1.8/ stretch main" >> /etc/apt/sources.list.d/freeswitch.list
apt-get update && apt-get install -y freeswitch-meta-all
```

最后启动服务`systemctl start freeswitch`，使用`fs_cli -rRS`访问控制台。如果当前电脑上没有ipv6地址，这里将会出现`[ERROR] fs_cli.c:1673 main() Error Connecting []`错误，修改配置文件`/etc/freeswitch/autoload_configs/event_socket.conf.xml`中的`listen-ip`。
```xml
<configuration name="event_socket.conf" description="Socket Client">   
  <settings> 
    <param name="nat-map" value="false"/>
    <param name="listen-ip" value="127.0.0.1"/>
    <param name="listen-port" value="8021"/>
    <param name="password" value="ClueCon"/>
    <!--<param name="apply-inbound-acl" value="loopback.auto"/>-->
    <!--<param name="stop-on-bind-error" value="true"/>-->
  </settings>
</configuration>
```

### 配置

#### 修改默认密码

编辑`/etc/freeswitch/vars.xml`，修改默认密码`1234`。
```xml
<include>
  <X-PRE-PROCESS cmd="set" data="default_password=dev1234"/>
  <!-- ... others ... -->
</include>
```

#### 启用Python及UniMRCP支持
编辑`/etc/freeswitch/autoload_configs/modules.conf.xml`，添加`mod_python`、`mod_unimrcp`启用Python及UniMRCP模块。

- `mod_python`模块对外提供FreeSWITCH的Python2接口。
- `mod_unimrcp`模块集成了UniMRCP客户端接口，简单配置后就可以直接使用FreeSWITCH的标准接口通过UniMRCP服务器进行语音识别与语音合成。

```xml
<configuration name="modules.conf" description="Modules">
  <modules>
    <!-- ... others ... -->
    <load module="mod_python" />
    <load module="mod_unimrcp" />
  </modules>
</configuration>
```

#### 配置UniMRCP

>  具体配置请查阅 [UniMRCP mod_unimrcp](https://freeswitch.org/confluence/display/FREESWITCH/mod_unimrcp) 文档

FreeSWITCH没有为UniMRCP服务器提供MRCPv2协议的配置文件，需要在`/etc/freeswitch/mrcp_profiles`下新建文件`unimrcpserver-mrcp-v2.xml`。由于我们将FreeSWITC与UniMRCP服务器部署在同一台服务器上，这里`server-ip`为`127.0.0.1`。

```xml
<!-- unimrcpserver-mrcp-v2.xml -->
<include>
  <!-- UniMRCP Server MRCPv2 -->
  <profile name="unimrcpserver-mrcp2" version="2">
    <param name="server-ip" value="127.0.0.1"/>
    <param name="server-port" value="8060"/>
    <param name="resource-location" value=""/>
    <param name="client-ip" value="auto" />
    <param name="client-port" value="5069"/>
    <param name="sip-transport" value="udp"/>
    <param name="rtp-ip" value="auto"/>
    <param name="rtp-port-min" value="4000"/>
    <param name="rtp-port-max" value="5000"/>
    <param name="codecs" value="PCMU PCMA L16/96/8000"/>
    <param name="speechsynth" value="speechsynthesizer"/>
    <param name="speechrecog" value="speechrecognizer"/>
  </profile>
</include>
```

配置文件`unimrcpserver-mrcp-v2.xml`中的`speechsynth`和`speechrecog`的值可以在UniMRCP服务器的配置文件`unimrcpserver.xml`中找到。

```xml
<!-- unimrcpserver.xml -->
<unimrcpserver>
  <components>
    <rtsp-uas id="RTSP-Agent-1" type="UniRTSP">
      <resource-map>
        <param name="speechsynth" value="speechsynthesizer"/>
        <param name="speechrecog" value="speechrecognizer"/>
      </resource-map>
    </rtsp-uas>
  </components>
</unimrcpserver>
```

最后修改`/etc/freeswitch/autoload_configs/unimrcp.conf.xml`中`default-tts-profile`、`default-asr-profile`的值为我们之前添加的MRCPv2配置文件的名称`unimrcpserver-mrcp2`。

```xml
<configuration name="unimrcp.conf" description="UniMRCP Client">
  <settings>
    <!-- UniMRCP profile to use for TTS -->
    <param name="default-tts-profile" value="unimrcpserver-mrcp2"/>
    <!-- UniMRCP profile to use for ASR -->
    <param name="default-asr-profile" value="unimrcpserver-mrcp2"/>
    <!-- UniMRCP logging level to appear in freeswitch.log.  Options are:
         EMERGENCY|ALERT|CRITICAL|ERROR|WARNING|NOTICE|INFO|DEBUG -->
    <param name="log-level" value="DEBUG"/>
    <!-- Enable events for profile creation, open, and close -->
    <param name="enable-profile-events" value="false"/>

    <param name="max-connection-count" value="100"/>
    <param name="offer-new-connection" value="1"/>
    <param name="request-timeout" value="3000"/>
  </settings>

  <profiles>
    <X-PRE-PROCESS cmd="include" data="../mrcp_profiles/*.xml"/>
  </profiles>

</configuration>
```


## FAQ

### FreeSWITCH 呼叫接入慢

网上的大多数方法是修改 `/etc/freeswitch/dialplan/default.xml` 中 `field="${default_password}"` 规则下的休眠时间，但只有默认密码为`1234`时，该规则才会被触发。在前面我们已经修改了默认的密码，这里修改该规则将没有任何作用。

```xml
<condition field="${default_password}" expression="^1234$" break="never">
<action application="log" data="CRIT WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING "/>
<action application="log" data="CRIT Open $${conf_dir}/vars.xml and change the default_password."/>
<action application="log" data="CRIT Once changed type 'reloadxml' at the console."/>
<action application="log" data="CRIT WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING "/>
<action application="sleep" data="10000"/>
</condition>
```

在公网环境中，由于存在大量恶意SIP访问，FS资源被占用，新的呼叫将会进行长时等待。在低配服务器上，这种情况更加严重，等待时长可能高达30s+。为了减轻服务器负担，这里可以使用`ipset`与`iptables`命令配合屏蔽掉大量恶意IP。

```sh
# 创建集合blacksip并添加ip
ipset create blacksip hash:net family inet hashsize 1024 maxelem 1000000
ipset add blacksip 36.66.69.33
ipset add blacksip ...other bad ip...
# 这里直接拒绝来自blacksip集合内ip的所有访问途径
iptables -I INPUT -m set --match-set blacksip src -j DROP
```

这里，我提供了一个精简的IP屏蔽列表 `blackip/blacksip.ipset`，实际使用中发现大部分的恶意IP都是来自于荷兰，或许可以把整个荷兰的IP都给ban掉。这里也可从仓库[firehol/blocklist-ipsets](https://github.com/firehol/blocklist-ipsets)获取公开的恶意IP列表。



## FreeSWITCH Chatbot 集成

**EASY !!!**

`chatbot/fs2chatbot.py` 提供了FreeSWITCH与外部的交互接口。

**TODO...**
