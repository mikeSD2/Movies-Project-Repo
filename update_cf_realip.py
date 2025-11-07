#!/usr/bin/env python3
import urllib.request, ssl, os, tempfile, subprocess, sys, hashlib

OUT_FILE = "/www/server/nginx/conf/cloudflare_realip_auto.conf"
IPS_V4_URL = "https://www.cloudflare.com/ips-v4"
IPS_V6_URL = "https://www.cloudflare.com/ips-v6"

NGINX_TEST_CMDS = [
    ["nginx", "-t"],
    ["/www/server/nginx/sbin/nginx", "-t"],
]
NGINX_RELOAD_CMDS = [
    ["nginx", "-s", "reload"],
    ["/www/server/nginx/sbin/nginx", "-s", "reload"],
    ["systemctl", "reload", "nginx"],
    ["service", "nginx", "reload"],
]

def http_get(url, timeout=15):
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(url, context=ctx, timeout=timeout) as r:
        return r.read().decode("utf-8").strip()

def build_conf(ipv4_list, ipv6_list):
    lines = []
    lines.append("real_ip_header CF-Connecting-IP;")
    lines.append("real_ip_recursive on;")
    lines.append("")
    for cidr in ipv4_list:
        cidr = cidr.strip()
        if cidr:
            lines.append(f"set_real_ip_from {cidr};")
    for cidr in ipv6_list:
        cidr = cidr.strip()
        if cidr:
            lines.append(f"set_real_ip_from {cidr};")
    lines.append("")
    return "\n".join(lines)

def sha256(s): return hashlib.sha256(s.encode("utf-8")).hexdigest()

def write_atomic(path, content):
    d = os.path.dirname(path)
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".cfip.", dir=d)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(content)
    os.replace(tmp, path)

def run(cmd):
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
        return p.returncode, p.stdout.decode(errors="ignore"), p.stderr.decode(errors="ignore")
    except Exception as e:
        return 1, "", str(e)

def main():
    try:
        v4 = http_get(IPS_V4_URL).splitlines()
        v6 = http_get(IPS_V6_URL).splitlines()
    except Exception as e:
        print(f"[cf-realip] fetch failed: {e}", file=sys.stderr)
        sys.exit(1)

    new_conf = build_conf(v4, v6)
    old_conf = ""
    if os.path.exists(OUT_FILE):
        try:
            with open(OUT_FILE, "r", encoding="utf-8") as f:
                old_conf = f.read()
        except:
            old_conf = ""

    if sha256(new_conf) == sha256(old_conf):
        print("[cf-realip] no changes")
        sys.exit(0)

    write_atomic(OUT_FILE, new_conf)
    print("[cf-realip] config updated, testing nginx...")

    ok = False
    for cmd in NGINX_TEST_CMDS:
        rc, _, err = run(cmd)
        if rc == 0:
            ok = True
            break
    if not ok:
        print(f"[cf-realip] nginx -t failed: {err}", file=sys.stderr)
        sys.exit(2)

    reloaded = False
    for cmd in NGINX_RELOAD_CMDS:
        rc, _, _ = run(cmd)
        if rc == 0:
            reloaded = True
            break
    if not reloaded:
        print("[cf-realip] reload failed; apply manually", file=sys.stderr)
        sys.exit(3)

    print("[cf-realip] nginx reloaded")

if __name__ == "__main__":
    main()