# SODE 

Welcome ! This is SODE's repo for Gemini API Developer Competition. In the following sections, we'll briefly introduce SODE and show you how to use it ! 
Then, if you still want to know more, there are some more details about the way it actually works ! Hope you enjoy  :heart_eyes: !! 

## What is SODE 

SODE is a system dynamics builder. As mentionned in the video describing the project, it starts from a text description (for instance, a transcription) that describes a system dynamics (e.g: deer population, economic cycles, inventory management...) and creates a structured representation and the simulation code that enables you to explore scenarios. Actually, we leverage the structured representation to also derive an interactive graph that displays all variables ( and constants and other parameters...), thus enabling users to tinker with the system dynamics without diving into the code if they would rather avoid it.

## How to install 

Ultimately, SODE will be platform agnostic. Nevertheless, for the time being, the installation / usage pipeline have only been developped / tested on **ubuntu**. To install: 

1. Clone this repo  
2. Ensure you have [anaconda 3 available](https://docs.anaconda.com/anaconda/install/linux/) 
3. `base path/to/the/repo/folder/sode_installer.sh`: the installation script will:
    * Create a conda env named `sode_env`
    * Install the necessary dependencies
    * Download Obsidian (which we currently rely on for graph vizualisation)
    * Ask you for your Gemini key, which will be saved in `~/.gemini.txt` 
    * And finally, put `sode_cli.sh` in the ~/.local/bin folder for easy access 


## How to use 

SODE's main goal is to lower the entry barrier to system dynamics. In this context, only a few commands are needed to control all features: 

### Build 

Command: `sode_cli.sh build --d path/to/your/system_desc.txt`
This will initialize the system, deriving the structure and producing the code from this first pass. It also creates a config file (including the path to the system description, for the structure file, the code...). The `deers.txt` file is provided as an example. 

### Check 

Command: `sode_cli.sh check`
Leverages previous results accessed via the configuration file. In this stage, SODE runs several checks, including whether all variables are used in the code. In some cases, SODE will leverage Gemini's implicit knowledge to provide change suggestions. If the checks are satisfied, a triumphant message will appear on screen, informing the user that the system is ready for simulation. 
Otherwise, the configuration file will be populated with the errors, limitations, uncertainties or user-refused suggestions, showing a way to improve system definition.  

Assuming success in defining the system, the associated interactive graph will also be available. Simply open the interactive_graph folder (default name) with Obsidian. From there, you can change the parameter values and use `sode_cli.sh update_from_graph` command to propagate those changes to both the structure and the code ! Make sure you respect the syntax: the intuitive and minimalist interface wouldn't support otherwise :sweat_smile: 


### Run 

Command: `sode_cli.sh run`
Pretty much self-explanatory: will run the produced simulation code, showing you a matplotlib plot with the monitored target stock(s). 

### Colab 

Command `sode_cli.sh colab`
While we encourage user exploration and system parameters tinkering, we know sometimes inspration can be scarce. In those cases, SODE offers a colaborative interface, in which the user can provide an observation/analysis of the systems dynamics (e.g: deer population explodes !) and SODE will, leveraging Gemini wide knowledge, offer grounded strategies to change this behavior. Concretely, SODE will present the user with three options and implement the changes from the selected course of action.  

### Additional commands 

* `sode_cli.sh reset` : resets the configuration 
* `sode_cli.sh current_config `: prints the configuration on screen 

## Perspectives

There are many systems to be built, we just usually lack the culture to do so. SODE brings this expertise closer to everyone, with chances to improve rationality, efficiency, long-term evaluation and comparison of policies across the board, potentially contributing to help mankind face many complex challenges through the dissemination of quality knowledge.    

We have a strong belief in SODE's potential. In the short term, regardless of the competition's outcome, we plan to enhance the system by enabling it, for instance, to build subsystems that can be combined into larger architectures. This approach offers an attractive balance between control, transparency, and ease of design/build. Furthermore, beyond its immediate applications, we envision SODE's knowledge structure—its recursive method of building systems to satisfy constraints through efficient hybrid techniques—as a promising way to leverage the new capabilities introduced by large language models (LLMs) in real-world, valuable use cases.

## How it works 

As suggested above, we initialize the system by identifying *boundary* conditions such as the time horizon, constants, and target stocks. Those can consequently be inserted in the simulation function code. Once the basics are established, we recursively build the system from the ground up. Specifically, we perform a deterministic code analysis to ensure all variables present in the code are defined. If any variables are undefined, SODE intelligently parses the system description to identify how to incorporate these variables. It suggests relationships between target variables and others, whether through functions or other means. This process is repeated until all variables are defined, ultimately reaching the constants identified initially.

The generated code is derived from an intermediate structured representation, which also enables us to build the interactive graph. This structured representation is crucial during the **colab** stage, as it allows the model to make precise and efficient changes to the system parameters.


## Some limitations 

While SODE offers a powerful and intuitive way to build and simulate system dynamics, there are some limitations and areas for improvement that users should be aware of:

* **Specialized Functions**: Currently, SODE may lack support for some specialized functions, (currently available functions include `piecewise_linear`, `step_after_time`, `conditional` and a more dubious `smooth`), which can be crucial for accurately modeling certain systems. We are actively working on expanding the library of supported functions to cover a broader range of use cases.

* **System Completeness**: If the system description is incomplete or too vague, the `check` stage will yield alerts that prevent the simulation from running. These alerts are designed to guide users in refining their system descriptions. SODE can help but it won't imagine the system for you. 

* **Collaborative interface** The `colab` command is designed as a proof of concept and while it enables the user to rely on the model for low-level changes, some elements (model memory, hierarchical study of the model, vision...) could potentially make the assistant more powerful 


