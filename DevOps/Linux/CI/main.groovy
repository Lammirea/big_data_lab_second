pipeline {
    agent any

    environment {
        DOCKERHUB_CREDS = credentials('lab_big_data_two')
    }

    options {
        timestamps()
        skipDefaultCheckout(true)
    }

    stages {
        stage('Checkout repo dir') {
            steps {
                script {
                    try {
                        sh 'GIT_LFS_SKIP_SMUDGE=1 git clone -b develop https://github.com/Lammirea/big_data_lab_second.git'
                    } catch (Exception e) {
                        echo "Ошибка при клонировании репозитория: ${e.getMessage()}"
                        currentBuild.result = 'FAILURE'
                        error("Не удалось клонировать репозиторий")
                    }
                }
                sh 'cd big_data_lab_second && git lfs pull && ls -lash'
                sh 'whoami'
            }
        }

        stage('Login') {
            steps {
                script {
                    try {
                        sh "docker login -u ${DOCKERHUB_CREDS_USR} -p ${DOCKERHUB_CREDS_PSW}"
                    } catch (Exception e) {
                        echo "Ошибка при входе в DockerHub: ${e.getMessage()}"
                        currentBuild.result = 'FAILURE'
                        error("Не удалось войти в DockerHub")
                    }
                }
            }
        }

        stage('Create and run docker container') {
            steps {
                script {
                    try {
                        sh 'cd big_data_lab_second && docker compose build'
                    } catch (Exception e) {
                        echo "Ошибка при сборке Docker-контейнера: ${e.getMessage()}"
                        currentBuild.result = 'FAILURE'
                        error("Не удалось собрать Docker-контейнер")
                    }
                    try {
                        sh 'cd big_data_lab_second && docker compose up -d'
                    } catch (Exception e) {
                        echo "Ошибка при запуске Docker-контейнера: ${e.getMessage()}"
                        currentBuild.result = 'FAILURE'
                        error("Не удалось запустить Docker-контейнер")
                    }
                }
            }
        }

        stage('Wait for Redis to be ready') {
            steps {
                script {
                    try {
                        sh '''
                            cd big_data_lab_second
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
                    } catch (Exception e) {
                        echo "Ошибка при ожидании Redis: ${e.getMessage()}"
                        currentBuild.result = 'FAILURE'
                        error("Не удалось дождаться готовности Redis")
                    }
                }
            }
        }

        stage('Checkout container logs') {
            steps {
                dir("big_data_lab_second") {
                    sh '''
                        containerId=$(docker ps -qf "name=^app-1")
                        if [[ -z "$containerId" ]]; then
                            echo "No container running"
                        else
                            docker logs --tail 1000 -f "$containerId"
                        fi
                    '''
                }
            }
        }

        stage('Checkout coverage report') {
            steps {
                dir("big_data_lab_second") {
                    sh '''
                        docker compose logs -t --tail 10
                    '''
                }
            }
        }

        stage('Push') {
            steps {
                script {
                    try {
                        sh 'docker push derelia/big_data_second_lab:latest'
                    } catch (Exception e) {
                        echo "Ошибка при публикации Docker-образа: ${e.getMessage()}"
                        currentBuild.result = 'FAILURE'
                        error("Не удалось опубликовать Docker-образ")
                    }
                }
            }
        }

        stage('Run tests') {
            steps {
                script {
                    try {
                        sh 'cd big_data_lab_second && python -m unittest discover -s src/unit_tests'
                    } catch (Exception e) {
                        echo "Ошибка при запуске тестов: ${e.getMessage()}"
                        currentBuild.result = 'FAILURE'
                        error("Не удалось запустить тесты")
                    }
                }
            }
        }
    }

    post {
        always {
            script {
                try {
                    sh 'docker logout'
                } catch (Exception e) {
                    echo "Ошибка при выходе из DockerHub: ${e.getMessage()}"
                }
            }
            cleanWs()
        }
    }
}