pipeline {
  agent {
    dockerfile true
  }
  libraries {
    lib('fxtest@1.10')
  }
  triggers {
    cron('H * * * * ')
  }
  options {
    timeout(time: 1, unit: 'HOURS')
  }
  stages {
    stage('Generate Report') {
      steps {
        sh 'python generate.py -o index.html'
      }
      post {
        always {
          archiveArtifacts 'index.html, generate.log'
          publishHTML(target: [
            allowMissing: false,
            alwaysLinkToLastBuild: true,
            keepAll: true,
            reportDir: '',
            reportFiles: "index.html",
            reportName: 'HTML Report'])
          step([$class: 'S3BucketPublisher',
            consoleLogLevel: 'INFO',
            dontWaitForConcurrentBuildCompletion: false,
            entries: [[
              bucket: 'net-mozaws-stage-fx-test-report',
              excludedFile: '',
              flatten: true,
              gzipFiles: true,
              keepForever: false,
              managedArtifacts: false,
              noUploadOnFailure: false,
              selectedRegion: 'us-east-1',
              showDirectlyInBrowser: false,
              sourceFile: 'index.html, overview.png',
              storageClass: 'STANDARD',
              uploadFromSlave: false,
              useServerSideEncryption: false]],
            pluginFailureResultConstraint: 'SUCCESS',
            profileName: 'fx-test-jenkins-s3-publisher'])
        }
        changed {
          ircNotification()
        }
        failure {
          emailext(
            attachLog: true,
            attachmentsPattern: 'index.html, generate.log',
            body: '$BUILD_URL',
            replyTo: '$DEFAULT_REPLYTO',
            subject: '$DEFAULT_SUBJECT',
            to: '$DEFAULT_RECIPIENTS')
        }
      }
    }
  }
}
