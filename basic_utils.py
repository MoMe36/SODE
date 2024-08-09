
import datetime
import numpy as np
import sys
import subprocess
import pandas as pd
import threading
import json
import re
import os
import random
import time
import google.generativeai as gemini



def spinner():
    # ANSI escape codes for colors
    colors = [
    '\033[91m',  # Red
    '\033[92m',  # Green
    '\033[93m',  # Yellow
    '\033[94m',  # Blue
    '\033[95m',  # Purple
    '\033[96m',  # Cyan
    ]
    # Reset color to default
    reset_color = '\033[0m'
    
    
    spin_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    spin_chars = "⠁,⠁,⠉,⠙,⠚,⠒,⠂,⠂,⠒,⠲,⠴,⠤,⠄,⠄,⠤,⠠,⠠,⠤,⠦,⠖,⠒,⠐,⠐,⠒,⠓,⠋,⠉,⠈,⠈".split(',')
    # spin_chars = "◰ ◳ ◲ ◱".split(' ')
    offset = 15
    while True:
        for i in range(len(spin_chars)):
            color = random.choice(colors)
            chars = " ".join([spin_chars[(i+j+2)%len(spin_chars)] for j in range(offset)])
            sys.stdout.write('\r' + color + chars + reset_color)
            
            sys.stdout.flush()
            time.sleep(0.03)
        if not spinner_active:
            break
    sys.stdout.write('\r ')


def crprint(text, end='\n'): 
    cprint(text, np.random.randint(60, 255, 3).tolist(), end=end) 


def cprint(text, color_list, end='\n'): 
    print_rgb_text(color_list[0], color_list[1], color_list[2], text, end=end)


def print_rgb_text(r, g, b, text, end='\n'):
    """
    Print text in a custom color specified by RGB values.
    """
    # ANSI escape code for 24-bit color
    escape_code = f"\x1b[38;2;{r};{g};{b}m"
    reset_code = "\x1b[0m"  # ANSI code to reset to default color
    print(f"{escape_code}{text}{reset_code}", end=end)


def uinput(query):

    # USE ! TO RUN A COMMAND AND ADDITIONAL ! TO ADD TEXT 
    crline(query + " >>> ", end = ' ')
    result = input()
    if result.startswith("!"): 
        command = result.split('!')[1]
        additional = "\n".join(result.split('!')[2:])
        out = subprocess.run(command, shell=True, capture_output=True).stdout.decode('utf-8')
        return out + "\n" + additional
    return result


def crline(text, end = '\n'):
    if text is None: 
        return
    """
    Print each character in the text with a different color.
    """
    c0 = np.random.randint(70, 255, (2,3))

    colors = np.linspace(c0[0], c0[1], len(text)).astype(int)
    
    # colors = np.random.randint(80, 255, (len(text), 3)).tolist()
    for i, char in enumerate(text):
        escape_code = f"\x1b[38;2;{colors[i][0]};{colors[i][1]};{colors[i][2]}m"
        reset_code = "\x1b[0m"  # ANSI code to reset to default color
        print(f"{escape_code}{char}{reset_code}", end='')
    print(end=end)


def load_icl(frame): 
    calling_func_name = frame.f_code.co_name
    file_name = frame.f_code.co_filename
    icl_path = os.path.join(os.path.dirname(file_name), '.{}_icl.txt'.format(calling_func_name))
    if not os.path.exists(icl_path): 
        crline('Missing ICL for {} - Creating empty file.'.format(calling_func_name))
        with open(icl_path, 'w') as file: 
            file.write('')
    contents = open(icl_path, 'r').read()
    return contents


def safe_gemini_ask(messages, model = 'pro'):   

    model_dict = {"pro": "gemini-1.5-pro",
                    "flash": "gemini-1.5-flash"}
    answer = direct_gemini_ask(messages, model_dict[model])
    json_parseable = False
    try: 
        cleaned_answer = parse_json(answer)
        json_parseable = True
    except:
        cleaned_answer = None
    return answer, json_parseable, cleaned_answer


def direct_gemini_ask(messages, model = 'pro'):

    global spinner_active 
    

    spinner_active = True
    thread = threading.Thread(target=spinner)
    thread.start()

    start = time.time()
        
    model_answer, infos = gemini_ask(messages, model)
    duration = time.time() - start
    call_recap = {"time": [datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')],
                "in_tokens": [infos['in_tokens']],
                "out_tokens": [infos['out_tokens']],
                "duration": [duration], 
                "model": [model]}
    
    # logging infos 
    call_recap_to_file(call_recap)

    spinner_active = False
    thread.join()
    if time.time() - start > 15: 
        play_sound_in_thread() # Reminder to check the output
    max_spacing = 30
    to_print = [["Model", f"{model.upper()}"], 
                ["Input tokens", f"{infos['in_tokens']}"], 
                ["Output tokens", f"{infos['out_tokens']}"],
                ["Gen time", "{:.2f}".format(duration)],
                ["Tokens/sec","{:.2f}".format(infos['out_tokens']/duration)]]
    to_print_formatted = "\n".join([""] + ["{} {} {}".format(p[0], '.'*(max_spacing - (len(p[0]) + len(p[1]))), p[1]) for p in to_print] + [""])

    cprint(to_print_formatted, [120,120,120])

    return model_answer # completion.choices[0].message.content


def gemini_ask(messages, model_name):

    api_key= open(os.path.join(os.path.expanduser('~'), '.gemini.txt')).read().strip()
    gemini.configure(api_key = api_key)
    model = gemini.GenerativeModel(model_name)

    first_msg = "SYSTEM PROMPT\n{}\n\n{}\n\nQuery:\n {}".format(messages[0]['content'], "="*15, messages[1]['content'])
    formatted_messages = [m for m in messages[1:]]
    formatted_messages[0]['content'] = first_msg
        

    gemini_messages = []
    for message in formatted_messages: 
        gemini_messages.append({k.replace('content', 'parts') : v.replace('assistant', "model") if k == "role" else v for k, v in message.items()})

    response = model.generate_content(gemini_messages, 
                                    generation_config=gemini.types.GenerationConfig(
                                    # Only one candidate for now.
                                    candidate_count=1,
                                    # stop_sequences=['x'],
                                    max_output_tokens=4096,
                                    temperature=0.)
    )

    out = response.candidates[0].content.parts[-1].text
    call_recap = {"in_tokens": model.count_tokens([m['parts'] for m in gemini_messages]).total_tokens, 
                    "out_tokens": model.count_tokens([out]).total_tokens, 
            }
    return out, call_recap


def call_recap_to_file(infos, target_file = os.path.join(os.path.expanduser('~'), 'model_usage.csv')):
    df_infos = pd.DataFrame(infos)
    if os.path.exists(target_file): 
        df_infos = pd.concat([(pd.read_csv(target_file)), df_infos])        
    df_infos.to_csv(target_file, index = False)


def play_sound_in_thread():
    def play_sound():
        if os.path.exists(os.path.join(os.path.expanduser('~'), ".computation_concluded.mp3")):
            playsound(os.path.join(os.path.expanduser('~'), ".computation_concluded.mp3"))
    sound_thread = threading.Thread(target=play_sound)
    sound_thread.start()


def parse_json(out_from_model): 
    
    # crprint(out_from_model)
    
    if isinstance(out_from_model, dict):
        return out_from_model
    if '```json' not in out_from_model: 
        if '```' in out_from_model: 
            
            out_from_model = out_from_model.split('```')[1].split('```')[0]
            # crprint('From path A:\n {}'.format(out_from_model))
        else: 
            # check if there is stuff around the potential json 
            before_json = out_from_model.split('{')[0].strip()
            after_json = out_from_model.split('}')[-1].strip()

            if len(before_json) > 0: 
                out_from_model = out_from_model.replace(before_json, '')
                # print('removing before json')
            if len(after_json) > 0:
                out_from_model = out_from_model.replace(after_json, '')
                # print('removing after json')
            out_from_model = out_from_model.strip()
            # crprint(out_from_model)
            # out_from_model = "```json\n" + out_from_model + "\n```"
            # crprint('From path B:\n {}'.format(out_from_model))
        if "{{" in out_from_model:
            out_from_model = out_from_model.replace('{{', '{').replace('}}', '}')
            if '```json' in out_from_model:
                out_from_model = out_from_model.split('```json')[1].split('```')[0]
            # crprint('From path C:\n {}'.format(out_from_model))
    else: 
        out_from_model = out_from_model.split('```json')[1].split('```')[0]
        # crprint('From path D:\n {}'.format(out_from_model))
    # remove comments and keep line break 
    out_from_model = re.sub(r'//.*', '', out_from_model)
    # crprint('Before parsing:\n {}'.format(out_from_model))
    return json.loads(out_from_model)

