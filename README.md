# matterircd-utils

Just a few helper files / scripts for running matterircd

## Systemd service

You can place [matterircd.service file](systemd/matterircd.service) in your `/etc/system/systemd` directory.
Don't forget to adapt the path to matterircd binary though.

## Hexchat addons

### Nickname completion

In order to have Mattermost style nickname completion, download [mattermost_completion.pl](hexchat/mattermost_completion.pl) into `~/.config/hexchat/addons`.

Be sure to adapt `%alt_complete_networks` to match your Matterircd network name and then load it in hexchat:
```
/load ~/.config/hexchat/addons/mattermost_completion.pl
```

### Thread formatting

For better readability and identification of threads, download [mattermost_thread_additions_format.py](hexchat/mattermost_thread_additions_format.py) into `~/.config/hexchat/addons`.

This script will colorize thread IDs (using hexchat colors 18-30 and bold) and will also reduce visibility of Mattermost thread context (re: ...) and following text (see `color_light` variable). If you have changed default colors (eg. for hilight, messages from self, ...) feel free to adapt color values. It should be able to handle thread context spread over multiple lines but I recommend setting `ShortenRepliesTo` to something like 20 or so, for readability in `matterircd.toml`.

Be sure to adapt `mm_networks` to match your Matterircd network name and then load it in hexchat:
```
/load ~/.config/hexchat/addons/mattermost_thread_additions_format.py
```

Formatting is compatible with BIP IRC Proxy backlog timestamp prefix.

## Using matterircd behind BIP IRC Proxy

Matterircd backlog might be lacking a bit sometimes, or not include all missed chats. Also, you might want to stay logged in and just connect and chat, from whereever you are. Using BIP can help with this.

Simply install BIP package (on Debian and Ubuntu) or from [source](https://projects.duckcorp.org/projects/bip), then generate `/etc/bip/tls/dh.pem` and `/etc/bip/tls/bip.pem` files.
```
sudo apt install bip
sudo openssl dhparam -out /etc/bip/tls/dh.pem 2048
sudo openssl req -newkey rsa:4096 -x509 -sha256 -days 365 -nodes -out /etc/bip/tls/bip.pem -keyout /etc/bip/tls/bip.pem
```

You'll need to run `bipmkpw` and adapt [bip.conf](bip/bip.conf) with it and your Mattermost token.

### Backlog behavior

With [bip.conf](bip/bip.conf) setup, BIP connects to your local matterircd and replays backlog until last spoken on each channel/DM (independent reset). You can then reset backlog manually with `/bip blreset`.

Alternatively, you could also set `backlog_reset_connection = true` to have BIP reset backlog as a whole when you speak in any channel/DM.
