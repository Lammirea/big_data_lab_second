pipeline {
    agent any

    environment {
        DOCKERHUB_CREDS = credentials('big_data_lab_second')
    }

    options {
        timestamps()
        skipDefaultCheckout(true)
    }

    stages {

        stage('Clone Repository') {
            steps {
                cleanWs()
                sh 'git clone -b develop https://github.com/Lammirea/big_data_lab_second.git'
            }
        }

        stage('Run Unit Tests') {
            steps {
                dir('big_data_lab_second') {
                    sh '''
                        # Проверяем доступные версии Python
                        which python || echo "python not found"
                        which python3 || echo "python3 not found"
                        
                        # Используем python вместо python3, если python3 недоступен
                        bash -c "
                            python -m venv venv &&
                            . venv/bin/activate &&
                            pip install -r requirements.txt &&
                            pytest src/unit_tests --cov=src
                        " || bash -c "
                            # Альтернативный вариант с системным Python
                            pip install -r requirements.txt &&
                            pytest src/unit_tests --cov=src
                        "
                    '''
                }
            }
        }

        stage('Login to DockerHub') {
            steps {
                sh 'docker login -u $DOCKERHUB_CREDS_USR -p $DOCKERHUB_CREDS_PSW'
            }
        }

        stage('Build Images and Run Containers') {
            steps {
                dir('big_data_lab_second') {
                    withCredentials([
                        string(credentialsId: 'redis-password', variable: 'REDIS_PASSWORD'),
                        string(credentialsId: 'redis-host', variable: 'REDIS_HOST'),
                        string(credentialsId: 'redis-port', variable: 'REDIS_PORT'),
                        string(credentialsId: 'redis-db', variable: 'REDIS_DB')
                    ]) {
                        sh '''
                            echo "REDIS_HOST=$REDIS_HOST" > .env
                            echo "REDIS_PORT=$REDIS_PORT" >> .env
                            echo "REDIS_PASSWORD=$REDIS_PASSWORD" >> .env
                            echo "REDIS_DB=$REDIS_DB" >> .env
                            docker-compose up -d --build
                        '''
                    }
                }
            }
        }
        
        stage('Check Container Logs') {
            steps {
                dir("big_data_lab_second") {
                    sh '''
                        container_id=$(docker ps -qf "name=web")
                        if [ -z "$container_id" ]; then
                            echo "No container running"
                            exit 1
                        fi
                        docker logs --tail 1000 "$container_id"
                    '''
                }
            }
        }

        stage('Push Docker Image to DockerHub') {
            steps {
                dir('big_data_lab_second') {
                    sh '''
                        image_id=$(docker images -q derelia/big_data_lab_second:latest)
                        if [ -z "$image_id" ]; then
                            echo "Error: Docker image not found. Build might have failed."
                            exit 1
                        fi
                        docker push derelia/big_data_lab_second:latest
                    '''
                }
            }
        }
    }

    post {
        always {
            sh '''
                docker stop web || true
                docker rm web || true
                docker stop redis || true
                docker rm redis || true
                docker rmi derelia/big_data_lab_second:latest || true
                docker rmi redis:latest || true
                docker logout || true
            '''
            cleanWs()
        }
    }
}