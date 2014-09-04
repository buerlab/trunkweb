$(function(){
    var groupStatArray=[];

    var bindEvent = function(){

        $(".groupStat-view-mode").click(function(){
            $(".groupStat-view-mode").removeClass("btn-primary");
            $(".groupStat-view-mode").addClass("btn-default");
            $(this).removeClass("btn-default");
            $(this).addClass("btn-primary");

            getGroupData();
        });

        $("#groupStat-date-confirm").click(function(){
            debugger;
            // getGroupDataTest2();
            getGroupData();
        });
    }
    var getDate = function(str){
            var b1 = str.split("-");
            return new Date(b1[0],(b1[1]-1),b1[2],0,0,0);
        }
 /******************
  * groupStat 数据总览  bengin
  *****************/   

    var getEditorParam = function(){
        var param = {};
        param.viewmode = $(".groupStat-view-mode.btn-primary").data("viewmode");


        if($("#groupStat-date-from").val().length>0){
            console.log(getDate($("#groupStat-date-from").val()));
            try{
                param.from = + getDate($("#groupStat-date-from").val());
            }catch(e){
                return null;
                showTips("起始时间格式不对");
            }
        }

        if($("#groupStat-date-to").val().length>0){
            try{
                param.to = + getDate($("#groupStat-date-to").val());
            }catch(e){
                return null;
                showTips("结束时间格式不对");
            }
        }

        if($("#groupStat-input-group").val().trim()==""){
            param.groupname = "all";
        }else{
            param.groupname = $("#groupStat-input-group").val().trim();
        }

        return param;
    }

    var renderEditor = function(array){
        $("#groupStatTable tbody").empty();
        debugger;
        $.each(array,function(k,v){
            // if(v.time != "summary"){
            var html = '<tr class="all-tr"><td>'+ v.time +'</td>'+ 
                      '<td>' + "汇总" + '</td>' + 
                      '<td>' + v.toAddMessageCount + '</td>' + 
                      '<td>' + v.toAddMessageIgnoreCount + '</td>' + 
                      '<td>' + v.toAddMessageDoneCount + '</td>' +
                      '<td>' + v.toAddMessageWaitCount + '</td></tr>' ;
            $("#groupStatTable tbody").append(html);
            $.each(v,function(k2,v2){
                if( typeof(v2) == "object"){
                    var html = '<tr><td>' +'</td>'+ 
                              '<td>' + k2 + '</td>' + 
                              '<td>' + v2.toAddMessageCount + '</td>' + 
                              '<td>' + v2.toAddMessageIgnoreCount + '</td>' + 
                              '<td>' + v2.toAddMessageDoneCount + '</td>' +
                              '<td>' + v2.toAddMessageWaitCount + '</td></tr>' ;
                    $("#groupStatTable tbody").append(html);
                }  
            });
                
            // }
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

        $.each(groupStatArray,function(k,v){
            if(v.time !="summary" || groupStatArray.length<=2){
                chartData.labels.push(v.time);
                chartData.datasets[0].data.push(v.toAddMessageCount);
                chartData.datasets[1].data.push(v.toAddMessageIgnoreCount);
                chartData.datasets[2].data.push(v.toAddMessageDoneCount);  
                // chartData.datasets[3].data.push(v.addedMessageCount);
            }
        });
        $("#groupStatCanvasCantainer").empty();
        $("#groupStatCanvasCantainer").append('<canvas id="groupStatCanvas"></canvas>');
        $("#groupStatCanvas").attr("height",400);
        $("#groupStatCanvas").attr("width",chartData.labels.length * 50 + 100);
        var ctx = $("#groupStatCanvas").get(0).getContext("2d");
        new Chart(ctx).Line(chartData,{
            multiTooltipTemplate:"<%=datasetLabel%>:<%= value %>"
        });

        
    }


    var getGroupData= function(){
        var url = "/stat/summary";
        
        var data = getEditorParam();

        var jqxhr = $.ajax({
            url: url,
            data: data,
            type: "GET",
            dataType: "json",
            success: function(data) {
                dataProtocolHandler(data,function(data){
                    groupStatArray = parseSummaryArray(data);
                    renderEditor(groupStatArray);
                    // showEditorChart(groupStatArray);
                });
            },

            error: function(data) {
                errLog && errLog("getGroupData() error");
            }
        });
    }




    // getGroupDataTest();
    getGroupData();
     /******************
      * summary 数据总览  end
      *****************/  

    bindEvent();
});
