@Library('pipeline-library') _

pipeline {
  agent { label 'docker' }
  stages {
    stage('Build') {
      steps {
        sh "docker build -t openstax/cnx-press:${GIT_COMMIT} ."
      }
    }
    stage('Publish Dev Container') {
      steps {
        // 'docker-registry' is defined in Jenkins under credentials
        withDockerRegistry([credentialsId: 'docker-registry', url: '']) {
          sh "docker push openstax/cnx-press:${GIT_COMMIT}"
        }
      }
    }
    stage('Deploy to the Staging stack') {
      when { branch 'master' }
      steps {
        // Requires DOCKER_HOST be set in the Jenkins Configuration.
        // Using the environment variable enables this file to be
        // endpoint agnostic.
        sh "docker -H ${CNX_STAGING_DOCKER_HOST} service update --label-add 'git.commit-hash=${GIT_COMMIT}' --image openstax/cnx-press:${GIT_COMMIT} staging_press"
      }
    }
    stage('Run Functional Tests'){
      when { branch 'master' }
      steps {
        runCnxFunctionalTests(testingDomain: "${env.CNX_STAGING_DOCKER_HOST}", area: "neb")
      }
    }
    stage('Publish Release') {
      when { buildingTag() }
      environment {
        release = getVersion()
      }
      steps {
        withDockerRegistry([credentialsId: 'docker-registry', url: '']) {
          sh "docker tag openstax/cnx-press:${GIT_COMMIT} openstax/cnx-press:${release}"
          sh "docker tag openstax/cnx-press:${GIT_COMMIT} openstax/cnx-press:latest"
          sh "docker push openstax/cnx-press:${release}"
          sh "docker push openstax/cnx-press:latest"
        }
      }
    }
  }
}
