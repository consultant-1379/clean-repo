# Contributing to description

This document describes how to contribute to the description Project.

## How to submit a feature request
Contact the PO mentioned in the [README.md]  
Please provide a feature description and why this should be added to this service. Also, please describe the definition of done (DoD) criteria.

## Gerrit Project Details  
description artifacts are stored in the Gerrit project: [OSS/com.ericsson.oss.ci.test/clean-repo](https://gerrit.ericsson.se/#/admin/projects/OSS/com.ericsson.oss.ci.test/clean-repo)
  
### Documents

The documentation for this service is located in the [doc folder](https://gerrit.ericsson.se/plugins/gitiles/OSS/com.ericsson.oss.ci.test/clean-repo/+/master/doc).

To update documents that are not in the referenced folder, contact the service guardians mentioned in the [README.md](https://gerrit.ericsson.se/plugins/gitiles/OSS/com.ericsson.oss.ci.test/clean-repo/+/master/README.md).

## Contact Information
Contact the PO mentioned in the [README.md]


## Contribution Workflow
1. The **contributor** updates the artifact in the local repository.
2. The **contributor** pushes the update to Gerrit for review, including a reference to the JIRA.
3. The **contributor** invites the **service guardians** (mandatory) and **other relevant parties** (optional) to the Gerrit review, and makes no further changes to the document until it is reviewed.
4. The **service guardians** review the document and give a code-review score.
The code-review scores and corresponding workflow activities are as follows:
    - Score is +1
        A **reviewer** is happy with the changes but approval is required from another reviewer.
    - Score is +2
        The **service guardian** accepts the change and merges the code to master branch. The Publish pipeline is initiated to make the change available to consumers.
    - Score is -1 or -2
        The **contributor** follows-up on reviewer comments, until changes approved by service guardian.
    - The **service guardian** and the **contributor** align to determine when and how the change is published.

   [README.md] (https://gerrit.ericsson.se/plugins/gitiles/OSS/com.ericsson.oss.ci.test/clean-repo/+/master/README.md)