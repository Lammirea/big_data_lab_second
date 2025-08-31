pipeline {
    agent any

    environment {
        // DockerHub credentials (username/password)
        DOCKERHUB_CREDS = credentials(params.get('dockerHubCredsId','big_data_lab_second'))

        // Repository settings
        REPO_URL = params.get('repoUrl','https://github.com/Lammirea/big_data_lab_second.git')
        BRANCH = params.get('branch','main')

        // Docker image that will be built/pushed
        DOCKER_IMAGE = params.get('dockerImage','Lammirea/big_data_lab_second:latest')

        // Defaults for Redis (can be overridden via Jenkins parameters or credentials)
        REDIS_HOST = params.get('redisHost','redis')
        REDIS_PORT = params.get('redisPort','6379')
        REDIS_DB   = params.get('redisDb','0')
    }

    options {
        timestamps()
        skipDefaultCheckout(true)
    }

    stages {
        stage('Clone Repository') {
            steps {
                cleanWs()
                sh "git clone -b ${BRANCH} ${REPO_URL}"
            }
        }

        stage('Run Unit Tests') {
            agent {
                docker {
                    image 'python:3.11-slim'
                    args '-u root:root --network host'
                    reuseNode true
                }
            }
            steps {
                dir('big_data_lab_second') {
                    sh '''
                        set -e
                        python -m venv venv
                        . venv/bin/activate
                        pip install -r requirements.txt
                        pytest src/unit_tests --cov=src
                    '''
                }
            }
        }

        stage('Login to DockerHub') {
            steps {
                sh 'docker login -u $DOCKERHUB_CREDS_USR -p $DOCKERHUB_CREDS_PSW'
            }
        }

        stage('Build Images and Run Containers (Redis)') {
            steps {
                dir('big_data_lab_second') {
                    // Inject Redis password from Jenkins credentials and build/run with docker-compose
                    withCredentials([string(credentialsId: params.get('redisPasswordCredId','redis-password'), variable: 'REDIS_PASSWORD')]) {
                        sh '''
                            set -e
                            cat > .env <<EOF
                            REDIS_HOST=${REDIS_HOST}
                            REDIS_PORT=${REDIS_PORT}
                            REDIS_PASSWORD=${REDIS_PASSWORD}
                            REDIS_DB=${REDIS_DB}
                            EOF

                            # Ensure docker-compose will use the .env we wrote
                            docker-compose up -d --build
                        '''
                }
            }
        }
    }

    stage('Check Container Logs') {
        steps {
            dir('big_data_lab_second') {
                sh '''
                    set -e
                    # try to find the web container by image first, fallback to service name
                    container_id=$(docker ps -qf "ancestor=${DOCKER_IMAGE}")
                    if [ -z "$container_id" ]; then
                            container_id=$(docker ps -qf "name=web")
                    fi
                    if [ -z "$container_id" ]; then
                        echo "No web container running"
                        docker ps -a
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
                    set -e
                    image_id=$(docker images -q ${DOCKER_IMAGE})
                    if [ -z "$image_id" ]; then
                        echo "Error: Docker image ${DOCKER_IMAGE} not found. Build might have failed."
                        docker images
                        exit 1
                    fi
                    docker push ${DOCKER_IMAGE}
                '''
                }
            }
        }
    }

    post {
        always {
            sh '''
                set +e
                # Stop and remove containers created by docker-compose
                (cd big_data_lab_second && docker-compose down -v) || true

                # Remove image we built/pulled
                docker rmi ${DOCKER_IMAGE} || true

                # Logout from DockerHub
                docker logout || true
            '''
            cleanWs()
        }
    }
}
