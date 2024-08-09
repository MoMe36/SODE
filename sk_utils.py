
import pandas as pd
import glob
import os
import hashlib
import json
import re
import random
import basic_utils
from io import StringIO


def to_markdown_table(data, headers = None):
    if isinstance(data, list): 
        data_df = pd.DataFrame(data, columns = headers)
    elif isinstance(data, pd.DataFrame): 
        data_df = data
    else: 
        raise ValueError("Data must be a list or a pandas DataFrame. Currently: {}".format(type(data))) 
    result = data_df.to_markdown(index=False)
    return result


def add_node_to_graph(graph_folder = "/path/to_graph", contents = "", node_prefix = "", parent_path = None, tags = None, node_suffix = "", name_override = None, use_hash = True): 
    
    if name_override is not None: 
        fname = os.path.join(graph_folder, "{}.md".format(name_override))
    else: 
        if parent_path is None: 
            fname = "{}{}.md".format(node_prefix, "{}".format("_" + node_suffix if not node_suffix.startswith("_") else node_suffix) if node_suffix.strip() != "" else "")
        else: 
            # merging the parent name with the node name
            parent_name = get_short_hash(os.path.basename(parent_path).split('.')[0]) if use_hash else os.path.basename(parent_path).split('.')[0] 

            if node_prefix.strip() != "": 
                pre_name= node_prefix if node_prefix.endswith('_') else node_prefix + "_"
            else: 
                pre_name = ""
            if node_suffix.strip() != "":
                suf_name = node_suffix if node_suffix.startswith('_') else "_" + node_suffix
            else: 
                suf_name = ""
            fname = pre_name + parent_name + suf_name + ".md"

        fname = os.path.join(graph_folder, fname)
        # fname = "{}{}".format("_{}".format(node_prefix[:-1] if node_prefix.endswith('_') else node_prefix) if node_prefix.strip() != "" else "", os.path.basename(parent_path).replace('.md', '') if parent_path is not None else "")
        # fname = os.path.join(graph_folder, "{}{}.md".format(fname, "_{}".format(node_suffix[1:] if node_suffix.startswith('_') else node_suffix) if node_suffix.strip() != "" else ""))
        # # SOMETIMES, NAMES END UP WITH MY_NAME_.MD # QUICK FIX THAT SHOULD BE IMPROVED
        # fname = fname.replace('_.md', '.md')
    # input(fname)
    
    if tags is not None:
        if isinstance(tags, str):
            tags = [tags]
        handle_tags_representation(graph_folder, tags)
        tags_formatted = '\n#'.join([''] + tags)
    else: 
        tags_formatted = "" 

    contents = make_formatted_contents(contents)
    
    with open(fname, 'w') as f:
        f.write(contents)
    
    if parent_path is not None:
        update_parent_node_links(parent_path, fname)

    update_section(fname, 'Tags', tags_formatted)
    

    handle_graph_forces(graph_folder)
    return fname 


def get_short_hash(text, lenth = 8): 
    sha256 = hashlib.sha256()
    sha256.update(text.encode('utf-8'))
    return sha256.hexdigest()[:lenth]


def handle_tags_representation(graph_folder, tags):

    graph_reprez = json.loads(open(os.path.join(graph_folder, ".obsidian", "graph.json")).read())
    groups = graph_reprez['colorGroups']
    groups_keys = [gc['query'] for gc in groups]
    tags_not_present = []
    for tag in tags: 
        if 'tag:{}'.format(tag) not in groups_keys: 
            color = random.randint(0, 16777215)
            graph_reprez['colorGroups'].append({"query": "tag:{}".format(tag),
                                                "color": {"a": 1, 
                                                          "rgb": color}})
            # basic_utils.crprint('Added {} tag'.format(tag))
            tags_not_present.append(tag)
    with open(os.path.join(graph_folder, ".obsidian", "graph.json"), "w") as f:
        f.write(json.dumps(graph_reprez, indent=4))


    # APPENDING TO THE .obsidian/tags_description.json
    if len(tags_not_present) > 0:
        if not os.path.exists(os.path.join(graph_folder, ".obsidian", "tags_description.json")):
            init_codebase_tags(graph_folder)
        current_tags = json.loads(open(os.path.join(graph_folder, ".obsidian", "tags_description.json")).read())
        for tag in tags_not_present: 
            current_tags[tag] = ""
        with open(os.path.join(graph_folder, ".obsidian", "tags_description.json"), "w") as f:
            f.write(json.dumps(current_tags, indent=4))
        # basic_utils.crline('Missing descriptions for tags:\n{}'.format('\n'.join(tags_not_present)))


def init_codebase_tags(path): 
    # THE FILE REQUIRED FOR THE PLAN GENERATOR (TAG: DESCRIPTION OF CONTENTS) --> FOR CODEBASES AND SNAKE 
    with open(os.path.join(path, ".obsidian", "tags_description.json"), "w") as f:
        f.write(json.dumps({}, indent=4))

    # IN CASE SOME NODE ALREADY EXIST: THIS SHOULD NOT HAPPEN FROM NOW ON (IT'S A LEGACY THING, I BELIEVE)
    tags = get_existing_tags(path)
    tags_dict = {tag: "" for tag in tags}
    with open(os.path.join(path, ".obsidian", "tags_description.json"), "w") as f:
        f.write(json.dumps(tags_dict, indent=4))


def get_existing_tags(path):

    _, all_paths = collect_node_contents(path, return_paths = True) 
    tags = []
    for p in all_paths: 
        collected_tags = [t.replace('#', "") for t in get_node_section(p, 'Tags').split('\n') if t.strip() != ""]
        tags.extend(collected_tags)
    
    tags = list(set(tags))
    return tags


def collect_node_contents(graph_folder, node_regex = r'.*', target_section = None, return_paths = True, tags = None): 
    
    if isinstance(node_regex, str): 
        node_regex = re.compile(node_regex)
    # get all the files in the folder 
    files = glob.glob(os.path.join(graph_folder, "*.md"))
    # keep files that comply with the regex
    files = [f for f in files if re.match(node_regex, os.path.basename(f))]
    files = tags_filter(files, tags)
    
    # for each file, get the target contents of the node (full node if no target section is specified) 
    # collected_contents = {}
    collected_contents = []
    for file in files: 
        with open(file, "r") as f: 
            contents = f.read()
        # get the node contents 
        if target_section is not None:

            contents = get_node_section(file, target_section)

        # collected_contents[file]= contents
        collected_contents.append(contents)
    if return_paths: 
        # result = [[c, f] for c, f in zip(collected_contents, files)]  #collected_contents, files
        # input(len(result))
        # return result
        return collected_contents, files
    return collected_contents


def tags_filter(files, tags):

    if tags is  None:
        return files 
    selected_files = []
    if isinstance(tags, str): 
        tags = [tags]
    for f in files: 
        contents = get_node_section(f, 'Tags')
        # print(f, contents)
        # input(' ok?')
        if contents is None:
            continue
        for content in contents.split('\n'):    
            for t in tags: 
                if t in content: 
                    selected_files.append(f)
                    break
    return selected_files


def get_node_section(file, target_section=None, debug=False):
    contents = open(file, 'r').read()
    if target_section is None:
        if not "Desc" in get_all_sections(file):
            # get first section 
            first_section = get_all_sections(file)[0]
            return get_node_section(file, first_section[1])
            # return contents
        else: 
            target_section = "Desc"

    sections_pattern = r"(#+)\s+(.*?)\n\n"
    sections = re.findall(sections_pattern, contents)
    actual_sections = [s[0] + " " + s[1] for s in sections]

    section_level = [len(s[0]) for s in sections]
    sections_clean = [s[1].strip() for s in sections]

    if target_section not in sections_clean:
        return None  # Target section not found

    args_section = sections_clean.index(target_section)
    current_section_level = section_level[args_section]

    # Find the end of the target section by looking for the next section of equal or lesser level
    end_index = None
    for i in range(args_section + 1, len(section_level)):
        if section_level[i] <= current_section_level:
            end_index = i
            break
    

    # Extract the content of the target section
    start_content = contents.split(actual_sections[args_section])[1]
    if end_index is not None:
        end_content = actual_sections[end_index]
        contents = start_content.split(end_content)[0].strip()
    else:
        contents = start_content.strip()

    if debug:
        print(contents)  # Replace with your debug print function if necessary

    return contents


def get_all_sections(file): 

    contents = open(file, 'r').read()
    # sections = re.findall(r"(#+)\s+(.*?)\n\n", contents)
    # sections = re.findall(r"(#+)\\s+(.*?)\\n\\n", contents)
    pattern = r'# (.+?)(?:\n\n|\n$)'
    # matches = re.findall(pattern, contents, re.DOTALL)
    matches = re.finditer(pattern, contents, re.MULTILINE)
    result = [[match.group(0).split(' ')[0].strip(), match.group(1).strip()] for match in matches]

    return result


def make_formatted_contents(contents): 

    if isinstance(contents, str): 
        contents = [['Desc', contents]]
    elif isinstance(contents, dict): 
        contents = [[k, contents[k]] for k in contents.keys()]
    elif isinstance(contents, list): 
        if len(contents) == 2: 
            contents = [[contents[0], contents[1]]]
        else: 
            contents = [[c[0], c[1]] for c in contents]

    
    sections = [c[0] for c in contents]
    if 'Links' not in sections:
        contents.append(['Links', ''])
    if 'Tags' not in sections:
        contents.append(['Tags', ''])

    formatted_contents = ""
    for content in contents: 
        formatted_contents += "# {}\n\n\n{}\n\n".format(content[0], format_for_obsidian(content[1]))

    return formatted_contents


def format_for_obsidian(content):
    return format_helper_for_obsidian(content, "")


def format_helper_for_obsidian(content, indent):
        result = ""
        if isinstance(content, dict):

            for k in content.keys():
                result += "{}- {}: \n".format(indent, k)
                result += format_helper_for_obsidian(content[k], indent + "    ")
        elif isinstance(content, list):
            for item in content:
                if isinstance(item, str):
                    result += "{}- {}\n".format(indent, item)
                else:
                    result += format_helper_for_obsidian(item, indent + "    ")
        else:
            result += "{}{}\n".format(indent, content)
        return result


def update_parent_node_links(parent_path, child_path):

    basic_utils.crprint(parent_path)
    parent_links = get_node_section(parent_path, 'Links')
    parent_links = parent_links.split('\n')
    parent_links.append("[[{}]]".format(os.path.basename(child_path).split('.')[0]))
    parent_links = "\n".join(parent_links)
    update_section(parent_path, 'Links', parent_links)


def update_section(file, target_section, new_contents):
    file_contents = open(file, 'r').read()
    # input(get_all_sections(file))   
    # if target_section in sections: 
    if check_section(file, target_section):
        current = get_node_section(file, target_section)
        # print("Section {} \n {}".format(target_section, current))
        if current.strip() == "": 
            new_contents = file_contents.replace("# {}".format(target_section), "# {}\n\n{}".format(target_section, new_contents))
        else: 
            new_contents = file_contents.replace(current +"\n", new_contents + "\n") # the \n handles some edge case where the content of the target section is the same as some other part in the file (e.g: function name)
        # print('New contents: \n{}'.format(new_contents))
        with open(file, 'w') as f: 
            f.write(new_contents)
    else: 
        basic_utils.crprint('Section {} not found in node {}. \n Skipping.'.format(target_section, file))


def check_section(target_file, target_section): 
    sections = get_all_sections(target_file)
    # print('Looking for section: {} in {} '.format(target_section, sections))

    return target_section.strip() in [s[1].strip() for s in sections]


def handle_graph_forces(graph_folder):
    # input('here')
    graph_reprez = json.loads(open(os.path.join(graph_folder, ".obsidian", "graph.json")).read())
    graph_reprez['centerStrength'] = 0.25
    graph_reprez['repelStrength'] = 14.3
    graph_reprez['scale'] = 0.13

    with open(os.path.join(graph_folder, ".obsidian", "graph.json"), "w") as f:
        f.write(json.dumps(graph_reprez, indent=4))


def from_markdown_table_to_df(markdown_table): 
    lines = markdown_table.strip().split('\n')
    header = lines[0]
    rows = lines[2:]

    # Reconstruct the table without the separator line
    table = '\n'.join([header] + rows)

    # Use StringIO to read the table into a pandas DataFrame
    df = pd.read_csv(StringIO(table), sep='|', engine='python')
    # Clean up the DataFrame by stripping whitespace from column names and data
    df.columns = [col.strip() for col in df.columns]
    df = df.map(lambda x: x.strip() if isinstance(x, str) else x)
    # drop unnamed columns
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

    return df


def init_obsidian_vault(path, exists_ok = False):
    if os.path.exists(path): 
        if exists_ok: 
            basic_utils.crline('Vault already existing and exists_ok options set to True')
            return 
        # remove 
        os.system("rm -r {}".format(path))
    os.makedirs(path, exist_ok = True)
    os.makedirs(os.path.join(path, ".obsidian"), exist_ok = True)    
    init_obsidian(path)
    basic_utils.crline('Vault initialized at {} '.format(path))


def init_obsidian(path): 
    d = {"accentColor" : "", 
         "theme": "obsidian"}
    with open(os.path.join(path, ".obsidian", "appearance.json"), "w") as f:
        json.dump(d, f)
    with open(os.path.join(path, ".obsidian", "app.json"), "w") as f:
        json.dump({}, f)
    with open(os.path.join(path, ".obsidian", "graph.json"), "w") as f:
        graph_display = {
            "collapse-filter": True,
            "search": "",
            "showTags": False,
            "showAttachments": False,
            "hideUnresolved": False,
            "showOrphans": True,
            "collapse-color-groups": True,
            "colorGroups": [],
            "collapse-display": True,
            "showArrow": False,
            "textFadeMultiplier": 0,
            "nodeSizeMultiplier": 1,
            "lineSizeMultiplier": 1,
            "collapse-forces": True,
            "centerStrength": 0.518713248970312,
            "repelStrength": 10,
            "linkStrength": 1,
            "linkDistance": 250,
            "scale": 1,
            "close": True
            }
        f.write(json.dumps(graph_display, indent=4))

    # ADDING HOTKEYS 
    with open(os.path.join(path, ".obsidian", "hotkeys.json"), "w") as f:
        hotkeys = {
            "app:reload": [
                {"modifiers": ["Mod"], 
                 "key": "R"}
            ]
        }
        f.write(json.dumps(hotkeys, indent=4))

    init_codebase_tags(path)


def collect_files_in_folder(folder_path, filter_out= None, target_tags = None, priority_up_list = []):

    files = glob.glob(os.path.join(folder_path, "*.md"))
    if filter_out is not None:
        files = [f for f in files if filter_out not in f]
    if target_tags is not None:
        files = tags_filter(files, target_tags)
    return files 

