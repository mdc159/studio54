 Issue                                                                                                                         
                                                                                                                                
  Donna (Hermes hub agent on Studio54, 148.230.95.154, hostname donna) couldn't SSH into Miguel's Samsung S24 running Termux    
  (miguels-s24, user u0_a369, port 8022) over Tailscale. Two symptoms appeared in sequence:                                     
                                                                                                                                
  1. Permission denied (publickey,password,keyboard-interactive) — phone reachable, sshd accepting connections, key offered, but
   refused.                                                                                                                     
  2. Later: connect to host miguels-s24 port 8022: Connection refused — port closed entirely.                                   
                                                                                                                                
  The desired milestone was a bounded readiness check returning SAM_AUTH_OK.                                                    
                                                                                                                                
  Diagnosis                                                                                                                     
                                                                  
  Worked outward from "what do we know to be true" before guessing:                                                             
                                                                  
  1. Located Donna. Searched local hermes-grid project + ssh config; deploy.sh:18 defines HUB="Studio54", and ~/.ssh/config had 
  Host Studio54 already wired up — confirmed Donna runs on Studio54 reachable via ssh Studio54.
  2. Verified Donna's key actually exists. SSHed to Studio54 read-only and confirmed ~/.ssh/donna_to_victoria_ed25519{,.pub}    
  present with fingerprint SHA256:Xv2Vhf3mIR+YbXtbn38cNlJIOBeH3Zb1HH9Ifqcjv0k — exactly matching the spec. So Donna was offering
   the right key; the failure was on the receiving end.
  3. Verified network path. tailscale status on Studio54 showed miguels-s24 = 100.83.211.53 (idle). Tailnet was healthy, so this
   wasn't a routing or MagicDNS issue.                                                                                          
  4. Found the load-bearing clue. Grepped local docs for the donna-to-victoria pubkey string. Hit two files:
    - debug.donna.md — the current key (AAAAC3...IBPPs0LEC6v4...)                                                               
    - ssh-phone.md — a different, older key (AAAAC3...ILAXHeP...)                                                               
                                                                                                                                
  ssh-phone.md was the bootstrap script previously used to seed authorized_keys on the phone. The key in it had since been      
  rotated to the new donna-to-victoria key, but the phone still had the old one installed. That fully explained symptom #1:     
  phone said "publickey rejected" because Donna was offering a key the phone had never been told to accept.                     

  ssh-phone.md was the bootstrap script previously used to seed authorized_keys on the phone. The key in it had since been
  rotated to the new donna-to-victoria key, but the phone still had the old one installed. That fully explained symptom #1:
  phone said "publickey rejected" because Donna was offering a key the phone had never been told to accept.
  rotated to the new donna-to-victoria key, but the phone still had the old one installed. That fully explained symptom #1:
  phone said "publickey rejected" because Donna was offering a key the phone had never been told to accept.
  5. Explained symptom #2. From debug.donna.md's history, sshd had been started in -ddd debug mode without -D, which exits after
   one connection. So between Permission-denied and Connection-refused, the daemon simply died.
  6. Probed live state from Donna. Ran ssh -v from Studio54 to the phone — got Connection refused, confirming sshd was still
  down. So the immediate blocker was "start sshd back up"; the underlying blocker was "and use the new key when you do."

  Correction

  Three changes, in this order:

  1. On the phone (Termux), via Miguel pasting a single snippet:
    - Overwrote $HOME/.ssh/authorized_keys with one clean line containing the current donna-to-victoria pubkey (using printf
  '%s\n', not echo, to avoid wrapping/\r artifacts).
    - Set chmod 700 on $HOME and $HOME/.ssh, chmod 600 on authorized_keys.
    - Killed any stale sshd, restarted it in normal daemon mode (no -D, no -ddd) on -p 8022 with PubkeyAuthentication=yes,
  password/kbd-interactive disabled.
    - Verified ssh-keygen -lf printed the expected Xv2Vhf3mIR+...qcjv0k fingerprint and :8022 was listening.
  2. From this WSL box, drove the Donna retry via ssh Studio54 'ssh ... u0_a369@miguels-s24 ...'. Got SAM_AUTH_OK + uname -a +
  python3 path back, exit 0. Also confirmed the ssh sam alias path works cleanly with no flag overrides.
  3. Local doc hygiene so this can't regress:
    - Rewrote ~/projects/company/ssh-phone.md to reference the current key and explicitly mark the old key as
  obsolete-do-not-reapply.
    - Updated ~/projects/hermes-grid/ssh/ssh_config.snippet's phone-termux block with the real miguels-s24 / u0_a369 / 8022 /
  donna_to_victoria_ed25519 values and aliased it to sam mobile-hermes s24.

  Studio54's actual ~/.ssh/config was already correctly configured — no edit needed there.

  TL;DR

  The phone had a stale public key from before the Donna keypair was rotated, and Termux sshd had been left in debug mode that  
  exited after one connection. Replaced the key on the phone, restarted sshd as a normal daemon, and Donna's readiness probe now
   passes.                     
 
 
 
 
 
 
 Prompt: Help Diagnose Donna → Android/Termux SSH Access for Mobile-Hermes Agent

    We are integrating an Android/Termux phone agent into a Hermes/Paperclip multi-agent fleet. The phone agent is already running locally in     Termux. Donna, the main Hermes agent running on the VPS/cloud side, is trying to establish SSH access into the phone over     Tailscale/MagicDNS so she can run bounded readiness checks and eventually communicate with the mobile-edge agent safely.

    The phone is reachable by hostname:

      ─ text
      miguels-s24

    The Termux SSH username appears to be:

      ─ text
      u0_a369

    The SSH port is:

      ─ text
      8022

    Donna has a dedicated Ed25519 SSH key for this phone/mobile-agent path. The public key fingerprint Donna is offering is:

      ─ text
      SHA256:Xv2Vhf3mIR+YbXtbn38cNlJIOBeH3Zb1HH9Ifqcjv0k

    The public key line Donna wants accepted by the phone is:

      ─ text
      ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBPPs0LEC6v4GJ2HVtxbYxO07fjpd1SOtGdqyDVCcNF/ donna-to-victoria@hermes-grid

    What Donna is trying to do

    Donna wants to run this kind of SSH command from the VPS side:

      ─ bash
      ssh \
        -o BatchMode=yes \
        -o PreferredAuthentications=publickey \
        -o PubkeyAuthentication=yes \
        -o IdentitiesOnly=yes \
        -o StrictHostKeyChecking=accept-new \
        -o ConnectTimeout=10 \
        -i ~/.ssh/donna_to_victoria_ed25519 \
        -p 8022 \
        u0_a369@miguels-s24 \
        'printf SAM_AUTH_OK\n; uname -a; command -v tmux || true; command -v python3 || true'

    The intended first milestone is simply:

      ─ text
      SAM_AUTH_OK

    No destructive actions. No package installs unless explicitly approved. No secrets copied. No session DB or memory store exfiltration.

    ────────────────────────────────────

    Symptoms observed so far

    1. Earlier, the phone was reachable, but rejected Donna’s key

    Donna’s SSH debug output showed:

      ─ text
      Offering public key: ED25519 SHA256:Xv2Vhf3mIR+YbXtbn38cNlJIOBeH3Zb1HH9Ifqcjv0k explicit
      Authentications that can continue: publickey,password,keyboard-interactive
      Permission denied (publickey,password,keyboard-interactive)

    This means:

    • Network path worked.
    • Port 8022 was reachable.
    • Donna was offering the intended key.
    • The Termux sshd server did not accept that key.

    Likely causes at that stage:

    • ~/.ssh/authorized_keys did not contain the key as one clean physical line.
    • authorized_keys was malformed due to mobile paste wrapping.
    • sshd was reading a different AuthorizedKeysFile.
    • Termux file permissions or StrictModes behavior was rejecting the file.
    • Wrong Termux user/home directory.
    • sshd config accepted pubkey auth in principle but not this file/key.

    2. Miguel inspected sshd_donna_debug.log on the phone

    The phone-side debug log reportedly showed:

      ─ text
      sshd starts normally.
      It loads Termux sshd config:
      /data/data/com.termux/files/usr/etc/ssh/sshd_config
      It enables public key auth and uses:
      /data/data/com.termux/files/home/.ssh/authorized_keys
      It binds successfully to port 8022 on:
      IPv6: ::
      IPv4: 0.0.0.0

    So at that moment:

    • Termux sshd was starting.
    • It was configured to use the expected authorized_keys.
    • It was binding on port 8022.

    But it still had not proven that the exact Donna key fingerprint was recognized/accepted.

    3. Later retry changed to “Connection refused”

    Donna retried and got:

      ─ text
      connect to address [TAILNET_IP] port 8022: Connection refused
      ssh: connect to host miguels-s24 port 8022: Connection refused

    This likely happened because sshd was previously started in debug mode with -ddd, which can exit after a single connection attempt or not     stay resident like normal daemon mode.

    So currently the immediate state may simply be:

    • Termux sshd is not running/listening anymore, or
    • It is bound differently than expected, or
    • Tailscale/MagicDNS is resolving but no process is accepting port 8022.

    ────────────────────────────────────

    Phone-side diagnostic request

    Please run these checks on the Android/Termux phone, preferably from the running phone agent or Termux shell.

    Do not print secrets. The public key is okay to inspect/fingerprint. Do not print private keys, tokens, .env files, Hermes session DBs,     memory stores, or raw logs containing secrets.

    A. Confirm identity and paths

      ─ sh
      echo "USER=$(whoami)"
      echo "HOME=$HOME"
      pwd

    Expected user is likely:

      ─ text
      u0_a369

    Expected home is likely:

      ─ text
      /data/data/com.termux/files/home

    B. Confirm sshd exists and version

      ─ sh
      command -v sshd || echo "NO_SSHD"
      sshd -V 2>&1 || true

    C. Check authorized_keys file shape and fingerprint

    Important: do not paste the private key. Only check the public authorized key file.

      ─ sh
      mkdir -p "$HOME/.ssh"
      chmod 700 "$HOME" "$HOME/.ssh"
      touch "$HOME/.ssh/authorized_keys"
      chmod 600 "$HOME/.ssh/authorized_keys"
      echo "authorized_keys path:"
      realpath "$HOME/.ssh/authorized_keys" 2>/dev/null || echo "$HOME/.ssh/authorized_keys"
      echo "authorized_keys line count:"
      wc -l "$HOME/.ssh/authorized_keys"
      echo "authorized_keys fingerprints:"
      ssh-keygen -lf "$HOME/.ssh/authorized_keys" 2>&1 || true

    We need to see whether this fingerprint appears:

      ─ text
      SHA256:Xv2Vhf3mIR+YbXtbn38cNlJIOBeH3Zb1HH9Ifqcjv0k

    If it does not appear, rebuild the file with the exact Donna public key:

      ─ sh
      mkdir -p "$HOME/.ssh"
      printf '%s\n' 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBPPs0LEC6v4GJ2HVtxbYxO07fjpd1SOtGdqyDVCcNF/ donna-to-victoria@hermes-grid' >       "$HOME/.ssh/authorized_keys"
      chmod 700 "$HOME" "$HOME/.ssh"
      chmod 600 "$HOME/.ssh/authorized_keys"
      ssh-keygen -lf "$HOME/.ssh/authorized_keys" 2>&1 || true

    Expected fingerprint should include:

      ─ text
      SHA256:Xv2Vhf3mIR+YbXtbn38cNlJIOBeH3Zb1HH9Ifqcjv0k

    D. Restart sshd in normal daemon mode

    Do not use -ddd for the normal test, because debug mode can exit after a connection.

    Use:

      ─ sh
      pkill sshd 2>/dev/null || true
      sshd \
        -o PubkeyAuthentication=yes \
        -o PasswordAuthentication=no \
        -o KbdInteractiveAuthentication=no \
        -o AuthorizedKeysFile="$HOME/.ssh/authorized_keys" \
        -o StrictModes=no \
        -p 8022
      sleep 1
      pgrep -a sshd || echo "NO_SSHD_PROCESS"

    Then check listener:

      ─ sh
      ss -ltnp 2>/dev/null | grep ':8022' || netstat -ltnp 2>/dev/null | grep ':8022' || echo "NO_8022_LISTENER"

    Expected:

      ─ text
      sshd is running
      port 8022 is listening

    E. If connection still fails, collect focused sshd debug output

    If Donna still gets Permission denied after the fingerprint is present and sshd is listening, run a one-shot debug server and capture the     relevant failure reason.

    On phone:

      ─ sh
      pkill sshd 2>/dev/null || true
      sshd \
        -D \
        -ddd \
        -E "$HOME/sshd_donna_debug.log" \
        -o PubkeyAuthentication=yes \
        -o PasswordAuthentication=no \
        -o KbdInteractiveAuthentication=no \
        -o AuthorizedKeysFile="$HOME/.ssh/authorized_keys" \
        -o StrictModes=no \
        -p 8022

    Then have Donna attempt the SSH connection once.

    After that, inspect:

      ─ sh
      grep -Ei 'authorized|key|refused|failed|accepted|authentication|bad ownership|permissions|Could not open|matching|userauth'       "$HOME/sshd_donna_debug.log" | tail -120

    Please report only the relevant lines. Redact IPs/hostnames if desired. Do not paste secrets.

    ────────────────────────────────────

    Third-party agent objective

    Please determine why Donna’s public key is not accepted by Termux sshd, or why port 8022 is not listening, and provide the smallest safe     fix.

    The desired final state is:

    1. Phone has Donna’s public key in:

      ─ text
      $HOME/.ssh/authorized_keys

    2. This command on the phone shows Donna’s fingerprint:

      ─ sh
      ssh-keygen -lf "$HOME/.ssh/authorized_keys"

    Expected fingerprint:

      ─ text
      SHA256:Xv2Vhf3mIR+YbXtbn38cNlJIOBeH3Zb1HH9Ifqcjv0k

    3. Phone has sshd running normally on port 8022.

    4. Donna can connect from VPS/cloud side using public-key auth and receives:

      ─ text
      SAM_AUTH_OK

    ────────────────────────────────────

    Safety boundaries

    Allowed:

    • Inspect whoami, $HOME, sshd config, process status, listener status.
    • Inspect/fingerprint authorized_keys.
    • Add/replace Donna’s public key in authorized_keys.
    • Restart Termux sshd.
    • Run non-destructive readiness commands like uname, command -v tmux, command -v python3.

    Not allowed unless Miguel explicitly approves:

    • Printing private keys or tokens.
    • Copying .env, Hermes sessions, memory stores, raw logs with secrets.
    • Installing packages.
    • Changing Tailscale config.
    • Opening public firewall ports.
    • Starting resident local LLMs.
    • Deleting data.
    • Exfiltrating phone files.
    • Enabling the phone as an active Studio54 grid worker before the readiness contract is complete.

────────────────────────────────────

Short version for the phone agent

You are running on the Android/Termux phone. Please make Termux sshd accept Donna’s public key over Tailscale on port 8022.

Donna’s public key must be exactly one line:

─ text
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBPPs0LEC6v4GJ2HVtxbYxO07fjpd1SOtGdqyDVCcNF/ donna-to-victoria@hermes-grid

Target fingerprint:

─ text
SHA256:Xv2Vhf3mIR+YbXtbn38cNlJIOBeH3Zb1HH9Ifqcjv0k

Safe command to apply:

─ sh
mkdir -p "$HOME/.ssh"
printf '%s\n' 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBPPs0LEC6v4GJ2HVtxbYxO07fjpd1SOtGdqyDVCcNF/ donna-to-victoria@hermes-grid' > "$HOME/.ssh/authorized_keys"
chmod 700 "$HOME" "$HOME/.ssh"
chmod 600 "$HOME/.ssh/authorized_keys"
ssh-keygen -lf "$HOME/.ssh/authorized_keys"
pkill sshd 2>/dev/null || true
sshd -o PubkeyAuthentication=yes -o PasswordAuthentication=no -o KbdInteractiveAuthentication=no -o AuthorizedKeysFile="$HOME/.ssh/authorized_keys" -o StrictModes=no -p 8022
sleep 1
pgrep -a sshd
ss -ltnp 2>/dev/null | grep ':8022' || netstat -ltnp 2>/dev/null | grep ':8022' || echo "NO_8022_LISTENER"
echo SAM_PHONE_READY_FOR_DONNA_RETRY

Then Donna should retry from VPS/cloud side.

────────────────────────────────────

That should give the other agent enough context without drowning them in our disco debugging saga.