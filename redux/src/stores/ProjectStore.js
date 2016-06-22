var Reflux = require('Reflux');

var actions = Reflux.createActions(['createProject', 'deleteProject', 'updateProject', 'listProjects']);
var projectStore = Reflux.createStore({

    init: function() {
    },
    data: Immutable.Map({})
});

