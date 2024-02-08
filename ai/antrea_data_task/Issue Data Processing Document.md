# Antrea Issue Data Processing Document

## Introduction

This document introduces how to process the Issue data from the Antrea project into a standardized format suitable for
training. Before processing the data, it is necessary to install the corresponding Python libraries. Please run the
following command in the Conda environment.

```plain
pip install -r requirements.txt
```

## How to use ？

### Steps 1 : Download Issue data

First of all, you need to change to the working directory of **github_issue_handling** in antrea after cloning the
repository:

```plain
cd ./antrea/ai/antrea_data_task
```

You need to obtain an OAuth2 token, which can increase the amount of ISSUE data downloaded from public repositories. You
need to create a new token in the "Developer settings" -> "Personal access tokens" -> "Generate new token" section of
your GitHub account settings.
When you create a token, you need to select the permissions for this token. To read issues from public repositories, you
need the "public_repo" permission.

When you run this command locally, you may encounter issues such as network interruptions that cause the program to
stop. Don't worry, just re-run the command. The program will download data from the point of interruption, rather than
downloading data from the beginning.

```plain
python issue_clawer.py --github-token 'OAuth2 token'
```

Although the data download program has taken steps to avoid downloading duplicate data, to ensure that the downloaded
data does not duplicate, please run the following command.

```plain
python issue_filter.py
```

### Steps 2 : Process Issue data and generate training data.

Firstly, this step mainly processes the original Issue data into a standardized format, making the data more
understandable. The issue_label_train_datasets.py file mainly generates the training data set. To enhance the
flexibility for users to generate any training data set, this script provides four parameters.

+ 1.**--assign-labels** :  This represents specifying the 'label' names, creating data that only includes the
  specified 'label' names.
  Below is an example of generating a training dataset that only contains 'bug' and 'api' labels.
   ```plain
   python issue_label_train_datasets.py --assign-labels bug api
   ```
+ 2.**--add-labels** : It indicates adding additional 'label' names, requiring the specification of the label mapping
  relationship. And generate training data containing the specified 'label'. The following execution command is a
  reference example.
   ```plain
   python issue_label_train_datasets.py --add-labels "{'triage/duplicate': 'xx',}"
   ```
+ 3.**--body-prompt** : It indicates whether there is a need to use Chatgpt to briefly summarize the 'body' part of the
  Issue, with optional parameters ['body_prompt_1','body_prompt_2','body_prompt_3']. An API Key for Chatgpt needs to be
  applied for on the [OpenAI](https://openai.com/) official website. The following execution command is a reference
  example.
   ```plain
   python issue_label_train_datasets.py 'other parameter' --body-prompt body_prompt_3 --openai-key 'you openai key'
   ```

The final generated training dataset file name is: **issue_train_datasets.json**, and the file name of the dataset
without labels is: **issue_datasets_no_label.json**.

### Steps 3 : Use the fine-tuned Chatgpt model to generate labels for unlabeled data.

Use the training data from Step 2 to fine-tune the Chatgpt model, and then use the fine-tuned model to generate labels
for unlabeled data. For information on how to fine-tune Chatgpt, please refer to
the [documentation](https://github.com/zgy0817/antrea/blob/ai/ai/docs/GPT%20Online%20Model%20Fine-tuning%20Documentation.md).

After obtaining the fine-tuned model, execute the following command to generate the validation dataset.

```plain
python issue_label_evaluate_datasets.py --openai-key 'You openai key' --job-id 'The job ID of the model after ChatGPT training has been completed.'
```

The final generated validation dataset file name is: **issue_evaluate_datasets.json**

## Regarding the generation of QA pairs from documents
The script for generating QA pairs from the document is doc_generate_qa.py. The --docs-dir argument specifies the path to the folder containing the documents.

Document is segmented to generate detailed QA pairs:
```plain
python doc_genratre_qa.py --docs-dir 'path to the document's folder' --openai-key 'openai key' --mode all
```
The document is segmented and questions are generated using headings:
```plain
python doc_genratre_qa.py --docs-dir 'path to the document's folder' --openai-key 'openai key' --mode title
```

## Summary of conversation data regarding the Issue
Upstream Data Summary:
```plain
python issue_summary_dataset.py --OAuth2-token 'Personal GitHub Access Token: Please refer to step 1.' --openai-key 'openai key' --data-type public --public-data-dir issue.json --use-model-type GPT
```