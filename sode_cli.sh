#!/bin/bash 


add_arg() {
    command="$1"
    arg_name="$2"
    arg_value="$3"
    if [ -n "$arg_value" ] && [ $arg_value != "None" ]; then
        command="$command, $arg_name=\"$arg_value\""
    fi

    echo "$command"
}

make_command(){
    func_to_call="$1"
    local_fp="$2"
    sys_desc="$3"
    struct_file="$4"
    target_code="$5"
    func_config="$6"
    interactive_graph="$7"
    command="python -c 'import sode_main; sode_main.$func_to_call(\"$local_fp\""
    
    if [ $func_to_call = "initial_build" ]; then
        if [ -e "$sys_desc" ]; then
            command="$command, system_description_path=\"$sys_desc\""
        fi
    else
        command=$(add_arg "$command" "system_description_path" "$sys_desc")
    fi 
    # command=$(add_arg "$command" "system_description_path" "$sys_desc")
    command=$(add_arg "$command" "structure_file_path" "$struct_file")
    command=$(add_arg "$command" "target_code_file" "$target_code")
    command=$(add_arg "$command" "function_config_file" "$func_config")
    command=$(add_arg "$command" "interactive_graph_folder" "$interactive_graph")
    command="$command)'"
    echo $command
}



# SODE CLI


local_file_path=$(dirname $0)/sode_config.json

if [ "$1" = "reset" ]; then 
    rm $local_file_path
    echo "Removed the local configuration file"
fi
if [ ! -e $local_file_path ]; then 
    # python -c "import sys; sys.path.append('/home/mehdimounsif/Codes/SystemDyn/'); import workflow; workflow.init_config_file('$local_file_path')"
    python -c "import sode_main; sode_main.init_config_file('$local_file_path')"
    echo "Created a local configuration file"
fi 

if [ "$1" = "current_config" ]; then 
    python -c "import json; c = json.load(open('$local_file_path')); print('===== SODE CONFIG =====\n'+  json.dumps(c, indent=4));"
fi

if [ "$1" = "build" ]; then 
    system_description_path=None
    structure_file_path=None
    target_code_file=None
    function_config_file=None
    
    while [ $# -gt 1 ]; do 
        case $1 in 
            --d) 
                system_description_path="$2"
                shift 2
                ;;
            --s) 
                structure_file_path="$2"
                shift 2
                ;;
            --c) 
                target_code_file="$2"
                shift 2
                ;;
            --f) 
                function_config_file="$2"
                shift 2
                ;;
            *) 
                shift 1
                ;;
        esac 
    done

    command=$(make_command "initial_build" $local_file_path $system_description_path $structure_file_path $target_code_file $function_config_file)
    # python -c "import sode_main; print(sode_main.__file__)"
    # echo "helloooooo $command"
    eval $command
fi 

if [ "$1" = "check" ]; then 
    system_description_path=None
    structure_file_path=None
    target_code_file=None
    function_config_file=None
    
    while [ $# -gt 1 ]; do 
        case $1 in 
            --d) 
                system_description_path="$2"
                shift 2
                ;;
            --s) 
                structure_file_path="$2"
                shift 2
                ;;
            --c) 
                target_code_file="$2"
                shift 2
                ;;
            --f) 
                function_config_file="$2"
                shift 2
                ;;
            *) 
                shift 1
                ;;
        esac 
    done

    command=$(make_command "system_check" $local_file_path $system_description_path $structure_file_path $target_code_file $function_config_file)
   
    eval $command
fi 

if [ "$1" = "run" ]; then 
    structure_file_path=None
    target_code_file=None
    function_config_file=None
    
    while [ $# -gt 1 ]; do 
        case $1 in 
            --s) 
                structure_file_path="$2"
                shift 2
                ;;
            --c) 
                target_code_file="$2"
                shift 2
                ;;
            --f) 
                function_config_file="$2"
                shift 2
                ;;
            *) 
                shift 1
                ;;
        esac 
    done

    command=$(make_command "run_sim" $local_file_path None $structure_file_path $target_code_file $function_config_file)
    eval $command
fi

if [ "$1" = "update_from_graph" ]; then 

    structure_file_path=None
    interactive_graph_folder=None
    function_config_file=None

    while [ $# -gt 1 ]; do 
        case $1 in 
            --s) 
                structure_file_path="$2"
                shift 2
                ;;
            --g) 
                interactive_graph_folder="$2"
                shift 2
                ;;
            --f) 
                function_config_file="$2"
                shift 2
                ;;
            *) 
                shift 1
                ;;
        esac 
    done

    command=$(make_command "propagate_graph_changes" $local_file_path None $structure_file_path None $function_config_file $interactive_graph_folder)
    eval $command
    # echo $command
fi 

if [ "$1" = "colab" ]; then 

    command=$(make_command "colab_loop" $local_file_path None None None None None)
    eval $command

fi 


    