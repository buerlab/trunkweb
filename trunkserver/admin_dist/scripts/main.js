function showTips(str){
    alert(str);
    console.log(str);
}

function errLog(str){
    debugger;
    console.log("ERROR:" +str);
    alert(str);
}

function dataProtocolHandler(data,successCallback,failCallback){
    if(data){
        if(data.code===0){
            if(successCallback && typeof successCallback == "function"){
                successCallback(data.data,data.datatype);
            }
        }else{
            if(failCallback && typeof failCallback == "function"){
                failCallback(data.code,data.msg,data.data,data.datatype);
            }else{
                showTips("data msg="+ data.msg+";data.code="+ data.code);
            }
           
        }
    }else{
        showTips("data is null");
    }
}

//header登录态展示处理
//依赖$.cookie

var G_data = G_data || {};
G_data.admin = G_data.admin || {};
if(localStorage){
	G_data.admin = JSON.parse(localStorage.getItem("admin"))|| {};
}



(loginHandler = function () {
	var $navLogin = $("#navLogin"),
		$navRegister = $("#navRegister"),
		$navNickname = $("#navNickname"),
		$navLogout = $("#navLogout"),
		$navVerifyIDNum = $("#navVerifyIDNum"),
		$navOperate = $(".navOperate"),
		$navVerifyDriverLicense = $("#navVerifyDriverLicense");

	if ($.cookie("mark") && $.cookie("username")){
		$navLogin.hide();
		$navRegister.hide();
		$navNickname.show();
		$navLogout.show();
		if(G_data.admin && G_data.admin.username){
			$navNickname.html(G_data.admin.username);
		}
		
	}else{
		$navLogin.show();
		$navRegister.show();
		$navNickname.hide();
		$navLogout.hide();
		$navOperate.hide();

		$navNickname.html("");
	}
	debugger;
	$.each(G_data.admin,function(k,v){
		if(k.indexOf("Permission")>=0){
			if(v){
				$("."+k).show();
			}else{
				$("."+k).hide();
			}
		}
	});

	$("#navNickname").click(function(){
		location.href = "me.html";
	});


	$navLogout.click(function(){
		var loginoutAjax = function(){
			var jqxhr = $.ajax({
				url: "/api/admin/logout",
				type: "POST",
				dataType: "json",
				success: function(data) {
					debugger;
					dataProtocolHandler(data,function(){
						location.href = location.href;
						G_data.admin= {};
						localStorage.setItem("admin","{}");
						
					});
					
				},
				error: function(data) {
					errLog && errLog("loginoutAjax");
				}
			});
		}
		loginoutAjax();
	});
})();



/*global Yobockbone, $*/

Backbone.sync = function(method, model, options) {
    var type = methodMap[method];

    // Default options, unless specified.
    _.defaults(options || (options = {}), {
      emulateHTTP: Backbone.emulateHTTP,
      emulateJSON: Backbone.emulateJSON
    });

    // Default JSON-request options.
    var params = {type: type, dataType: 'json'};

    // Ensure that we have a URL.
    if (!options.url) {
      params.url = _.result(model, 'url') || urlError();
    }

    // Ensure that we have the appropriate request data.
    if (options.data == null && model && (method === 'create' || method === 'update' || method === 'patch')) {
      // params.contentType = 'application/json';
      // params.data = JSON.stringify(options.attrs || model.toJSON(options));

      //由于tornado 不支持 application/json 的解析
      params.data = options.attrs || model.toJSON(options);
    }

    // For older servers, emulate JSON by encoding the request into an HTML-form.
    if (options.emulateJSON) {
      params.contentType = 'application/x-www-form-urlencoded';
      params.data = params.data ? {model: params.data} : {};
    }

    // For older servers, emulate HTTP by mimicking the HTTP method with `_method`
    // And an `X-HTTP-Method-Override` header.
    if (options.emulateHTTP && (type === 'PUT' || type === 'DELETE' || type === 'PATCH')) {
      params.type = 'POST';
      if (options.emulateJSON) params.data._method = type;
      var beforeSend = options.beforeSend;
      options.beforeSend = function(xhr) {
        xhr.setRequestHeader('X-HTTP-Method-Override', type);
        if (beforeSend) return beforeSend.apply(this, arguments);
      };
    }

    // Don't process data on a non-GET request.
    if (params.type !== 'GET' && !options.emulateJSON) {
      params.processData = false;
    }

    // If we're sending a `PATCH` request, and we're in an old Internet Explorer
    // that still has ActiveX enabled by default, override jQuery to use that
    // for XHR instead. Remove this line when jQuery supports `PATCH` on IE8.
    if (params.type === 'PATCH' && noXhrPatch) {
      params.xhr = function() {
        return new ActiveXObject("Microsoft.XMLHTTP");
      };
    }

    _.extend(params, options)
    var xhr = options.xhr =$.ajax({
            url: params.url,
            data: params.data,
            type: params.type,
            success:params.success,
            error: params.error,
            dataType: params.dataType
        });
    // Make the request, allowing the user to override any Ajax options.

    // var xhr = options.xhr = Backbone.ajax(_.extend(params, options));
    model.trigger('request', model, xhr, options);
    return xhr;
  };

  var noXhrPatch =
    typeof window !== 'undefined' && !!window.ActiveXObject &&
      !(window.XMLHttpRequest && (new XMLHttpRequest).dispatchEvent);

  // Map from CRUD to HTTP for our default `Backbone.sync` implementation.
  var methodMap = {
    'create': 'POST',
    'update': 'PUT',
    'patch':  'PATCH',
    'delete': 'DELETE',
    'read':   'GET'
  };

  // Set the default implementation of `Backbone.ajax` to proxy through to `$`.
  // Override this if you'd like to use a different library.
  Backbone.ajax = function() {
    console.log("arguments");
    console.log(arguments);
    return Backbone.$.ajax.apply(Backbone.$, arguments);
  };

window.Yobockbone = {
    Models: {},
    Collections: {},
    Views: {},
    Routers: {},
    init: function () {
        'use strict';
        console.log('Hello from Backbone!');
        var TodosCollection = new Yobockbone.Collections.Todos;
        var Todos = new Yobockbone.Views.Todos({model:TodosCollection});
    }
};

$(document).ready(function () {
    'use strict';
    Yobockbone.init();

    $('#datetimepicker').datepicker({
      format: "yyyy-mm-dd",
      language: "zh-CN",
      orientation: "top right",
      autoclose: true,
      startDate: '-0d',
      beforeShowDay: function (date) {
      }
    });
    $('select').selectpicker();
    
    $('input').iCheck({
    checkboxClass: 'icheckbox_square-blue',
    radioClass: 'iradio_square-blue',
    increaseArea: '20%' // optional
  });
  $(".main").css({
    "height": (document.documentElement.clientHeight-72)  + "px",
  });
});

this["JST"] = this["JST"] || {};

this["JST"]["app/scripts/templates/todo.ejs"] = function(obj) {
obj || (obj = {});
var __t, __p = '', __e = _.escape, __j = Array.prototype.join;
function print() { __p += __j.call(arguments, '') }
with (obj) {
__p += '<div class="view">\n  <input class="toggle" type="checkbox" ';
 if (completed) { ;
__p += 'checked';
 } ;
__p += '>\n  <label>' +
((__t = ( title )) == null ? '' : __t) +
'</label>\n  <a class="destroy">x</a>\n</div>\n<input class="edit" type="text" value="' +
((__t = ( title )) == null ? '' : __t) +
'">';

}
return __p
};

this["JST"]["app/scripts/templates/todos.ejs"] = function(obj) {
obj || (obj = {});
var __t, __p = '', __e = _.escape;
with (obj) {
__p += '<form class="input-append">\n    <input type="text" id="new-todo" placeholder="What do you need to do today?">\n    <input type="button" class="btn" id="submitBtn" value="Submit">\n</form>\n<ul id="todoContainer">\n    <!-- Where our To Do items will go -->\n</ul>\n';

}
return __p
};
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

/*global Yobockbone, Backbone*/

Yobockbone.Routers = Yobockbone.Routers || {};

(function () {
    'use strict';

    Yobockbone.Routers.Todo2 = Backbone.Router.extend({

    });

})();
