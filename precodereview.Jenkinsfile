#!/usr/bin/env groovy

def bob = "./bob/bob -r ci/common_ruleset2.0.yaml"

def Boolean FOSS_CHANGED = true
def LOCKABLE_RESOURCE_LABEL = "kaas"
def String job_type = ""
def String pr_type = ""
@Library('oss-common-pipeline-lib@dVersion-2.0.0-hybrid') _   // Shared library from the OSS/com.ericsson.oss.ci/oss-common-ci-utils

pipeline {
    agent { label env.NODE_LABEL }

    options {
        timestamps()
        timeout(time: 60, unit: 'MINUTES')
    }

    environment {
        KUBECONFIG = "${WORKSPACE}/.kube/config"
        MAVEN_CLI_OPTS = "-Duser.home=${env.HOME} -B -s ${env.WORKSPACE}/settings.xml"
        OPEN_API_SPEC_DIRECTORY = "src/main/resources/v1"
    }

    stages {
        stage('Prepare') {
            steps {
                deleteDir()
                script {
                    ci_pipeline_init.clone_project("pcr")
                    ci_pipeline_init.clone_ci_repo("common")
                    ci_pipeline_init.setEnvironmentVariables()
                    ci_pipeline_init.setBuildName()
                    ci_pipeline_init.updateJava17Builder("common")
                }
                sh "${bob} --help"
                sh "${bob} -lq"
                echo 'Inject settings.xml into workspace:'
                configFileProvider([configFile(fileId: "${env.SETTINGS_CONFIG_FILE_NAME}", targetLocation: "${env.WORKSPACE}")]) {}

                sh "${bob} clean"
                ci_load_custom_stages ("stage-marker-prepare")
            }
        }

        stage('Init') {
            steps {
                sh "${bob} init-precodereview"
                ci_load_custom_stages ("stage-marker-init")
            }
        }

        stage('Lint') {
            when {
                expression { env.LINT_ENABLED == "true" }
            }
            steps {
                parallel(
                    "lint markdown": {
                        sh "${bob} lint:markdownlint lint:vale"
                    },
                    "lint helm": {
                        sh "${bob} lint:helm"
                    },
                    "lint helm design rule checker": {
                        sh "${bob} lint:helm-chart-check"
                    },
                    "lint code": {
                        sh "${bob} lint:license-check"
                    },
                    "lint OpenAPI spec": {
                        sh "${bob} lint:oas-bth-linter"
                    },
                    "lint metrics": {
                        sh "${bob} lint:metrics-check"
                    },
                    "SDK Validation": {
                        script {
                            if (env.validateSdk == "true") {
                                sh "${bob} validate-sdk"
                            }
                        }
                    }
                )
            }
            post {
                always {
                    archiveArtifacts allowEmptyArchive: true, artifacts: '**/*bth-linter-output.html, **/design-rule-check-report.*'
                }
            }
        }

        stage('Generate') {
            when {
                expression { env.GENERATE_ENABLED == "true" }
            }
            steps {
                parallel(
                    "Open API Spec": {
                        sh "${bob} rest-2-html:check-has-open-api-been-modified"
                        script {
                            def val = readFile '.bob/var.has-openapi-spec-been-modified'
                            if (val.trim().equals("true")) {
                                sh "${bob} rest-2-html:zip-open-api-doc"
                                sh "${bob} rest-2-html:generate-html-output-files"
                                
                                manager.addInfoBadge("OpenAPI spec has changed. Review the Archived HTML Output files: rest2html*.zip")
                                archiveArtifacts allowEmptyArchive: true, artifacts: "rest_conversion_log.txt, rest2html*.zip"
                                echo "Sending email to CPI document reviewers distribution list: ${env.EMAIL}"
                                try {
                                    mail to: "${env.EMAIL}",
                                            from: "${env.GERRIT_PATCHSET_UPLOADER_EMAIL}",
                                            cc: "${env.GERRIT_PATCHSET_UPLOADER_EMAIL}",
                                            subject: "[${env.JOB_NAME}] OpenAPI specification has been updated and is up for review",
                                            body: "The OpenAPI spec documentation has been updated.<br><br>" +
                                                    "Please review the patchset and archived HTML output files (rest2html*.zip) linked here below:<br><br>" +
                                                    "&nbsp;&nbsp;Gerrit Patchset: ${env.GERRIT_CHANGE_URL}<br>" +
                                                    "&nbsp;&nbsp;HTML output files: ${env.BUILD_URL}artifact <br><br><br><br>" +
                                                    "<b>Note:</b> This mail was automatically sent as part of the following Jenkins job: ${env.BUILD_URL}",
                                            mimeType: 'text/html'
                                } catch(Exception e) {
                                    echo "Email notification was not sent."
                                    print e
                                }
                            }
                        }
                    },
                    "Generate Docs": {
                        sh "${bob} generate-docs"
                        archiveArtifacts "build/doc/**/*.*"
                        publishHTML (target: [
                            allowMissing: false,
                            alwaysLinkToLastBuild: false,
                            keepAll: true,
                            reportDir: 'build/doc',
                            reportFiles: 'CTA_api.html',
                            reportName: 'REST API Documentation'
                        ])
                    }
                )
            }
        }

        stage('Build') {
            when {
                expression { env.BUILD_ENABLED == "true" }
            }
            steps {
                withCredentials([usernamePassword(credentialsId: 'SELI_ARTIFACTORY', usernameVariable: 'SELI_ARTIFACTORY_REPO_USER', passwordVariable: 'SELI_ARTIFACTORY_REPO_PASS')]) {
                    sh "${bob} build"
                    ci_load_custom_stages ("stage-marker-build")
                }
            }
        }

        stage('Test') {
            when {
                expression { env.TEST_ENABLED == "true" }
            }
            steps {
                withCredentials([usernamePassword(credentialsId: 'SELI_ARTIFACTORY', usernameVariable: 'SELI_ARTIFACTORY_REPO_USER', passwordVariable: 'SELI_ARTIFACTORY_REPO_PASS')]){
                    sh "${bob} test"
                    ci_load_custom_stages ("stage-marker-test")
                }
            }
        }

        stage('SonarQube') {
            when {
                expression { env.SQ_ENABLED == "true" && env.SQ_LOCAL_ENABLED == "true"}
            }
            steps {
                withCredentials([usernamePassword(credentialsId: 'SELI_ARTIFACTORY', usernameVariable: 'SELI_ARTIFACTORY_REPO_USER', passwordVariable: 'SELI_ARTIFACTORY_REPO_PASS')]){
                    withSonarQubeEnv("${env.SQ_SERVER}") {
                        sh "${bob} sonar-enterprise-pcr"
                    }
                }
                timeout(time: 5, unit: 'MINUTES') {
                    waitUntil {
                        withSonarQubeEnv("${env.SQ_SERVER}") {
                            script {
                                return ci_pipeline_scripts.getQualityGate()
                            }
                        }
                    }
                }
            }
        }

        stage('Image') {
            when {
                expression { env.IMAGE_ENABLED == "true" }
            }
            steps {
                script {
                    ci_pipeline_scripts.retryMechanism("${bob} image",3)
                    ci_pipeline_scripts.retryMechanism("${bob} image-dr-check",3)
                    ci_load_custom_stages ("stage-marker-image")
                }
            }
            post {
                always {
                    archiveArtifacts allowEmptyArchive: true, artifacts: '**/image-design-rule-check-report*'
                }
            }
        }

        stage('Package') {
            when {
                expression { env.PACKAGE_ENABLED == "true" }
            }
            steps {
                script {
                    withCredentials([usernamePassword(credentialsId: 'SELI_ARTIFACTORY', usernameVariable: 'SELI_ARTIFACTORY_REPO_USER', passwordVariable: 'SELI_ARTIFACTORY_REPO_PASS'),
                                file(credentialsId: 'docker-config-json', variable: 'DOCKER_CONFIG_JSON')]) {
                        ci_pipeline_scripts.checkDockerConfig()
                        ci_pipeline_scripts.retryMechanism("${bob} package",3)
                        sh "${bob} package-jars"
                        sh "${bob} delete-images-from-agent:delete-internal-image"
                        ci_load_custom_stages ("stage-marker-package")
                    }
                }
            }
        }

        stage('K8S Resource Lock') {
            options {
                lock(label: LOCKABLE_RESOURCE_LABEL, variable: 'RESOURCE_NAME', quantity: 1)
            }
            environment {
                K8S_CLUSTER_ID = sh(script: "echo \${RESOURCE_NAME} | cut -d'_' -f1", returnStdout: true).trim()
                K8S_NAMESPACE = sh(script: "echo \${RESOURCE_NAME} | cut -d',' -f1 | cut -d'_' -f2", returnStdout: true).trim()
            }
            stages {
                stage('Helm Install') {
                    steps {
                        echo "Inject kubernetes config file (${env.K8S_CLUSTER_ID}) based on the Lockable Resource name: ${env.RESOURCE_NAME}"
                        configFileProvider([configFile(fileId: "${env.K8S_CLUSTER_ID}", targetLocation: "${env.KUBECONFIG}")]) {}
                        echo "The namespace (${env.K8S_NAMESPACE}) is reserved and locked based on the Lockable Resource name: ${env.RESOURCE_NAME}"

                        sh "${bob} expand-helm-template"
                        sh "${bob} create-namespace"
                        ci_load_custom_stages ("stage-marker-resource_lock") //for custom helm install / helm test

                        script {
                            if (env.HELM_INSTALL_ENABLED == "true") {
                                sh "${bob} helm-dry-run"
                                ci_pipeline_scripts.retryMechanism("${bob} helm-install",2)
                                sh "${bob} healthcheck"
                            }
                        }
                        ci_load_custom_stages ("stage-marker-helm") //for custom helm test or additional VA scans
                    }
                    post {
                        always {
                            sh "${bob} kaas-info || true"
                            archiveArtifacts allowEmptyArchive: true, artifacts: 'build/kaas-info.log'
                        }
                        unsuccessful {
                            withCredentials([usernamePassword(credentialsId: 'SERO_ARTIFACTORY', usernameVariable: 'SERO_ARTIFACTORY_REPO_USER', passwordVariable: 'SERO_ARTIFACTORY_REPO_PASS')]) {
                                sh "${bob} collect-k8s-logs || true"
                            }
                            archiveArtifacts allowEmptyArchive: true, artifacts: "k8s-logs/*"
                            sh "${bob} delete-namespace"
                        }
                    }
                }
                stage('Vulnerability Analysis') {
                    when {
                        expression { env.VA_ENABLED == "true" }
                    }
                    steps {
                        parallel(
                            "Hadolint": {
                                script {
                                    if (env.HADOLINT_ENABLED == "true") {
                                        sh "${bob} hadolint-scan"
                                        echo "Evaluating Hadolint Scan Resultcodes..."
                                        sh "${bob} evaluate-design-rule-check-resultcodes"
                                        archiveArtifacts "build/va-reports/hadolint-scan/**.*"
                                    }else{
                                        echo "stage Hadolint skipped"
                                    }
                                }
                            },
                            "Kubehunter": {
                                script {
                                    if (env.KUBEHUNTER_ENABLED == "true") {
                                        configFileProvider([configFile(fileId: "${K8S_CLUSTER_ID}", targetLocation: "${env.KUBECONFIG}")]) {}
                                        sh "${bob} kubehunter-scan"
                                        archiveArtifacts "build/va-reports/kubehunter-report/**/*"
                                    }else{
                                        echo "stage Kubehunter skipped"
                                    }
                                }
                            },
                            "Kubeaudit": {
                                script {
                                    if (env.KUBEAUDIT_ENABLED == "true") {
                                        sh "${bob} kube-audit"
                                        archiveArtifacts "build/va-reports/kube-audit-report/**/*"
                                    }else{
                                        echo "stage Kubeaudit skipped"
                                    }
                                }
                            },
                            "Kubesec": {
                                script {
                                    if (env.KUBESEC_ENABLED == "true") {
                                        sh "${bob} kubesec-scan"
                                        archiveArtifacts "build/va-reports/kubesec-reports/*"
                                    }else{
                                        echo "stage Kubsec skipped"
                                    }
                                }
                            },
                            "Trivy": {
                                script {
                                    if (env.TRIVY_ENABLED == "true") {
                                        sh "${bob} trivy-inline-scan"
                                        archiveArtifacts "build/va-reports/trivy-reports/**.*"
                                        archiveArtifacts "trivy_metadata.properties"
                                    }else{
                                        echo "stage Trivy skipped"
                                    }
                                }
                            },
                            "X-Ray": {
                                script {
                                    if (env.XRAY_ENABLED == "true") {
                                        sleep(60)
                                        withCredentials([usernamePassword(credentialsId: 'XRAY_SELI_ARTIFACTORY', usernameVariable: 'XRAY_USER', passwordVariable: 'XRAY_APIKEY')]) {
                                            ci_pipeline_scripts.retryMechanism("${bob} fetch-xray-report",3)
                                        }
                                        archiveArtifacts "build/va-reports/xray-reports/xray_report.json"
                                        archiveArtifacts "build/va-reports/xray-reports/raw_xray_report.json"
                                    }else{
                                        echo "stage X-Ray skipped"
                                    }
                                }
                            },
                            "Anchore-Grype": {
                                script {
                                    if (env.ANCHORE_ENABLED == "true") {
                                        sh "${bob} anchore-grype-scan"
                                        archiveArtifacts "build/va-reports/anchore-reports/**.*"
                                    }else{
                                        echo "stage Anchore-Grype skipped"
                                    }
                                }
                            }
                        )
                    }
                    post {
                        unsuccessful {
                            withCredentials([usernamePassword(credentialsId: 'SERO_ARTIFACTORY', usernameVariable: 'SERO_ARTIFACTORY_REPO_USER', passwordVariable: 'SERO_ARTIFACTORY_REPO_PASS')]) {
                                sh "${bob} collect-k8s-logs || true"
                            }
                            archiveArtifacts allowEmptyArchive: true, artifacts: 'k8s-logs/**/*.*'
                        }
                        cleanup {
                            sh "${bob} delete-namespace"
                            sh "${bob} delete-images-from-agent:cleanup-anchore-trivy-images"
                            sh "rm -f ${env.KUBECONFIG}"
                        }
                    }
                }
            }
        }

        stage('Generate Vulnerability report V2.0'){
            when {
                expression { env.VA_ENABLED == "true" }
            }
            steps {
                sh "${bob} generate-VA-report-V2:no-upload"
                archiveArtifacts allowEmptyArchive: true, artifacts: 'build/va-reports/Vulnerability_Report_2.0.md'
                ci_load_custom_stages ("stage-marker-va-report")
            }
        }

        stage('Maven Dependency Tree Check') {
            when {
                expression { env.FOSSA_ENABLED == "true" }
            }
            steps {
                script{
                    withCredentials([usernamePassword(credentialsId: 'SELI_ARTIFACTORY', usernameVariable: 'SELI_ARTIFACTORY_REPO_USER', passwordVariable: 'SELI_ARTIFACTORY_REPO_PASS')]) {
                        sh "${bob} generate-mvn-dep-tree"
                    }
                    if (ci_pipeline_scripts.compareDepTreeFiles("fossa/local_dep_tree.txt","build/dep_tree.txt")){
                        FOSS_CHANGED = false
                    }
                    echo "foss changed: $FOSS_CHANGED"
                }
                archiveArtifacts allowEmptyArchive: true, artifacts: 'build/dep_tree.txt'
            }
        }

        // skip when Foss not changed
        stage('FOSSA Analyze') {
            when {
                expression { env.FOSSA_ENABLED == "true" && FOSS_CHANGED }
            }
            steps {
                withCredentials([string(credentialsId: 'FOSSA_API_token', variable: 'FOSSA_API_KEY')]){
                    sh "${bob} fossa-analyze"
                }
            }
        }

        stage('FOSSA Fetch Report') {
            when {
                expression { env.FOSSA_ENABLED == "true" && FOSS_CHANGED }
            }
            steps {
                script{
                    withCredentials([string(credentialsId: 'FOSSA_API_token', variable: 'FOSSA_API_KEY')]){
                        ci_pipeline_scripts.retryMechanism("${bob} fossa-scan-status-check",2)
                        ci_pipeline_scripts.retryMechanism("${bob} fetch-fossa-report-attribution",2)
                        archiveArtifacts "*fossa-report.json"
                    }
                }
            }
        }

        stage('FOSSA Dependency Validate') {
            when {
                expression { env.FOSSA_ENABLED == "true" }
            }
            steps {
                withCredentials([string(credentialsId: 'FOSSA_API_token', variable: 'FOSSA_API_KEY')]){
                    sh "${bob} dependency-validate"
                }
                ci_load_custom_stages ("stage-marker-fossa")
            }
        }
    }
    post {
        success {
            script {
                ci_load_custom_stages ("stage-marker-post")
                sh "${bob} helm-chart-check-report-warnings"
                ci_pipeline_post.addHelmDRWarningIcon("pcr")
                ci_pipeline_post.modifyBuildDescription("pcr")
            }
        }
        failure {
            script{
                ci_pipeline_post.getFailedStage()
            }
        }
        always{
            sh "${bob} delete-images-from-agent"
            archiveArtifacts allowEmptyArchive: true, artifacts: "ci/*.Jenkinsfile, ci/common_ruleset2.0.yaml"
            archiveArtifacts allowEmptyArchive: true, artifacts: "ci/local_ruleset.yaml, ci/custom_stages.yaml, ci/local_pipeline_env.txt"
        }
    }
}
