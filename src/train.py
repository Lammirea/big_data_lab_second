import configparser
import os
import pandas as pd
import pickle
from sklearn.metrics import accuracy_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.naive_bayes import GaussianNB

from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from imblearn.over_sampling import SMOTE

from preprocess import DataMaker
from logger import Logger
import sys

SHOW_LOG = True
IS_TEST_MODE = "pytest" in sys.modules or "unittest" in sys.modules

class MultiModel:
    def __init__(self):
        # Инициализация логгера и конфигурации
        logger = Logger(SHOW_LOG)
        self.config = configparser.ConfigParser()
        self.log = logger.get_logger(__name__)
        
        # Получаем директорию текущего файла
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Формируем путь на уровень выше (если config.ini в родительской папке)
        config_path = os.path.abspath(os.path.join(current_dir, "..", "config.ini"))
        
        print(f"Пытаемся загрузить конфиг из: {config_path}")
        
        if os.path.exists(config_path):
            self.config.read(config_path)
            self.log.info("Конфигурация успешно загружена")
        else:
            error_msg = f"Ошибка: файл {config_path} не найден"
            self.log.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        # Загрузка данных из файлов, указанных в config.ini
        #project_root = os.path.abspath(os.path.join(os.getcwd(), '..'))
        train_path = os.path.normpath(os.path.join(os.getcwd(), self.config["UTEST_DATA"]["train_file"]))
        test_path = os.path.normpath(os.path.join(os.getcwd(), self.config["DATA"]["test_file"]))
        train_df = pd.read_csv(train_path, encoding='latin1', low_memory=False)
        test_df = pd.read_csv(test_path, encoding='latin1', low_memory=False)
        
        # Предобработка данных
        data_preproc = DataMaker()
        self.X_train_raw, self.y_train = data_preproc.preprocess_data(train_df)
        self.X_test_raw, self.y_test = data_preproc.preprocess_data(test_df)
        self.feature_columns = list(self.X_train_raw.columns)
        
        # Создание pipeline для предобработки
        self.pipeline = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='mean')),
            ('scaler', StandardScaler())
        ])
        self.X_train_scaled = self.pipeline.fit_transform(self.X_train_raw)
        self.X_test_scaled = self.pipeline.transform(self.X_test_raw)
        
        
        # Балансировка классов с помощью SMOTE
        smote = SMOTE(random_state=42)
        self.X_train_smote, self.y_train_smote = smote.fit_resample(self.X_train_scaled, self.y_train)
        
        # Путь для сохранения моделей и предобработчика
        if not IS_TEST_MODE:
            self.project_path = os.path.join(os.getcwd(), "experiments")
            os.makedirs(self.project_path, exist_ok=True)
            self.preprocessor_path = os.path.join(self.project_path, "preprocessor.sav")
            try:
                with open(self.preprocessor_path, "wb") as f:
                    pickle.dump({'pipeline': self.pipeline, 'feature_columns': self.feature_columns}, f)
            except Exception as e:
                self.log.warning(f"Не удалось сохранить preprocessor: {e}")
        
        # Пути для сохранения моделей
        self.log_reg_path = os.path.join(self.project_path, "log_reg.sav")
        self.rand_forest_path = os.path.join(self.project_path, "rand_forest.sav")
        self.gnb_path = os.path.join(self.project_path, "gnb.sav")
        self.d_tree_path = os.path.join(self.project_path, "d_tree.sav")
        
        self.log.info("MultiModel is ready")

    def log_reg(self, predict=False):
        classifier = LogisticRegression()
        classifier.fit(self.X_train_smote, self.y_train_smote)
        if predict:
            y_pred = classifier.predict(self.X_test_scaled)
            print(accuracy_score(self.y_test, y_pred))
        params = {'path': self.log_reg_path}
        return self.save_model(classifier, self.log_reg_path, "LOG_REG", params)

    def rand_forest(self, use_config: bool, n_estimators=100, criterion="entropy", predict=False):
        if use_config:
            n_estimators = self.config.getint("RAND_FOREST", "n_estimators", fallback=n_estimators)
            criterion = self.config["RAND_FOREST"].get("criterion", criterion)
        classifier = RandomForestClassifier(n_estimators=n_estimators, criterion=criterion)
        classifier.fit(self.X_train_smote, self.y_train_smote)
        if predict:
            y_pred = classifier.predict(self.X_test_scaled)
            print(accuracy_score(self.y_test, y_pred))
        params = {'n_estimators': str(n_estimators), 'criterion': criterion, 'path': self.rand_forest_path}
        return self.save_model(classifier, self.rand_forest_path, "RAND_FOREST", params)

    def log_reg(self, use_config: bool, solver="lbfgs", max_iter=100, predict=False):
        if use_config:
            solver = self.config["LOG_REG"].get("solver", solver)
            max_iter = self.config.getint("LOG_REG", "max_iter", fallback=max_iter)
        classifier = LogisticRegression(solver=solver, max_iter=max_iter)
        classifier.fit(self.X_train_smote, self.y_train_smote)
        if predict:
            y_pred = classifier.predict(self.X_test_scaled)
            print(accuracy_score(self.y_test, y_pred))
        params = {'solver': solver, 'max_iter': str(max_iter), 'path': self.log_reg_path}
        return self.save_model(classifier, self.log_reg_path, "LOG_REG", params)


    def gnb(self, predict=False):
        classifier = GaussianNB()
        classifier.fit(self.X_train_smote, self.y_train_smote)
        if predict:
            y_pred = classifier.predict(self.X_test_scaled)
            print(accuracy_score(self.y_test, y_pred))
        params = {'path': self.gnb_path}
        return self.save_model(classifier, self.gnb_path, "GNB", params)

    def d_tree(self, use_config: bool, max_depth=10, min_samples_split=2, predict=False):
        if use_config:
            max_depth = self.config.getint("DECISION_TREE", "max_depth", fallback=max_depth)
            min_samples_split = self.config.getint("DECISION_TREE", "min_samples_split", fallback=min_samples_split)
        classifier = DecisionTreeClassifier(max_depth=max_depth, min_samples_split=min_samples_split)
        classifier.fit(self.X_train_smote, self.y_train_smote)
        if predict:
            y_pred = classifier.predict(self.X_test_scaled)
            print(accuracy_score(self.y_test, y_pred))
        params = {'max_depth': str(max_depth), 'min_samples_split': str(min_samples_split), 'path': self.d_tree_path}
        return self.save_model(classifier, self.d_tree_path, "DECISION_TREE", params)

    def save_model(self, classifier, path, section, params):
        # Сохранение модели и обновление конфигурации
        self.config[section] = params
        with open('config.ini', 'w') as configfile:
            self.config.write(configfile)
        with open(path, 'wb') as f:
            pickle.dump(classifier, f)
        self.log.info(f'{path} is saved')
        return os.path.isfile(path)
    
    def predict(self, model_name, test_type):
        """
        Выполняет предсказание для заданной модели и типа теста.
        """
        model_paths = {
            "log_reg": self.log_reg_path,
            "d_tree": self.d_tree_path,
            "gnb": self.gnb_path,
            "rand_forest": self.rand_forest_path
        }

        if model_name not in model_paths:
            raise ValueError(f"Unknown model: {model_name}")

        try:
            with open(model_paths[model_name], "rb") as f:
                model = pickle.load(f)
        except Exception as e:
            raise FileNotFoundError(f"Failed to load model {model_name}: {e}")

        if test_type == "smoke":
            score = model.score(self.X_test_scaled, self.y_test)
            return {"test_score": score}
        else:
            raise NotImplementedError(f"Test type '{test_type}' is not implemented in this method.")
        
if __name__ == "__main__":
    multi_model = MultiModel()
    # multi_model.d_tree(use_config=False, predict=True)
    # result = multi_model.predict("d_tree", "smoke")

    multi_model.log_reg(use_config=False, predict=True)
    #result = multi_model.predict("log_reg", "smoke")

    # multi_model.gnb(predict=True)
    # result = multi_model.predict("gnb", "smoke")

    # multi_model.rand_forest(use_config=False, predict=True)
    # result = multi_model.predict("rand_forest", "smoke")
    #print(result)