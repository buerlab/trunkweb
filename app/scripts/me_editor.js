$(function(){
    var editorStatArray=[];

    if(G_data && G_data.admin && G_data.admin.username){
        $("#editorStat-input-editor").val(G_data.admin.username);
    }
    var bindEvent = function(){

        $(".editorStat-view-mode").click(function(){
            $(".editorStat-view-mode").removeClass("btn-primary");
            $(".editorStat-view-mode").addClass("btn-default");
            $(this).removeClass("btn-default");
            $(this).addClass("btn-primary");

            getEditorData();
        });

        $("#editorStat-date-confirm").click(function(){
            debugger;
            // getEditorDataTest2();
            getEditorData();
        });
    }
    var getDate = function(str){
            var b1 = str.split("-");
            return new Date(b1[0],(b1[1]-1),b1[2]);
        }
 /******************
  * editorStat 数据总览  bengin
  *****************/   

    var getEditorParam = function(){
        var param = {};
        param.viewmode = $(".editorStat-view-mode.btn-primary").data("viewmode");


        if($("#editorStat-date-from").val().length>0){
            console.log(getDate($("#editorStat-date-from").val()));
            try{
                param.from = + getDate($("#editorStat-date-from").val());
            }catch(e){
                return null;
                showTips("起始时间格式不对");
            }
        }

        if($("#editorStat-date-to").val().length>0){
            try{
                param.to = + getDate($("#editorStat-date-to").val());
            }catch(e){
                return null;
                showTips("结束时间格式不对");
            }
        }

        if($("#editorStat-input-editor").val().trim()==""){
            param.editor = "all";
        }else{
            param.editor = $("#editorStat-input-editor").val().trim();
        }

        return param;
    }

    var renderEditor = function(array){
        $("#editorStatTable tbody").empty();
        debugger;
        $.each(array,function(k,v){
            // if(v.time != "summary"){
            var html = '<tr class="all-tr"><td>'+ v.time +'</td>'+ 
                      '<td>' + "汇总" + '</td>' + 
                      '<td>' + v.toAddMessageIgnoreCount + '</td>' + 
                      '<td>' + v.toAddMessageDoneCount + '</td>' +
                      '<td>' + v.confirmingMessageCount + '</td>' +
                      '<td>' + v.refuseMessageCount + '</td>' +
                      '<td>' + v.giveupMessageCount + '</td>' +
                      '<td>' + v.confirmedMessageCount + '</td></tr>' ;
                      
            $("#editorStatTable tbody").append(html);
            $.each(v,function(k2,v2){
                if( typeof(v2) == "object"){
                    var html = '<tr><td>' +'</td>'+ 
                              '<td>---' + k2 + '</td>' + 
                              '<td>' + v2.toAddMessageIgnoreCount + '</td>' + 
                              '<td>' + v2.toAddMessageDoneCount + '</td>' +
                              '<td>' + v2.confirmingMessageCount + '</td>' +
                              '<td>' + v2.refuseMessageCount + '</td>' +
                              '<td>' + v2.giveupMessageCount + '</td>' +
                              '<td>' + v2.confirmedMessageCount + '</td></tr>' ;
                    $("#editorStatTable tbody").append(html);
                }  
            });
                
            // }
            // "confirmingMessageCount":0,
            // "refuseMessageCount":0,
            // "confirmedMessageCount":0
        });

    }

    var showEditorChart = function(){
        var chartData = {};
        chartData.labels = [];
        chartData.datasets = [
            {
                fillColor : "rgba(220,220,220,0.5)",
                strokeColor : "rgba(220,220,220,1)",
                pointColor : "rgba(220,220,220,1)",
                pointStrokeColor : "#fff",
                data : [],
                label: "抓取数量",
                name: "toAddMessageCount"
            },
            {
                fillColor : "rgba(255,0,0,0.5)",
                strokeColor : "rgba(255,0,0,1)",
                pointColor : "rgba(255,0,0,1)",
                pointStrokeColor : "#fff",
                data : [],
                label: "忽略数量",
                name:"toAddMessageIgnoreCount"
            },
            {
                fillColor : "rgba(151,187,205,0.5)",
                strokeColor : "rgba(151,187,205,1)",
                pointColor : "rgba(151,187,205,1)",
                pointStrokeColor : "#fff",
                data : [],
                label:"完成数量",
                name:"toAddMessageDoneCount"
            }
            // },
            // {
            //     fillColor : "rgba(0,255,0,0.5)",
            //     strokeColor : "rgba(0,255,0,1)",
            //     pointColor : "rgba(0,255,0,1)",
            //     pointStrokeColor : "#fff",
            //     data : [],
            //     label: "addedMessageCount"
            // }
        ];

        $.each(editorStatArray,function(k,v){
            if(v.time !="summary" || editorStatArray.length<=2){
                chartData.labels.push(v.time);
                chartData.datasets[0].data.push(v.toAddMessageCount);
                chartData.datasets[1].data.push(v.toAddMessageIgnoreCount);
                chartData.datasets[2].data.push(v.toAddMessageDoneCount);  
                // chartData.datasets[3].data.push(v.addedMessageCount);
            }
        });
        $("#editorStatCanvasCantainer").empty();
        $("#editorStatCanvasCantainer").append('<canvas id="editorStatCanvas"></canvas>');
        $("#editorStatCanvas").attr("height",400);
        $("#editorStatCanvas").attr("width",chartData.labels.length * 50 + 100);
        var ctx = $("#editorStatCanvas").get(0).getContext("2d");
        new Chart(ctx).Line(chartData,{
            multiTooltipTemplate:"<%=datasetLabel%>:<%= value %>"
        });

        
    }


    var parseEditorArray = function(data){
        var summaryArray =  [];
        $.each(data,function(k,v){
            var a = v;
            a.time = k.replace("t-","");
            summaryArray.push(a);
        });

        summaryArray.sort(function(a,b){

            if(a.time == "summary"){
                return -1;
            }

            if(b.time == "summary"){
                return 1;
            }
            if(+getDate(a.time) > +getDate(b.time)){
                return 1;
            }else if(+getDate(a.time) == +getDate(b.time)){
                return 0;
            }else{
                return -1;
            }
        });
        return summaryArray;
    }

    var getEditorData= function(){
        var url = "http://localhost:9289/stat/workload";
        
        var data = getEditorParam();

        var jqxhr = $.ajax({
            url: url,
            data: data,
            type: "GET",
            dataType: "json",
            success: function(data) {
                dataProtocolHandler(data,function(data){
                    editorStatArray = parseEditorArray(data);
                    renderEditor(editorStatArray);
                    // showEditorChart(editorStatArray);
                });
            },

            error: function(data) {
                errLog && errLog("getEditorData() error");
            }
        });
    }




    // getEditorDataTest();
    getEditorData();
     /******************
      * summary 数据总览  end
      *****************/  

    bindEvent();
});
