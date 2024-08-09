.. _data_copilot_fin:

=====================
Finance Data Copilot
=====================


**🤖 Automated Quantitative Trading & Factors Extraction from Financial Reports**
---------------------------------------------------------------------------------

📖 Background
~~~~~~~~~~~~~~
**Research reports** are treasure troves of insights, often unveiling potential **factors** that can drive successful quantitative trading strategies. 
Yet, with the sheer volume of reports available, extracting the most valuable insights efficiently becomes a daunting task.

Furthermore, rather than hastily replicating factors from a report, it's essential to delve into the underlying logic of their construction. 
Does the factor capture the essential market dynamics? How unique is it compared to the factors already in your library?

Therefore, there is an urgent need for a systematic approach to design a framework that can effectively manage this process. 
And this is where the **Finance Data Copilot** steps in.


🎥 Demo
~~~~~~~~~~
TODO: Here should put a video of the demo.


🌟 Introduction
~~~~~~~~~~~~~~~~
In this scenario, RDAgent demonstrates the process of extracting factors from financial research reports, implementing these factors, and analyzing their performance through Qlib backtesting. 
This process continually expands and refines the factor library.

Here's an enhanced outline of the steps:

**Step 1 : Hypothesis Generation 🔍**

- Generate and propose initial hypotheses based on insights from financial reports with thorough reasoning and financial justification.

**Step 2 : Factor Creation ✨**

- Based on the hypothesis and financial reports, divide the tasks. 
- Each task involves developing, defining, and implementing a new financial factor, including its name, description, formulation, and variables.

**Step 3 : Factor Implementation 👨‍💻**

- Implement the factor code based on the description, evolving it as a developer would.
- Quantitatively validate the newly created factors.

**Step 4 : Backtesting with Qlib 📉**

- Integrate the full dataset into the factor implementation code and prepare the factor library.
- Conduct backtesting using the Alpha158 plus newly developed factors and LGBModel in Qlib to evaluate the new factors' effectiveness and performance.

+----------------+------------+----------------+----------------------------------------------------+
| Dataset        | Model      | Factors        | Data Split                                         |
+================+============+================+====================================================+
| CSI300         | LGBModel   | Alpha158 Plus  | +-----------+--------------------------+           |
|                |            |                | | Train     | 2008-01-01 to 2014-12-31 |           |
|                |            |                | +-----------+--------------------------+           |
|                |            |                | | Valid     | 2015-01-01 to 2016-12-31 |           |
|                |            |                | +-----------+--------------------------+           |
|                |            |                | | Test      | 2017-01-01 to 2020-08-01 |           |
|                |            |                | +-----------+--------------------------+           |
+----------------+------------+----------------+----------------------------------------------------+

**Step 5 : Feedback Analysis 🔍**

- Analyze backtest results to assess performance.
- Incorporate feedback to refine hypotheses and improve the model.

**Step 6 :Hypothesis Refinement ♻️**

- Refine hypotheses based on feedback from backtesting.
- Repeat the process to continuously improve the model.

⚡ Quick Start
~~~~~~~~~~~~~~~~~

You can try our demo by running the following command:

- 🐍 Create a Conda Environment
    - Create a new conda environment with Python (3.10 and 3.11 are well tested in our CI):
    
      .. code-block:: sh
      
          conda create -n rdagent python=3.10

    - Activate the environment:

      .. code-block:: sh

          conda activate rdagent

- 📦 Install the RDAgent
    - You can directly install the RDAgent package from PyPI:

      .. code-block:: sh

          pip install rdagent

- ⚙️ Environment Configuration
    - Place the `.env` file in the same directory as the `.env.example` file.
        - The `.env.example` file contains the environment variables required for users using the OpenAI API (Please note that `.env.example` is an example file. `.env` is the one that will be finally used.)
    
    - If you want to change the default environment variables, you can refer to `Env Config`_ below

- 🚀 Run the Application
    - Store the factors you want to extract from the financial reports in your desired folder. Then, save the paths of the reports in the `report_result_json_file_path`. The format should be as follows:

      .. code-block:: json

          [
              "git_ignore_folder/report/fin_report1.pdf",
              "git_ignore_folder/report/fin_report2.pdf",
              "git_ignore_folder/report/fin_report3.pdf"
          ]

    - Run the application using the following command:
    
      .. code-block:: sh

          rdagent fin_factor_report

🛠️ Usage of modules
~~~~~~~~~~~~~~~~~~~~~

.. _Env Config: 

- **Env Config**

The following environment variables can be set in the `.env` file to customize the application's behavior:

.. autopydantic_settings:: rdagent.app.qlib_rd_loop.conf.FactorFromReportPropSetting
    :settings-show-field-summary: False
    :show-inheritance:
    :exclude-members: Config

.. autopydantic_settings:: rdagent.components.coder.factor_coder.config.FactorImplementSettings
    :settings-show-field-summary: False
    :members: coder_use_cache, data_folder, data_folder_debug, cache_location, enable_execution_cache, file_based_execution_timeout, select_method, select_threshold, max_loop, knowledge_base_path, new_knowledge_base_path
    :exclude-members: Config, python_bin, fail_task_trial_limit, v1_query_former_trace_limit, v1_query_similar_success_limit, v2_query_component_limit, v2_query_error_limit, v2_query_former_trace_limit, v2_error_summary, v2_knowledge_sampler
    :no-index: