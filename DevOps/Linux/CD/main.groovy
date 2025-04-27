pipeline {
    agent any

    environment {
        DOCKERHUB_CREDS = credentials('big_data_lab_two')
    }

    options {
        timestamps()
        skipDefaultCheckout(true)
    }

    stages {
        stage('Login') {
            steps {
                sh "docker login -u ${DOCKERHUB_CREDS_USR} -p ${DOCKERHUB_CREDS_PSW}"
            }
        }

        stage('Pull image') {
            steps {
                sh '''
                    docker pull derelia/big_data_lab_second:latest
                '''
            }
        }

        stage('Run containers with Docker Compose') {
            steps {
                script {
                    try {
                        sh 'cd big_data_lab_second && docker compose build'
                    } finally {
                        sh 'cd big_data_lab_second && docker compose up -d'
                    }
                }
            }
        }

        stage('Wait for Redis to be ready') {
            steps {
                script {
                    sh '''
                        containerId=$(docker ps -qf "name=^redis-1")
                        if [[ -z "$containerId" ]]; then
                            echo "Redis container not found"
                            exit 1
                        fi
                        until docker exec $containerId redis-cli ping; do
                            echo "Waiting for Redis..."
                            sleep 5
                        done
                        echo "Redis is ready"
                    '''
                }
            }
        }
    }

    post {
        always {
            sh 'docker compose down && docker logout'
            cleanWs()
        }
    }
}