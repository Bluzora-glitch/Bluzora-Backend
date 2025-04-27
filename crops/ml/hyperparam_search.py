# crops/ml/hyperparam_search.py

from sklearn.model_selection import GridSearchCV

def gridSearch(X_train, y_train, rf):
    param_grid = {
        'max_depth': [20, 30, 50, None],
        'max_features': ['auto', 'sqrt', None],
        'min_samples_leaf': [4, 6, 10],
        'min_samples_split': [4, 5, 6],
        'n_estimators': [200, 500, 1000]
    }
    grid_search = GridSearchCV(estimator=rf, param_grid=param_grid,
                               cv=3, n_jobs=-1, verbose=2)
    grid_search.fit(X_train, y_train)
    best_grid = grid_search.best_estimator_
    return best_grid
