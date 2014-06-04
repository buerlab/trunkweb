/*global Yobockbone, Backbone, JST*/

Yobockbone.Views = Yobockbone.Views || {};

(function () {
    'use strict';

    Yobockbone.Views.Todo = Backbone.View.extend({

        template: JST['app/scripts/templates/todo.ejs'],

        tagName: 'li',

        id: '',

        className: '',

        events: {
            "click .toggle"   : "toggleComplete",
            "click .destroy"  : "clear",
            "dblclick .view": "edit",
            "keypress .edit"  : "updateOnEnter",
        },

        initialize: function () {
            this.render();
            this.listenTo(this.model, 'change', this.render);
            this.listenTo(this.model, 'destroy',this.remove);
        },

        render: function () {
            this.$el.html(this.template(this.model.toJSON()));
            this.$el.toggleClass('done', this.model.get('completed'));
        },
        toggleComplete:function(){
            this.model.toggle();
        },
        edit: function() {
            debugger;
          this.$el.addClass("editing");
          this.$(".edit").focus();
        },
        clear:function(){
            debugger;
            this.model.destroy();
        },
            // If you hit `enter`, we're through editing the item.
        updateOnEnter: function(e) {
          if (e.keyCode == 13) this.close();
        },
    // Close the `"editing"` mode, saving changes to the todo.
        close: function() {
          var value = this.$(".edit").val();
          if (!value) {
            this.clear();
          } else {
            this.model.save({title: value});
            this.$el.removeClass("editing");
          }
        }

    });

})();
