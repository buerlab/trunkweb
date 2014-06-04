/*global Yobockbone, Backbone*/

Yobockbone.Models = Yobockbone.Models || {};

(function () {
    'use strict';

    Yobockbone.Models.Todo = Backbone.Model.extend({

        // url: "http://localhost:8888/api/todos",
        urlRoot:"http://localhost:8888/api/todos",
        initialize: function() {
        },

        validate: function(attrs, options) {
        },

        parse: function(response, options)  {
            if(response && response.code ===0){
                return response.data;
            }else{
                return response;
            }
        },

        defaults: {
            title: '',
            completed: false
        },
         // Toggle the `done` state of this todo item.
        toggle: function() {
          this.save({completed: !this.get("completed")});
        }
    });

})();
