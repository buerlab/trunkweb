$(function(){
    var summaryStatArray=[];

    var bindEvent = function(){
        $(".summaryStat-view-mode").click(function(){
            $(".summaryStat-view-mode").removeClass("btn-primary");
            $(".summaryStat-view-mode").addClass("btn-default");
            $(this).removeClass("btn-default");
            $(this).addClass("btn-primary");

            getSummaryData();
        });

        $("#summaryStat-date-confirm").click(function(){
            debugger;
            // getSummaryDataTest2();
            getSummaryData();
        });
    }
 /******************
  * summaryStat 数据总览  bengin
  *****************/   

    var getSummaryParam = function(){
        var param = {};
        param.viewmode = $(".summaryStat-view-mode.btn-primary").data("viewmode");


        if($("#summaryStat-date-from").val().length>0){
            console.log(getDate($("#summaryStat-date-from").val()));
            try{
                param.from = + getDate($("#summaryStat-date-from").val());
            }catch(e){
                return null;
                showTips("起始时间格式不对");
            }
        }

        if($("#summaryStat-date-to").val().length>0){
            try{
                param.to = + getDate($("#summaryStat-date-to").val());
            }catch(e){
                return null;
                showTips("结束时间格式不对");
            }
        }
        return param;
    }

    var renderSummary = function(array){
        $("#summaryStatTable tbody").empty();
        $.each(array,function(k,v){
            // if(v.time != "summary"){
                var html = '<tr><td>'+ v.time +'</td>'+ 
                          '<td>' + v.toAddMessageCount + '</td>' + 
                          '<td>' + v.toAddMessageIgnoreCount + '</td>' + 
                          '<td>' + v.toAddMessageDoneCount + '</td>' + 
                          '<td>' + v.toAddMessageWaitCount + '</td>' + 
                          '<td>' + v.addedMessageCount + '</td></tr>' ;
                $("#summaryStatTable tbody").append(html);
            // }
        });

    }

    var showSummaryChart = function(){
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

        $.each(summaryStatArray,function(k,v){
            if(v.time !="summary" || summaryStatArray.length<=2){
                chartData.labels.push(v.time);
                chartData.datasets[0].data.push(v.toAddMessageCount);
                chartData.datasets[1].data.push(v.toAddMessageIgnoreCount);
                chartData.datasets[2].data.push(v.toAddMessageDoneCount);  
                // chartData.datasets[3].data.push(v.addedMessageCount);
            }
        });
        $("#summaryStatCanvasCantainer").empty();
        $("#summaryStatCanvasCantainer").append('<canvas id="summaryStatCanvas"></canvas>');
        $("#summaryStatCanvas").attr("height",400);
        $("#summaryStatCanvas").attr("width",chartData.labels.length * 50 + 100);
        var ctx = $("#summaryStatCanvas").get(0).getContext("2d");
        new Chart(ctx).Line(chartData,{
            multiTooltipTemplate:"<%=datasetLabel%>:<%= value %>"
        });
    }

    var getSummaryData= function(){
        var url = "/stat/summary";
        
        var data = getSummaryParam();

        var jqxhr = $.ajax({
            url: url,
            data: data,
            type: "GET",
            dataType: "json",
            success: function(data) {
                dataProtocolHandler(data,function(data){
                    summaryStatArray = parseSummaryArray(data);
                    renderSummary(summaryStatArray);
                    showSummaryChart(summaryStatArray);
                });
            },

            error: function(data) {
                errLog && errLog("getSummaryData() error");
            }
        });
    }

    var getSummaryDataTest = function(){
        var data  = {
                    "t-2014-08-23":
                        {"toAddMessageWaitCount":132,
                        "toAddMessageDoneCount":3,
                        "toAddMessageIgnoreCount":40,
                        "toAddMessageCount":1429,
                        "addedMessageCount":37},
                        "t-2014-07-23":
                        {"toAddMessageWaitCount":132,
                        "toAddMessageDoneCount":3,
                        "toAddMessageIgnoreCount":40,
                        "toAddMessageCount":1429,
                        "addedMessageCount":37},
                        "t-2014-06-23":
                        {"toAddMessageWaitCount":132,
                        "toAddMessageDoneCount":3,
                        "toAddMessageIgnoreCount":40,
                        "toAddMessageCount":1429,
                        "addedMessageCount":37},
                        "t-2014-05-23":
                        {"toAddMessageWaitCount":132,
                        "toAddMessageDoneCount":3,
                        "toAddMessageIgnoreCount":40,
                        "toAddMessageCount":1429,
                        "addedMessageCount":37},
                        "t-2014-03-23":
                        {"toAddMessageWaitCount":132,
                        "toAddMessageDoneCount":3,
                        "toAddMessageIgnoreCount":40,
                        "toAddMessageCount":1429,
                        "addedMessageCount":37},
                        "t-2014-11-23":
                        {"toAddMessageWaitCount":132,
                        "toAddMessageDoneCount":3,
                        "toAddMessageIgnoreCount":40,
                        "toAddMessageCount":1429,
                        "addedMessageCount":37},
                        "t-2014-08-23":
                        {"toAddMessageWaitCount":132,
                        "toAddMessageDoneCount":3,
                        "toAddMessageIgnoreCount":40,
                        "toAddMessageCount":1429,
                        "addedMessageCount":37},
                        "t-2014-08-23":
                        {"toAddMessageWaitCount":132,
                        "toAddMessageDoneCount":3,
                        "toAddMessageIgnoreCount":40,
                        "toAddMessageCount":1429,
                        "addedMessageCount":37},
                        "t-2014-08-23":
                        {"toAddMessageWaitCount":132,
                        "toAddMessageDoneCount":3,
                        "toAddMessageIgnoreCount":40,
                        "toAddMessageCount":1429,
                        "addedMessageCount":37},
                        "t-2013-07-23":
                        {"toAddMessageWaitCount":132,
                        "toAddMessageDoneCount":3,
                        "toAddMessageIgnoreCount":40,
                        "toAddMessageCount":1429,
                        "addedMessageCount":37},
                        "t-2013-06-23":
                        {"toAddMessageWaitCount":132,
                        "toAddMessageDoneCount":3,
                        "toAddMessageIgnoreCount":40,
                        "toAddMessageCount":1429,
                        "addedMessageCount":37},
                        "t-2013-05-23":
                        {"toAddMessageWaitCount":132,
                        "toAddMessageDoneCount":3,
                        "toAddMessageIgnoreCount":40,
                        "toAddMessageCount":1429,
                        "addedMessageCount":37},
                        "t-2013-03-23":
                        {"toAddMessageWaitCount":132,
                        "toAddMessageDoneCount":3,
                        "toAddMessageIgnoreCount":40,
                        "toAddMessageCount":1429,
                        "addedMessageCount":37},
                        "t-2013-11-23":
                        {"toAddMessageWaitCount":132,
                        "toAddMessageDoneCount":3,
                        "toAddMessageIgnoreCount":40,
                        "toAddMessageCount":1429,
                        "addedMessageCount":37},
                        "t-2013-08-23":
                        {"toAddMessageWaitCount":132,
                        "toAddMessageDoneCount":3,
                        "toAddMessageIgnoreCount":40,
                        "toAddMessageCount":1429,
                        "addedMessageCount":37},
                        "t-2013-08-29":
                        {"toAddMessageWaitCount":132,
                        "toAddMessageDoneCount":3,
                        "toAddMessageIgnoreCount":40,
                        "toAddMessageCount":1429,
                        "addedMessageCount":37},
                    "t-2014-08-21":
                        {"toAddMessageWaitCount":35,
                        "toAddMessageDoneCount":1,
                        "toAddMessageIgnoreCount":4,
                        "toAddMessageCount":40,
                        "addedMessageCount":5},
                    "t-2014-08-22":
                        {"toAddMessageWaitCount":1373,
                        "toAddMessageDoneCount":16,
                        "toAddMessageIgnoreCount":40,
                        "toAddMessageCount":1429,
                        "addedMessageCount":37},
                    "summary":
                        {"toAddMessageWaitCount":1408,
                        "toAddMessageDoneCount":17,
                        "toAddMessageIgnoreCount":44,
                        "toAddMessageCount":1469,
                        "addedMessageCount":42}};
        summaryStatArray = parseSummaryArray(data);
        renderSummary(summaryStatArray);
        showSummaryChart(summaryStatArray);
    }

    var getSummaryDataTest2 = function(){
        var data  = {"t-2014-08-23":
                        {"toAddMessageWaitCount":132,
                        "toAddMessageDoneCount":3,
                        "toAddMessageIgnoreCount":40,
                        "toAddMessageCount":1429,
                        "addedMessageCount":37},
                    "summary":
                        {"toAddMessageWaitCount":1408,
                        "toAddMessageDoneCount":17,
                        "toAddMessageIgnoreCount":44,
                        "toAddMessageCount":1469,
                        "addedMessageCount":42}};
        summaryStatArray = parseSummaryArray(data);
        renderSummary(summaryStatArray);
        showSummaryChart(summaryStatArray);
    }


    
    
     /******************
      * summary 数据总览  end
      *****************/  

    bindEvent();
    $("#summaryStatMenu").click(function(){
        getSummaryData();
        debugger;
    });
    // getSummaryData();
    // getSummaryDataTest();
});
