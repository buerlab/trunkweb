/*global Yobockbone, Backbone*/

Yobockbone.Collections = Yobockbone.Collections || {};

(function () {
    'use strict';

    Yobockbone.Collections.Todos = Backbone.Collection.extend({
    	// localStorage: new Backbone.LocalStorage('backbone-generator-todos'),
        model: Yobockbone.Models.Todo,
        url:"http://localhost:8888/api/todos",
        parse: function(response, options)  {
            if(response && response.code ===0){
                return response.data;
            }else{
                alert("error");
                return null;
            }
        },
    });

})();
	