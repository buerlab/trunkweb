/*global Yobockbone, Backbone, JST*/

Yobockbone.Views = Yobockbone.Views || {};

(function () {
    'use strict';
    
    Yobockbone.Views.Todos = Backbone.View.extend({

        template: JST['app/scripts/templates/todos.ejs'],

        tagName: 'div',

        id: '',
        el: $('#todo-app'),

        className: 'hello',

        events: {
             "click #submitBtn": "createTodo"
        },

        initialize: function () {
            this.listenTo(this.model, 'change', this.render);
            // this.listenTo(this.model, 'all', this.render);
            this.listenTo(this.model,"sync",this.render);
            this.model.fetch({
                success:function (a,b,c) {
                    // Note that we could also 'recycle' the same instance of EmployeeFullView
                    // instead of creating new instances
                    
                },
                error:function(data){
                    
                }
            });
            // this.render();
            console.log("initialize");
        },

        render: function () {
            console.log("render");
            this.$el.html(this.template(this.model.toJSON()));
            this.$("#todoContainer").empty();
            var that = this;
            $.each(this.model.models,function(k,v){
                var view = new Yobockbone.Views.Todo({model: v});
               that.$("#todoContainer").append(view.$el); 
            });                
        },

        createTodo: function(e) {
            var val = $("#new-todo").val();
            this.model.create({title: val,completed:true});
            $("#new-todo").val('');
            console.log("create");
        }

    });

})();
