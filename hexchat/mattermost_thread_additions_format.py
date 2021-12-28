import hexchat
from collections import defaultdict
import hashlib
import re

__module_name__ = 'Mattermost Thread Format'
__module_author__ = 'kotodama'
__module_version__ = '0.0.1'
__module_description__ = 'Enhance lisibility by formatting Mattermost Threads'

mm_networks = ["MatterMost"]

ec = defaultdict(str)

# This is used to specify control characters in the script.
ec.update({
    "b": "\002",  # bold
    "c": "\003",  # color
    "h": "\010",  # italics
    "u": "\037",  # underline
    "o": "\017",  # original attributes
    "r": "\026",  # reverse color
    "e": "\007",  # beep
    "i": "\035",  # italics
    "t": "\t",    # tab
})
color_light = "00"
color_hl = "19"
color_self = "30"
color_min = 18
color_max = 30
debug_enabled = set('*')

thread_re = re.compile(r"^(([0-9]{2}:[0-9]{2}:[0-9]{2}.? )?\[([0-9a-f]{3}->)?([0-9a-f]{3})\])")
thread_re_sub = r"\2[{}\3\4{}]"
# [29a->279] blah blah blah (re @nickname: original message) (cc @nick2 @nick3))
#thread_ctx_re = re.compile(r"(\(re @[^: ]+: (.*)( \(cc( @\s)+\))?\)( \(mention .*\))?)$")
# Sometimes it gets cut
thread_ctx_re = re.compile(r"( \(re @[^: ]+: .*)$")
thread_ctx_replace = r"{}\1{}".format(ec["h"] + ec["c"] + color_light, ec["o"])
mm_thread_prefix_re = re.compile(r"^([0-9]{2}:[0-9]{2}:[0-9]{2}.? )?\[[0-9a-f]{3}(->[0-9a-f]{3})?\] ")

last_msg_context = None
last_msg_nick = None
last_msg_threadctx_formatted = False
last_msg_threadctx_closed = False

current_focus_tab = None
recursion = False


def dmsg(msg, desc="DEBUG", prefix="(nn) "):
    "Debug message -- Print 'msg' if debugging is enabled."
    if "*" in debug_enabled or desc in debug_enabled:
        omsg(msg, desc, prefix)

def omsg(msg, desc="Info", prefix="(nn) "):
    "Other message -- Print 'msg', with 'desc' in column."
    jprint(ecs("b"), str(prefix), str(desc), ecs("bt"), str(msg))

def jprint(*objects):
    hexchat.prnt("".join(objects))

def ecs(series):
    "return a series of escape codes"
    return "".join([ec[code] for code in series])

def tab_focus_callback(word, word_eol, userdata):
    global current_focus_tab
    current_focus_tab = hexchat.get_context()
    #dmsg("Focus changed to {}.".format(current_focus_tab), "GUICOLOR")
    return hexchat.EAT_NONE

def text_to_color(text):
    crange = color_max-color_min
    rand = sum(ord(i) for i in hashlib.md5(text.encode('utf-8')).hexdigest()) % (2*crange)
    color = int(color_min + rand/2)
    if color < 10:
        color = "0{}".format(color)
    else:
        color = str(color)
    #dmsg("Thread id: {} color: {}".format(text, color))
    if rand > crange:
        return (color, True)
    else:
        return (color, False)

def color_codes(text):
    (color, bold) = text_to_color(text)
    if bold:
        return ec['b'] + ec['c'] + color
    else:
        return ec['c'] + color

def is_current_tab(ctx):
    global current_focus_tab
    return is_same_context(ctx, current_focus_tab)

def is_same_context(ctx1, ctx2):
    if ctx1 is None or ctx2 is None:
        return False
    try:
        return ctx1 == ctx2
    except:
        return False

def message_callback(word, word_eol, userdata, attributes):
    global last_msg_threadctx_formatted, last_msg_threadctx_closed, last_msg_context, last_msg_nick, recursion
    last_changed = last_msg_threadctx_formatted

    if recursion:
        return hexchat.EAT_NONE

    last_msg_threadctx_formatted = False
    network = hexchat.get_info('network')
    if network is None or network not in mm_networks:
        return hexchat.EAT_NONE

    if "event" not in userdata:
        dmsg("Missing event name")
        return hexchat.EAT_NONE
    event_name = userdata["event"]

    hilight = False
    if event_name == "Channel Msg Hilight":
        reset_code = ec["o"] + ec['c'] + color_hl
        hilight = True
    elif event_name == "Your Message":
        reset_code = ec["o"] + ec['c'] + color_self
    else:
        reset_code = ec['o']

    ctx = hexchat.get_context()
    #dmsg("last formatted: {}".format(last_changed))
    if last_changed and is_same_context(ctx, last_msg_context) and last_msg_nick == word[0] and (not mm_thread_prefix_re.match(word[1]) or not last_msg_threadctx_closed):
        #dmsg("same message actually")
        if word[1][-2:] == '…)':
            #dmsg("Current message has closing parenthesis")
            last_msg_threadctx_closed = True
        word[1] = "{}{}{}".format(ec["h"] + ec["c"] + color_light, word[1], ec["o"])
    else:
        match = thread_re.match(word[1])
        if match:
            #dmsg("match: {}".format(match.groups()))
            thread_id = match.groups()[3]
            if word[1][-1] == ')':
                #dmsg("Current message has closing parenthesis")
                last_msg_threadctx_closed = True
            else:
                last_msg_threadctx_closed = False
            word[1] = thread_re.sub(thread_re_sub.format(color_codes(thread_id), reset_code), word[1], 1)
    
        (word[1], changes) = thread_ctx_re.subn(thread_ctx_replace, word[1], 1)
        if changes == 1:
            #dmsg("Setting last_msg_threadctx_formatted")
            last_msg_threadctx_formatted = True

    try:
        if not is_current_tab(ctx):
            if hilight:
                hexchat.command("gui color 3") # required since HexChat 2.12.4
            else:
                hexchat.command("gui color 2 -nooverride") # required since HexChat 2.12.4
    except:
        dmsg("Failure 2")
        return hexchat.EAT_NONE

    #dmsg("set recursion true and print")
    last_msg_context = ctx
    last_msg_nick = word[0]
    recursion = True
    ctx.emit_print(event_name, *word, time=attributes.time)
    #dmsg("set recursion false")
    recursion = False

    return hexchat.EAT_ALL

hexchat.hook_print_attrs("Channel Message", message_callback, {"event": "Channel Message"}, priority=hexchat.PRI_LOWEST)
hexchat.hook_print_attrs("Channel Msg Hilight", message_callback, {"event": "Channel Msg Hilight"}, priority=hexchat.PRI_LOWEST)
hexchat.hook_print_attrs("Your Message", message_callback, {"event": "Your Message"}, priority=hexchat.PRI_LOWEST)
#hexchat.hook_print_attrs("Channel Action", message_callback, "Channel Action", priority=hexchat.PRI_HIGHEST)
#hexchat.hook_print_attrs("Channel Action Hilight", message_callback, "Channel Action Hilight", priority=hexchat.PRI_LOW)
hexchat.hook_print("Focus Tab", tab_focus_callback, priority=hexchat.PRI_LOW)
