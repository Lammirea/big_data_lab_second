pipeline {
    agent any

    environment {
        REDIS_HOST = 'redis'
        REDIS_PORT = '6379'
        REDIS_DB = '0'
        REDIS_PASSWORD = credentials('REDIS_PASSWORD')
        DOCKER_CREDS = credentials('big_data_lab_second')
    }

    options {
        timestamps()
        skipDefaultCheckout(true)
    }

    stages {
        stage('Setup Docker') {
            steps {
                script {
                    // Установка Docker на сервере, если его нет
                    sh '''
                    if ! [ -x "$(command -v docker)" ]; then
                      curl -fsSL https://get.docker.com -o get-docker.sh
                      sh get-docker.sh
                    fi
                    '''
                }
            }
        }

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

        stage('Diagnostics') {
            steps {
                script {
                    echo 'Проверка наличия Docker и переменных окружения...'
                    
                    // Проверим, установлен ли docker
                    sh 'which docker || echo "Docker не найден"'

                    // Проверим версию docker (если найден)
                    sh 'docker --version || echo "Невозможно получить версию Docker"'

                    // Проверим, подставилась ли переменная логина (не пароль!)
                    sh 'echo "DOCKER_CREDS_USR: $DOCKER_CREDS_USR"'
                }
            }
        }

        stage('Login') {
            steps {
                script {
                    withCredentials([usernamePassword(credentialsId: 'big_data_lab_second', usernameVariable: 'DOCKER_CREDS_USR', passwordVariable: 'DOCKER_CREDS_PSW')]) {
                try {
                    sh 'echo $DOCKER_CREDS_PSW | docker login -u $DOCKER_CREDS_USR --password-stdin'
                } catch (Exception e) {
                    echo "Ошибка при входе в DockerHub: ${e.getMessage()}"
                    currentBuild.result = 'FAILURE'
                    error("Не удалось войти в DockerHub")
                }
            }
        }
            }
        }

        stage('Create and run docker container') {
            steps {
                script {
                    try {
                        sh 'echo "REDIS_HOST=$REDIS_HOST  REDIS_PORT=$REDIS_PORT  REDIS_DB=$REDIS_DB"'
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

        stage('Wait for Redis') {
            steps {
                dir('big_data_lab_second') {
                    sh '''
                    svc=redis
                    cid=$(docker compose ps -q $svc)
                    [ -n "$cid" ] || { echo "Redis service not found"; exit 1; }
                    for i in {1..12}; do
                      res=$(docker exec "$cid" redis-cli -a "$REDIS_PASSWORD" ping || true)
                      if [ "$res" = "PONG" ]; then echo 'Redis ready'; exit 0; fi
                      sleep 5
                    done
                    echo 'Redis did not respond'; exit 1
                    '''
                }
            }
        }

        stage('Run Unit Tests') {
            steps {
                dir('big_data_lab_second') {
                    echo 'Запуск unit-тестов и сбор результатов в results.xml'
                    sh '''
                        containerId=$(docker compose ps -q app)
                        [ -n "$containerId" ] || { echo "App container is not running"; exit 1; }
                        docker exec "$containerId" \
                            pytest src/unit_tests \
                                   --maxfail=1 \
                                   --disable-warnings \
                                   -q \
                                   --junitxml=/tmp/results.xml
                        docker cp "$containerId":/tmp/results.xml "${WORKSPACE}/big_data_lab_second/results.xml"
                    '''
                }
            }
            post {
                always {
                    // Подхватим xml-отчет и дадим Jenkins показать фейлы
                    junit allowEmptyResults: false, testResults: 'big_data_lab_second/results.xml'
                }
            }

        stage('Checkout container logs') {
            steps {
                dir("big_data_lab_second") {
                    sh '''
                        # ask Compose for the running container ID of the "app" service
                        containerId=$(docker compose ps -q app)

                        # POSIX-compatible test
                        if [ -z "$containerId" ]; then
                        echo "No 'app' container running"
                        else
                        echo "Following logs for container $containerId"
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
                        sh 'docker push derelia/big_data_lab_second:latest'
                    } catch (Exception e) {
                        echo "Ошибка при публикации Docker-образа: ${e.getMessage()}"
                        currentBuild.result = 'FAILURE'
                        error("Не удалось опубликовать Docker-образ")
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