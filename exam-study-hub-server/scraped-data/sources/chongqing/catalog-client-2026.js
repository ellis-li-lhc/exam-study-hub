$(function() {
	layui.use([ 'table', 'form' ], function() {
		var table = layui.table;
		var form = layui.form;
		$.ajax({
			type : "GET",
			async : false,
			url : "/info/getBkcc/all",
			success : function(result) {
				if (result.status == 200) {
					$("#ccselect").empty();
					$("#ccselect").append("<option  value =\"\">请选择层次</option>");
					$.each(result.data, function(index, pq) {
						$("#ccselect").append("<option  value =\"" + pq.code + "\">" + pq.name + "</option>");
					});
					form.render();
				}
			},
			error : function(result) {
				handleResult(result);
			}
		});
		$.ajax({
			type : "GET",
			async : false,
			url : "/info/getXxxs",
			success : function(result) {
				if (result.status == 200) {
					$("#xxxsselect").empty();
					$("#xxxsselect").append("<option  value =\"\">请选择学习形式</option>");
					$.each(result.data, function(index, pq) {
						$("#xxxsselect").append("<option  value =\"" + pq.code + "\">" + pq.name + "</option>");
					});
					form.render();
				}
			},
			error : function(result) {
				handleResult(result);
			}
		});
		form.on('select(ccselect)', function(data) {
			if (jQuery.isEmptyObject(data.value)) {
				$("#klselect").empty();
				$("#klselect").append("<option  value =\"\">请选择科类</option>");
				form.render();
			} else {
				$.ajax({
					type : "GET",
					async : false,
					url : "/info/getKl/" + data.value,
					success : function(result) {
						handleSUCCESSResult(result) ;
						if (result.status == 200) {
							$("#klselect").empty();
							$("#klselect").append("<option  value =\"\">请选择科类</option>");
							$.each(result.data, function(index, pq) {
								$("#klselect").append("<option  value =\"" + pq.code + "\">" + pq.name + "</option>");
							});
							form.render();
						}
					},
					error : function(result) {
						handleResult(result);
					}
				});
			}
		});

		buildTable();
	});
});

function buildTable() {
	layui.use('table', function() {
		var table = layui.table;
		var tableDate = [];

		var filterjson = {
			"yxdm" : null,
			"ccdm" : $("#ccselect").val(),
			"kldm" : $("#klselect").val(),
			"xxxsdm" : $("#xxxsselect").val(),
			"zymc" : $("#zymcinput").val(),
			"wyyzmc" :null
		};


		$.ajax({
			cache : false,
			type : 'POST',
			dataType : 'JSON',
			async : false,
			data:filterjson,
			url : '/info/getZsyxZylist?_=' + Math.random(),
			success : function(result) {
				handleSUCCESSResult(result) ;
				if (!jQuery.isEmptyObject(result) && 200 == result.status) {
					tableDate = result.data;
				}
			},
			error : function(result) {
				handleResult(result);
			}
		});

		//展示已知数据
		table.render({
			elem : '#zylist',
			cols : [ [ //标题栏
				{
					type : 'numbers',
					title : '序号'
				}
				, {
					field : 'yxdm',
					title : '学校代码',
					align : 'center',
					width : 90
				}
				, {
					field : 'yxmc',
					title : '学校名称',
					align : 'center',
					width : 150
				}
				, {
					field : 'zydm',
					title : '专业代码',
					align : 'center',
					width : 90
				}
				, {
					field : 'zymc',
					title : '专业名称',
					align : 'center',
					width : 200
				}
				, {
					field : 'klmc',
					title : '科类	',
					align : 'center',
					width : 150
				}
				, {
					field : 'ccmc',
					title : '层次',
					align : 'center',
					width : 90
				}
				, {
					field : 'xxxsmc',
					title : '学习形式',
					align : 'center',
					width : 90
				}
				, {
					field : 'wyyzmc',
					title : '外语语种',
					align : 'center',
					width : 90
				}
				, {
					field : 'xz',
					title : '学制',
					align : 'center',
					width : 90
				}
				, {
					field : 'zydz',
					title : '说明（招生性质、学校地址、收费标准）',
					align : 'center',
					width : 600
				}
			] ],
			data : tableDate, //,skin: 'line' //表格风格
			even : true,
			limit : 5000
		});
		setIframeHeight();
	})
	
}

$("#jcsearch").on("click", function () {
	 buildTable();
});

function GetQueryString(name) {
	var reg = new RegExp("(^|&)" + name + "=([^&]*)(&|$)");
	var r = window.location.search.substr(1).match(reg);
	if (r != null) return unescape(r[2]);
	return null;
}